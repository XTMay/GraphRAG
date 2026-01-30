"""
LangGraph Workflow Definition
=============================

Defines the complete agent workflow as a state graph.

Teaching Points:
- LangGraph workflows are directed graphs
- Nodes are processing steps
- Edges define control flow
- Conditional edges enable branching
"""

from langgraph.graph import StateGraph, END, START

from src.agent.state import AgentState, create_initial_state, state_summary
from src.agent.nodes import (
    parse_intent,
    retrieve_context,
    check_sufficiency,
    generate_plan,
    validate_plan,
    generate_response,
    ask_clarification,
    handle_error,
    increment_counter,
    route_after_check,
    route_after_validation,
)


def create_workflow() -> StateGraph:
    """
    Create the Smart Home Agent workflow graph.

    Workflow Structure:
    ```
    START
      │
      ▼
    parse_intent
      │
      ▼
    retrieve_context
      │
      ▼
    check_sufficiency ──────┐
      │                     │
      │ (sufficient)        │ (needs clarification)
      ▼                     ▼
    generate_plan      ask_clarification
      │                     │
      ▼                     ▼
    validate_plan          END
      │
      ├── (valid) ──────────┐
      │                     │
      │ (invalid, retry)    │
      ▼                     │
    generate_plan           │
      │                     │
      ▼                     ▼
    validate_plan     generate_response
      │                     │
      ▼                     ▼
    generate_response      END
      │
      ▼
     END
    ```

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph with our state type
    workflow = StateGraph(AgentState)

    # =========================================
    # ADD NODES
    # =========================================

    # Stage 1: Intent Parsing
    workflow.add_node("parse_intent", parse_intent)

    # Stage 2: Context Retrieval
    workflow.add_node("retrieve_context", retrieve_context)

    # Stage 3: Sufficiency Check
    workflow.add_node("check_sufficiency", check_sufficiency)

    # Stage 4a: Clarification (if needed)
    workflow.add_node("ask_clarification", ask_clarification)

    # Stage 4b: Plan Generation
    workflow.add_node("generate_plan", generate_plan)

    # Stage 5: Validation
    workflow.add_node("validate_plan", validate_plan)

    # Stage 6: Response Generation
    workflow.add_node("generate_response", generate_response)

    # Utility: Counter increment
    workflow.add_node("increment_counter", increment_counter)

    # =========================================
    # ADD EDGES (Control Flow)
    # =========================================

    # Start -> Parse Intent
    workflow.add_edge(START, "parse_intent")

    # Parse Intent -> Retrieve Context
    workflow.add_edge("parse_intent", "retrieve_context")

    # Retrieve Context -> Check Sufficiency
    workflow.add_edge("retrieve_context", "check_sufficiency")

    # Check Sufficiency -> Conditional Branch
    workflow.add_conditional_edges(
        "check_sufficiency",
        route_after_check,
        {
            "ask_clarification": "ask_clarification",
            "generate_plan": "generate_plan",
        }
    )

    # Ask Clarification -> END
    workflow.add_edge("ask_clarification", END)

    # Generate Plan -> Increment Counter -> Validate Plan
    workflow.add_edge("generate_plan", "increment_counter")
    workflow.add_edge("increment_counter", "validate_plan")

    # Validate Plan -> Conditional Branch
    workflow.add_conditional_edges(
        "validate_plan",
        route_after_validation,
        {
            "generate_response": "generate_response",
            "regenerate_plan": "generate_plan",  # Loop back
        }
    )

    # Generate Response -> END
    workflow.add_edge("generate_response", END)

    return workflow


def compile_workflow():
    """
    Create and compile the workflow for execution.

    Returns:
        Compiled workflow (runnable)
    """
    workflow = create_workflow()
    return workflow.compile()


# Create a singleton compiled workflow
_compiled_workflow = None


def get_workflow():
    """Get the compiled workflow (singleton)."""
    global _compiled_workflow
    if _compiled_workflow is None:
        _compiled_workflow = compile_workflow()
    return _compiled_workflow


# =========================================
# AGENT INTERFACE
# =========================================

class SmartHomeAgent:
    """
    High-level interface for the Smart Home Agent.

    Usage:
        agent = SmartHomeAgent()
        response = agent.run("Make the living room cozy for movie night")
        print(response)

    Teaching Point:
        This class wraps the LangGraph workflow and provides
        a simple interface for the user.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the agent.

        Args:
            debug: If True, print state at each step
        """
        self.workflow = get_workflow()
        self.debug = debug

    def run(self, user_input: str) -> str:
        """
        Process a user request and return a response.

        Args:
            user_input: Natural language request

        Returns:
            Agent's response string
        """
        # Create initial state
        initial_state = create_initial_state(user_input)

        # Run the workflow
        if self.debug:
            print("\n" + "=" * 60)
            print("STARTING AGENT WORKFLOW")
            print("=" * 60)
            print(f"Input: {user_input}")

        final_state = self.workflow.invoke(initial_state)

        if self.debug:
            print("\n" + state_summary(final_state))

        # Return the final response
        return final_state.get("final_response", "I couldn't process your request.")

    def run_with_trace(self, user_input: str) -> tuple[str, list[str]]:
        """
        Run and return both response and reasoning trace.

        Args:
            user_input: Natural language request

        Returns:
            Tuple of (response, reasoning_trace)
        """
        initial_state = create_initial_state(user_input)
        final_state = self.workflow.invoke(initial_state)

        response = final_state.get("final_response", "I couldn't process your request.")
        trace = final_state.get("reasoning_trace", [])

        return response, trace

    def run_streaming(self, user_input: str):
        """
        Run with streaming to see each step.

        Args:
            user_input: Natural language request

        Yields:
            State updates at each step
        """
        initial_state = create_initial_state(user_input)

        for event in self.workflow.stream(initial_state):
            yield event

    def get_full_state(self, user_input: str) -> AgentState:
        """
        Run and return the full final state.

        Useful for debugging and teaching.

        Args:
            user_input: Natural language request

        Returns:
            Complete AgentState after processing
        """
        initial_state = create_initial_state(user_input)
        return self.workflow.invoke(initial_state)


# =========================================
# VISUALIZATION
# =========================================

def visualize_workflow():
    """
    Generate a visual representation of the workflow.

    Returns:
        Mermaid diagram string
    """
    mermaid = """
```mermaid
graph TD
    START([Start]) --> parse[Parse Intent]
    parse --> retrieve[Retrieve Context]
    retrieve --> check{Check Sufficiency}

    check -->|Needs Clarification| ask[Ask Clarification]
    check -->|Sufficient| plan[Generate Plan]

    ask --> END1([End])

    plan --> counter[Increment Counter]
    counter --> validate{Validate Plan}

    validate -->|Valid| response[Generate Response]
    validate -->|Invalid & Retry| plan

    response --> END2([End])

    style START fill:#90EE90
    style END1 fill:#FFB6C1
    style END2 fill:#FFB6C1
    style check fill:#FFE4B5
    style validate fill:#FFE4B5
```
"""
    return mermaid


# =========================================
# TESTING
# =========================================

if __name__ == "__main__":
    print("Testing Smart Home Agent Workflow")
    print("=" * 60)

    # Print workflow structure
    print("\nWorkflow Visualization:")
    print(visualize_workflow())

    # Test with mock data (no API calls)
    print("\nTesting workflow structure...")

    try:
        workflow = create_workflow()
        compiled = workflow.compile()
        print("✓ Workflow compiled successfully!")

        # Get the graph structure
        print(f"✓ Nodes: {list(compiled.get_graph().nodes.keys())}")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test full run (requires API keys)
    print("\n" + "-" * 60)
    print("Testing full agent run...")
    print("(Requires OPENAI_API_KEY and Neo4j connection)")
    print("-" * 60)

    try:
        agent = SmartHomeAgent(debug=True)
        response = agent.run("Turn on the living room lights")
        print(f"\nFinal Response: {response}")
    except Exception as e:
        print(f"\nSkipped full test: {e}")
        print("Set OPENAI_API_KEY and start Neo4j to run full tests.")
