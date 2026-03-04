"""
ReAct-Style Tool-Calling Agent
===============================

An agent that uses LLM Function Calling to dynamically select tools.

Teaching Points:
- Tool Calling (Function Calling): LLM decides WHICH tool to call and with WHAT parameters
- ReAct Pattern: Reason → Act → Observe → Repeat
- Comparison with explicit workflow:
    - Explicit (SmartHomeAgent): deterministic graph, predictable, easier to debug
    - Tool-calling (ToolCallingAgent): flexible, can handle unexpected queries, harder to debug
- ToolNode from LangGraph handles tool execution automatically
"""

import json
from typing import Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict, Annotated

from src.llm import get_llm
from src.agent.tools import get_all_tools
from src.agent.memory import ConversationMemory, get_memory


# =========================================
# STATE DEFINITION
# =========================================

class ToolAgentState(TypedDict):
    """
    State for the tool-calling agent.

    Teaching Point:
        Unlike SmartHomeAgent's AgentState (many fields for each stage),
        ToolAgentState is simple: just a list of messages.
        The LLM itself decides the flow by choosing tools.
    """
    messages: Annotated[list, add_messages]


# =========================================
# SYSTEM PROMPT
# =========================================

TOOL_AGENT_SYSTEM_PROMPT = """你是一个智能家居助手，可以帮助用户控制家中的设备。

## 你的能力
1. 查询房间中的设备和能力
2. 查询设备的详细信息
3. 搜索预设场景
4. 执行设备控制命令（模拟）

## 工作流程
1. 理解用户需求
2. 使用工具查询相关信息
3. 根据查询结果制定方案
4. 执行设备命令
5. 向用户报告结果

## 注意事项
- 只控制已确认存在的设备
- 只使用设备实际拥有的能力
- 如果信息不足，先查询再行动
- 用自然、友好的语言回复用户
- 如果用户的请求模糊，先查询可用设备再决定"""


# =========================================
# WORKFLOW BUILDER
# =========================================

def create_tool_agent():
    """
    Create a ReAct tool-calling agent using LangGraph.

    Architecture:
    ```
    START → agent_node ←→ tool_node → END
                 ↑              |
                 └──────────────┘
         (loop until LLM stops calling tools)
    ```

    Teaching Point:
        The key difference from SmartHomeAgent is that the LLM
        decides the flow. It can call tools 0, 1, or many times
        before generating a final response.
    """
    tools = get_all_tools()
    llm = get_llm(temperature=0.0)

    # Bind tools to the LLM (enables Function Calling)
    llm_with_tools = llm.bind_tools(tools)

    # Agent node: call the LLM
    def agent_node(state: ToolAgentState) -> dict:
        """
        Call the LLM with the current messages.
        The LLM may respond with text or tool calls.
        """
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Routing: check if the LLM wants to call a tool
    def should_continue(state: ToolAgentState) -> str:
        """
        Route based on whether the last message has tool calls.

        Teaching Point:
            When the LLM uses Function Calling, its response
            contains tool_calls instead of text content.
        """
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # Build the graph
    workflow = StateGraph(ToolAgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# =========================================
# HIGH-LEVEL INTERFACE
# =========================================

class ToolCallingAgent:
    """
    High-level interface for the tool-calling agent.

    Provides the same interface as SmartHomeAgent for easy comparison.

    Usage:
        agent = ToolCallingAgent()
        response = agent.run("打开客厅的灯")
        print(response)

    Teaching Point:
        Having the same interface allows direct comparison:
        - SmartHomeAgent: explicit workflow, predictable
        - ToolCallingAgent: LLM-driven, flexible
    """

    def __init__(self, memory: Optional[ConversationMemory] = None):
        """
        Args:
            memory: Optional conversation memory for multi-turn support.
                    If None, creates a new memory instance.
        """
        self.workflow = create_tool_agent()
        self.memory = memory or get_memory()

    def run(self, user_input: str, session_id: Optional[str] = None) -> str:
        """
        Process a user request and return a response.

        Args:
            user_input: Natural language request
            session_id: Optional session ID for conversation memory
        """
        messages = self._build_messages(user_input, session_id)
        result = self.workflow.invoke({"messages": messages})

        # Extract the final response
        response = result["messages"][-1].content

        # Save to memory if session is provided
        if session_id:
            self.memory.add_message(session_id, "user", user_input)
            self.memory.add_message(session_id, "assistant", response)

        return response

    def run_with_trace(self, user_input: str, session_id: Optional[str] = None) -> tuple[str, list[str]]:
        """
        Run and return both response and reasoning trace.

        The trace includes all tool calls and their results.
        """
        messages = self._build_messages(user_input, session_id)
        result = self.workflow.invoke({"messages": messages})

        # Extract trace from messages
        trace = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace.append(f"Tool Call: {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})")
            elif hasattr(msg, "name") and msg.name:
                # Tool result message
                trace.append(f"Tool Result ({msg.name}): {msg.content[:200]}")

        response = result["messages"][-1].content

        if session_id:
            self.memory.add_message(session_id, "user", user_input)
            self.memory.add_message(session_id, "assistant", response)

        return response, trace

    def run_streaming(self, user_input: str, session_id: Optional[str] = None):
        """
        Run with streaming to see each step.

        Yields state updates at each step.
        """
        messages = self._build_messages(user_input, session_id)

        for event in self.workflow.stream({"messages": messages}):
            yield event

    def _build_messages(self, user_input: str, session_id: Optional[str] = None) -> list:
        """Build the message list with system prompt and optional history."""
        messages = [SystemMessage(content=TOOL_AGENT_SYSTEM_PROMPT)]

        # Add conversation history if session exists
        if session_id:
            history = self.memory.get_history(session_id)
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=user_input))
        return messages


if __name__ == "__main__":
    print("Testing Tool-Calling Agent")
    print("=" * 60)

    try:
        agent = ToolCallingAgent()
        print("\n--- Test 1: Simple query ---")
        response, trace = agent.run_with_trace("客厅有什么设备？")
        print(f"Response: {response}")
        print(f"Trace: {trace}")

        print("\n--- Test 2: Action request ---")
        response, trace = agent.run_with_trace("打开客厅的灯")
        print(f"Response: {response}")
        print(f"Trace: {trace}")

    except Exception as e:
        print(f"\nSkipped test: {e}")
        print("Set LLM_PROVIDER and start Neo4j to run full tests.")
