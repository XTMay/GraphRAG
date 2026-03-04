"""
LangGraph Node Functions
========================

Each function is a "node" in the agent workflow graph.
Nodes read from state, perform operations, and return state updates.

Teaching Points:
- Nodes are pure functions: (State) -> StateUpdate
- Each node has a single responsibility
- Nodes can call LLMs, tools, or do logic
"""

import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import get_llm

from src.agent.state import AgentState
from src.agent.prompts import (
    INTENT_PARSER_PROMPT,
    ACTION_PLAN_PROMPT,
    CLARIFICATION_PROMPT,
    VALIDATION_PROMPT,
    RESPONSE_PROMPT,
)
from src.utils.output_parser import (
    SmartHomeOutputParser,
    extract_json,
)
from src.graph.retriever import SmartHomeRetriever


# Global retriever instance (initialized lazily)
_retriever = None


def get_retriever() -> SmartHomeRetriever:
    """Get or create retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = SmartHomeRetriever()
    return _retriever


# =========================================
# NODE: Parse Intent
# =========================================

def parse_intent(state: AgentState) -> dict:
    """
    Parse user input to extract structured intent.

    Input State:
        - user_input: Raw user request

    Output State:
        - parsed_intent: Structured intent dict
        - reasoning_trace: Updated with parsing step

    Teaching Point:
        This node transforms unstructured text into
        structured data that downstream nodes can use.
    """
    user_input = state["user_input"]

    # Call LLM to parse intent
    llm = get_llm()
    prompt = INTENT_PARSER_PROMPT.format_messages(user_input=user_input)
    response = llm.invoke(prompt)

    # Parse the response
    try:
        parsed = extract_json(response.content)
    except ValueError:
        # Fallback: create minimal intent
        parsed = {
            "goal": user_input,
            "rooms": [],
            "actions": [],
            "mood": None,
            "scene_hint": None,
            "constraints": []
        }

    return {
        "parsed_intent": parsed,
        "reasoning_trace": [f"Parsed intent: goal='{parsed.get('goal')}', rooms={parsed.get('rooms')}"]
    }


# =========================================
# NODE: Retrieve Context
# =========================================

def retrieve_context(state: AgentState) -> dict:
    """
    Retrieve relevant context from the knowledge graph.

    Input State:
        - parsed_intent: Structured intent

    Output State:
        - retrieved_context: Formatted context string
        - retrieval_metadata: Info about what was retrieved
        - reasoning_trace: Updated

    Teaching Point:
        This is the GraphRAG step! We use the parsed intent
        to decide what to retrieve from the graph.
    """
    intent = state.get("parsed_intent", {})
    retriever = get_retriever()

    context_parts = []
    metadata = {"strategies_used": [], "total_devices": 0}

    # Strategy 1: Room-based retrieval
    rooms = intent.get("rooms") or []
    if rooms:
        for room in rooms:
            result = retriever.get_room_context(room)
            context_parts.append(result.formatted_context)
            metadata["strategies_used"].append("room_context")
            metadata["total_devices"] += result.metadata.get("device_count", 0)

    # Strategy 2: Scene-based retrieval
    scene_hint = intent.get("scene_hint")
    if scene_hint:
        result = retriever.get_scene_context(scene_hint)
        if result.metadata.get("scenes_found", 0) > 0:
            context_parts.append(result.formatted_context)
            metadata["strategies_used"].append("scene_lookup")

    # Strategy 3: Capability-based retrieval (for action words)
    actions = intent.get("actions") or []
    capability_map = {
        "dim": "dim",
        "brighten": "dim",
        "light": "power",
        "music": "play_music",
        "play": "play_music",
        "temperature": "temperature",
        "warm": "color",
        "cool": "color",
    }

    capabilities_to_find = []
    for action in actions:
        for keyword, cap in capability_map.items():
            if keyword in action.lower():
                capabilities_to_find.append(cap)

    if capabilities_to_find and not rooms:
        # Only do capability search if no rooms specified
        result = retriever.get_devices_by_capability(list(set(capabilities_to_find)))
        context_parts.append(result.formatted_context)
        metadata["strategies_used"].append("capability_search")

    # Strategy 4: Keyword search (fallback if nothing found)
    if not context_parts:
        # Extract keywords from goal
        goal = intent.get("goal", "")
        keywords = [w for w in goal.split() if len(w) > 3][:5]
        if keywords:
            result = retriever.search_by_keywords(keywords)
            context_parts.append(result.formatted_context)
            metadata["strategies_used"].append("keyword_search")

    # Combine all context
    combined_context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."

    return {
        "retrieved_context": combined_context,
        "retrieval_metadata": metadata,
        "reasoning_trace": [f"Retrieved context using strategies: {metadata['strategies_used']}"]
    }


# =========================================
# NODE: Check Sufficiency
# =========================================

def check_sufficiency(state: AgentState) -> dict:
    """
    Check if we have enough context to proceed.

    Input State:
        - retrieved_context
        - retrieval_metadata

    Output State:
        - needs_clarification: bool
        - clarification_question: str (if needed)

    Teaching Point:
        This is a decision node that determines the control flow.
        It's simple logic, not an LLM call.
    """
    context = state.get("retrieved_context", "")
    metadata = state.get("retrieval_metadata", {})
    intent = state.get("parsed_intent", {})

    # Check if we found any devices
    if "No relevant context found" in context or "No matching" in context:
        # Need clarification
        question = "I couldn't find devices matching your request. Could you specify which room?"
        return {
            "needs_clarification": True,
            "clarification_question": question,
            "reasoning_trace": ["Insufficient context - asking for clarification"]
        }

    # Check if room was too vague
    rooms = intent.get("rooms") or []
    if not rooms and "devices" not in context.lower():
        question = "Which room would you like me to adjust? (e.g., living room, bedroom)"
        return {
            "needs_clarification": True,
            "clarification_question": question,
            "reasoning_trace": ["No room specified - asking for clarification"]
        }

    # Sufficient context
    return {
        "needs_clarification": False,
        "reasoning_trace": ["Context is sufficient to generate plan"]
    }


# =========================================
# NODE: Generate Plan
# =========================================

def generate_plan(state: AgentState) -> dict:
    """
    Generate action plan using LLM.

    Input State:
        - parsed_intent
        - retrieved_context

    Output State:
        - action_plan: Dict with reasoning and actions

    Teaching Point:
        This is where the LLM does the heavy lifting -
        reasoning about how to achieve the goal given
        the available devices and capabilities.
    """
    intent = state.get("parsed_intent", {})
    context = state.get("retrieved_context", "")

    # Format intent for prompt
    intent_str = json.dumps(intent, indent=2)

    # Call LLM
    llm = get_llm()
    prompt = ACTION_PLAN_PROMPT.format_messages(
        parsed_intent=intent_str,
        retrieved_context=context
    )
    response = llm.invoke(prompt)

    # Parse response
    try:
        plan = extract_json(response.content)
    except ValueError:
        plan = {
            "reasoning": "Could not generate a valid plan",
            "actions": []
        }

    return {
        "action_plan": plan,
        "reasoning_trace": [f"Generated plan with {len(plan.get('actions', []))} actions"]
    }


# =========================================
# NODE: Validate Plan
# =========================================

def validate_plan(state: AgentState) -> dict:
    """
    Validate the generated action plan.

    Input State:
        - action_plan
        - retrieved_context

    Output State:
        - validation_result: Dict with is_valid, issues, suggestions

    Teaching Point:
        Validation ensures the plan is executable.
        This could be rule-based or LLM-based.
        We use simple rule-based validation here.
    """
    plan = state.get("action_plan", {})
    context = state.get("retrieved_context", "")

    issues = []
    suggestions = []
    actions = plan.get("actions", [])

    # Check if we have any actions
    if not actions:
        issues.append("No actions in the plan")

    # Validate each action
    for action in actions:
        device_name = action.get("device_name", "")
        capability = action.get("capability", "")

        # Check device exists in context
        if device_name.lower() not in context.lower():
            issues.append(f"Device '{device_name}' not found in available devices")

        # Check capability mentioned
        if capability and capability.lower() not in context.lower():
            issues.append(f"Capability '{capability}' may not be available")

        # Check value is present
        if action.get("value") is None:
            suggestions.append(f"Action for {device_name} is missing a value")

    is_valid = len(issues) == 0

    return {
        "validation_result": {
            "is_valid": is_valid,
            "issues": issues,
            "suggestions": suggestions
        },
        "reasoning_trace": [f"Validation: {'passed' if is_valid else 'failed with ' + str(len(issues)) + ' issues'}"]
    }


# =========================================
# NODE: Generate Response
# =========================================

def generate_response(state: AgentState) -> dict:
    """
    Generate user-facing response.

    Input State:
        - user_input
        - action_plan

    Output State:
        - final_response: Friendly response text

    Teaching Point:
        The final response should be natural and informative,
        not just a JSON dump of the plan.
    """
    user_input = state.get("user_input", "")
    plan = state.get("action_plan", {})

    # Format plan for prompt
    plan_str = json.dumps(plan, indent=2)

    # Call LLM
    llm = get_llm(temperature=0.7)  # Slightly more creative for response
    prompt = RESPONSE_PROMPT.format_messages(
        user_input=user_input,
        action_plan=plan_str
    )
    response = llm.invoke(prompt)

    return {
        "final_response": response.content,
        "reasoning_trace": ["Generated user response"]
    }


# =========================================
# NODE: Handle Error
# =========================================

def handle_error(state: AgentState) -> dict:
    """
    Handle errors gracefully.

    Input State:
        - error

    Output State:
        - final_response: Error message for user
    """
    error = state.get("error", "An unknown error occurred")

    return {
        "final_response": f"I'm sorry, I encountered an issue: {error}. Please try rephrasing your request.",
        "reasoning_trace": [f"Error handled: {error}"]
    }


# =========================================
# NODE: Increment Counter
# =========================================

def increment_counter(state: AgentState) -> dict:
    """
    Increment iteration counter to prevent infinite loops.
    """
    current = state.get("iteration_count", 0)
    return {"iteration_count": current + 1}


# =========================================
# ROUTING FUNCTIONS
# =========================================

def route_after_check(state: AgentState) -> Literal["ask_clarification", "generate_plan"]:
    """
    Route based on whether clarification is needed.

    Teaching Point:
        This is a conditional edge in LangGraph.
        It returns the name of the next node.
    """
    if state.get("needs_clarification", False):
        return "ask_clarification"
    return "generate_plan"


def route_after_validation(state: AgentState) -> Literal["generate_response", "regenerate_plan"]:
    """
    Route based on validation result.
    """
    validation = state.get("validation_result", {})

    if validation.get("is_valid", False):
        return "generate_response"

    # Check iteration count to prevent infinite loops
    if state.get("iteration_count", 0) >= 2:
        return "generate_response"  # Give up and respond anyway

    return "regenerate_plan"


# =========================================
# NODE: Ask Clarification (Terminal for now)
# =========================================

def ask_clarification(state: AgentState) -> dict:
    """
    Prepare clarification question as final response.

    In a real system, this would pause and wait for user input.
    For this demo, we just return the question.
    """
    question = state.get("clarification_question", "Could you please provide more details?")

    return {
        "final_response": question,
        "reasoning_trace": ["Asking user for clarification"]
    }


if __name__ == "__main__":
    # Test individual nodes
    print("Testing Agent Nodes")
    print("=" * 50)

    # Create test state
    from src.agent.state import create_initial_state

    state = create_initial_state("Make the living room cozy for movie night")

    # Test parse_intent (requires OpenAI key)
    print("\n1. Testing parse_intent node...")
    try:
        result = parse_intent(state)
        print(f"   Parsed: {result['parsed_intent']}")
        state.update(result)
    except Exception as e:
        print(f"   Skipped (needs OpenAI key): {e}")
        # Use mock data
        state["parsed_intent"] = {
            "goal": "create cozy movie atmosphere",
            "rooms": ["living room"],
            "mood": "cozy",
            "scene_hint": "movie night"
        }

    # Test retrieve_context (requires Neo4j)
    print("\n2. Testing retrieve_context node...")
    try:
        result = retrieve_context(state)
        print(f"   Context length: {len(result['retrieved_context'])} chars")
        print(f"   Strategies: {result['retrieval_metadata']['strategies_used']}")
        state.update(result)
    except Exception as e:
        print(f"   Skipped (needs Neo4j): {e}")

    print("\n✓ Node tests complete!")
