"""
Agent State Definition
======================

Defines the state that flows through the LangGraph workflow.

Teaching Points:
- State is a typed dictionary passed between nodes
- Each node reads and updates specific state fields
- TypedDict provides type hints for better tooling
"""

from typing import Any, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from src.utils.output_parser import ParsedIntent, ActionPlan, ValidationResult


def replace_value(current: Any, new: Any) -> Any:
    """Reducer that replaces the current value with new value."""
    return new


def append_to_list(current: list, new: Any) -> list:
    """Reducer that appends to a list."""
    if current is None:
        current = []
    if isinstance(new, list):
        return current + new
    return current + [new]


class AgentState(TypedDict, total=False):
    """
    State object that flows through the LangGraph workflow.

    Teaching Point:
        This state is like a "context object" that accumulates
        information as the agent processes a request. Each node
        reads what it needs and writes what it produces.

    Fields:
        user_input: Original user request
        parsed_intent: Extracted intent from user input
        retrieved_context: Context from GraphRAG retrieval
        reasoning_trace: List of reasoning steps (for debugging)
        action_plan: Generated device commands
        validation_result: Result of plan validation
        final_response: User-facing response
        needs_clarification: Whether to ask user for more info
        clarification_question: Question to ask user
        error: Error message if something went wrong
        iteration_count: Track iterations to prevent infinite loops
    """

    # Input
    user_input: str

    # Intent Parsing Stage
    parsed_intent: Annotated[Optional[dict], replace_value]

    # Retrieval Stage
    retrieved_context: Annotated[Optional[str], replace_value]
    retrieval_metadata: Annotated[Optional[dict], replace_value]

    # Reasoning Stage
    reasoning_trace: Annotated[list[str], append_to_list]

    # Planning Stage
    action_plan: Annotated[Optional[dict], replace_value]

    # Validation Stage
    validation_result: Annotated[Optional[dict], replace_value]

    # Output Stage
    final_response: Annotated[Optional[str], replace_value]

    # Control Flow
    needs_clarification: Annotated[bool, replace_value]
    clarification_question: Annotated[Optional[str], replace_value]
    error: Annotated[Optional[str], replace_value]
    iteration_count: Annotated[int, replace_value]


def create_initial_state(user_input: str) -> AgentState:
    """
    Create initial state for a new request.

    Args:
        user_input: The user's natural language request

    Returns:
        Initialized AgentState
    """
    return AgentState(
        user_input=user_input,
        parsed_intent=None,
        retrieved_context=None,
        retrieval_metadata=None,
        reasoning_trace=[],
        action_plan=None,
        validation_result=None,
        final_response=None,
        needs_clarification=False,
        clarification_question=None,
        error=None,
        iteration_count=0,
    )


def state_summary(state: AgentState) -> str:
    """
    Generate a human-readable summary of current state.
    Useful for debugging and teaching.

    Args:
        state: Current agent state

    Returns:
        Formatted string summary
    """
    lines = ["=" * 50, "AGENT STATE SUMMARY", "=" * 50]

    # User Input
    lines.append(f"\n📝 User Input: {state.get('user_input', 'N/A')}")

    # Parsed Intent
    intent = state.get('parsed_intent')
    if intent:
        lines.append(f"\n🎯 Parsed Intent:")
        lines.append(f"   Goal: {intent.get('goal', 'N/A')}")
        lines.append(f"   Rooms: {intent.get('rooms', [])}")
        lines.append(f"   Mood: {intent.get('mood', 'N/A')}")

    # Retrieved Context
    context = state.get('retrieved_context')
    if context:
        lines.append(f"\n📚 Retrieved Context: {len(context)} characters")

    # Action Plan
    plan = state.get('action_plan')
    if plan:
        actions = plan.get('actions', [])
        lines.append(f"\n📋 Action Plan: {len(actions)} actions")
        for action in actions[:3]:  # Show first 3
            lines.append(f"   - {action.get('device_name')}: {action.get('capability')}")
        if len(actions) > 3:
            lines.append(f"   ... and {len(actions) - 3} more")

    # Validation
    validation = state.get('validation_result')
    if validation:
        status = "✅ Valid" if validation.get('is_valid') else "❌ Invalid"
        lines.append(f"\n✔️  Validation: {status}")

    # Control Flow Status
    lines.append(f"\n🔄 Iteration: {state.get('iteration_count', 0)}")
    if state.get('needs_clarification'):
        lines.append(f"❓ Needs Clarification: {state.get('clarification_question')}")
    if state.get('error'):
        lines.append(f"⚠️  Error: {state.get('error')}")

    # Final Response
    response = state.get('final_response')
    if response:
        lines.append(f"\n💬 Final Response: {response[:100]}...")

    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


# Type alias for cleaner code
State = AgentState


if __name__ == "__main__":
    # Demo state creation and summary
    state = create_initial_state("Make the living room cozy for movie night")

    # Simulate some updates
    state['parsed_intent'] = {
        'goal': 'create cozy movie atmosphere',
        'rooms': ['living room'],
        'mood': 'cozy',
        'scene_hint': 'movie night'
    }

    state['action_plan'] = {
        'reasoning': 'Dimming lights for movie atmosphere',
        'actions': [
            {'device_name': 'Ceiling Light', 'capability': 'dim', 'value': 20},
            {'device_name': 'Smart TV', 'capability': 'power', 'value': 'on'}
        ]
    }

    state['iteration_count'] = 1

    print(state_summary(state))
