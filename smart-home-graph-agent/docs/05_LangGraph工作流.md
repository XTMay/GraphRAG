# 第五章：LangGraph工作流

## 📖 本章目标

1. 理解状态机与工作流的概念
2. 掌握LangGraph的核心API
3. 学会设计节点与边
4. 完成动手实验：构建完整Agent

---

## 5.1 状态机与工作流

### 什么是状态机？

```
┌─────────────────────────────────────────────────────────────────┐
│                    有限状态机 (FSM) 概念                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  有限状态机是一个数学模型，由以下组成:                           │
│                                                                 │
│  • 状态集合 (States): 系统可能处于的状态                        │
│  • 初始状态 (Initial State): 起始状态                           │
│  • 转换函数 (Transitions): 状态之间如何转换                     │
│  • 终止状态 (Final States): 结束状态                            │
│                                                                 │
│  示例: 自动售货机                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │     ┌─────────┐   投币   ┌─────────┐   选择   ┌────────┐│   │
│  │     │  空闲   │─────────→│ 已投币  │────────→│ 出货中 ││   │
│  │     └─────────┘          └─────────┘         └────────┘│   │
│  │          │                    │                    │     │   │
│  │          │                    │ 退币               │     │   │
│  │          │                    ▼                    │     │   │
│  │          │              ┌─────────┐               │     │   │
│  │          └──────────────│  退币   │←──────────────┘     │   │
│  │                         └─────────┘                      │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agent为什么需要状态机？

```
┌─────────────────────────────────────────────────────────────────┐
│                  Agent状态机的优势                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ 没有状态机的Agent (简单循环)                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  while True:                                             │   │
│  │      response = llm(user_input)                          │   │
│  │      if "done" in response:                              │   │
│  │          break                                           │   │
│  │      # 如何处理错误？如何回退？如何调试？                 │   │
│  │                                                          │   │
│  │  问题:                                                   │   │
│  │  • 难以追踪执行状态                                      │   │
│  │  • 难以处理复杂的控制流                                  │   │
│  │  • 难以调试和测试                                        │   │
│  │  • 无法可视化                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ✅ 使用状态机的Agent (LangGraph)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  • 明确的状态定义                                        │   │
│  │  • 显式的转换条件                                        │   │
│  │  • 可追踪的执行路径                                      │   │
│  │  • 可测试的独立节点                                      │   │
│  │  • 可视化的工作流                                        │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.2 LangGraph核心概念

### 三大核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph 核心概念                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1️⃣ State (状态)                                         │   │
│  │                                                          │   │
│  │  状态是一个TypedDict，包含工作流中所有需要的数据          │   │
│  │                                                          │   │
│  │  class AgentState(TypedDict):                            │   │
│  │      user_input: str          # 用户输入                 │   │
│  │      parsed_intent: dict      # 解析后的意图             │   │
│  │      context: str             # 检索的上下文             │   │
│  │      action_plan: dict        # 操作计划                 │   │
│  │      response: str            # 最终响应                 │   │
│  │                                                          │   │
│  │  状态在节点之间流动，每个节点可以读取和更新状态           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2️⃣ Node (节点)                                          │   │
│  │                                                          │   │
│  │  节点是执行特定任务的函数                                 │   │
│  │                                                          │   │
│  │  def parse_intent(state: AgentState) -> dict:            │   │
│  │      # 读取输入                                          │   │
│  │      user_input = state["user_input"]                    │   │
│  │                                                          │   │
│  │      # 执行任务 (调用LLM)                                │   │
│  │      intent = llm.parse(user_input)                      │   │
│  │                                                          │   │
│  │      # 返回状态更新                                      │   │
│  │      return {"parsed_intent": intent}                    │   │
│  │                                                          │   │
│  │  节点的输入是当前状态，输出是状态更新（字典）             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  3️⃣ Edge (边)                                            │   │
│  │                                                          │   │
│  │  边定义节点之间的转换关系                                 │   │
│  │                                                          │   │
│  │  普通边: A → B (总是执行)                                 │   │
│  │  graph.add_edge("parse_intent", "retrieve_context")      │   │
│  │                                                          │   │
│  │  条件边: A → B or C (根据条件选择)                        │   │
│  │  graph.add_conditional_edges(                            │   │
│  │      "check_sufficiency",                                │   │
│  │      route_function,           # 返回下一个节点名        │   │
│  │      {"clarify": "ask", "proceed": "generate"}           │   │
│  │  )                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph API

```python
# ============================================
# LangGraph 基础API
# ============================================

from langgraph.graph import StateGraph, END, START
from typing import TypedDict

# 1. 定义状态
class MyState(TypedDict):
    input: str
    output: str

# 2. 创建图
graph = StateGraph(MyState)

# 3. 添加节点
def my_node(state: MyState) -> dict:
    return {"output": state["input"].upper()}

graph.add_node("my_node", my_node)

# 4. 添加边
graph.add_edge(START, "my_node")  # 从开始到节点
graph.add_edge("my_node", END)    # 从节点到结束

# 5. 编译
app = graph.compile()

# 6. 运行
result = app.invoke({"input": "hello"})
print(result)  # {"input": "hello", "output": "HELLO"}
```

---

## 5.3 本项目的工作流设计

### 完整工作流图

```
┌─────────────────────────────────────────────────────────────────┐
│              Smart Home Agent 完整工作流                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                         ┌───────────┐                           │
│                         │   START   │                           │
│                         └─────┬─────┘                           │
│                               │                                 │
│                               ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    parse_intent                          │   │
│  │                                                          │   │
│  │  输入: user_input                                        │   │
│  │  处理: LLM提取结构化意图                                 │   │
│  │  输出: parsed_intent                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│                               ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   retrieve_context                       │   │
│  │                                                          │   │
│  │  输入: parsed_intent                                     │   │
│  │  处理: GraphRAG检索相关上下文                            │   │
│  │  输出: retrieved_context, retrieval_metadata             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│                               ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  check_sufficiency                       │   │
│  │                                                          │   │
│  │  输入: retrieved_context, parsed_intent                  │   │
│  │  处理: 判断上下文是否足够                                │   │
│  │  输出: needs_clarification, clarification_question       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│               ┌───────────────┴───────────────┐                 │
│               │                               │                 │
│               ▼ needs_clarification=True      ▼ False           │
│  ┌───────────────────────┐        ┌───────────────────────┐    │
│  │   ask_clarification   │        │    generate_plan      │    │
│  │                       │        │                       │    │
│  │  设置response为问题   │        │  LLM生成操作计划      │    │
│  └───────────┬───────────┘        └───────────┬───────────┘    │
│              │                                │                 │
│              ▼                                ▼                 │
│         ┌────────┐               ┌───────────────────────┐     │
│         │  END   │               │   increment_counter   │     │
│         └────────┘               │                       │     │
│                                  │  防止无限循环          │     │
│                                  └───────────┬───────────┘     │
│                                              │                  │
│                                              ▼                  │
│                                 ┌───────────────────────┐      │
│                                 │    validate_plan      │      │
│                                 │                       │      │
│                                 │  验证计划有效性        │      │
│                                 └───────────┬───────────┘      │
│                                             │                   │
│                          ┌──────────────────┴──────────────┐   │
│                          │                                 │   │
│                          ▼ is_valid=False                  ▼   │
│                          │ & iteration<2                   │   │
│             ┌────────────┴────────────┐     ┌─────────────────┐│
│             │    generate_plan        │     │generate_response││
│             │    (重试)               │     │                 ││
│             └─────────────────────────┘     │ 生成友好回复    ││
│                                             └────────┬────────┘│
│                                                      │         │
│                                                      ▼         │
│                                                 ┌────────┐     │
│                                                 │  END   │     │
│                                                 └────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 状态定义

```python
# src/agent/state.py

from typing import TypedDict, Optional, Annotated
from typing_extensions import TypedDict

def replace_value(current, new):
    """替换策略：用新值替换旧值"""
    return new

def append_to_list(current, new):
    """追加策略：追加到列表"""
    if current is None:
        current = []
    if isinstance(new, list):
        return current + new
    return current + [new]

class AgentState(TypedDict, total=False):
    """
    Agent状态定义

    字段说明:
    - Annotated[type, reducer] 指定状态更新策略
    - total=False 允许字段可选
    """

    # 输入
    user_input: str

    # 意图解析阶段
    parsed_intent: Annotated[Optional[dict], replace_value]

    # 检索阶段
    retrieved_context: Annotated[Optional[str], replace_value]
    retrieval_metadata: Annotated[Optional[dict], replace_value]

    # 推理阶段
    reasoning_trace: Annotated[list[str], append_to_list]

    # 计划阶段
    action_plan: Annotated[Optional[dict], replace_value]

    # 验证阶段
    validation_result: Annotated[Optional[dict], replace_value]

    # 输出阶段
    final_response: Annotated[Optional[str], replace_value]

    # 控制流
    needs_clarification: Annotated[bool, replace_value]
    clarification_question: Annotated[Optional[str], replace_value]
    error: Annotated[Optional[str], replace_value]
    iteration_count: Annotated[int, replace_value]
```

### 节点实现

```python
# src/agent/nodes.py

def parse_intent(state: AgentState) -> dict:
    """
    节点1: 解析用户意图

    输入: state["user_input"]
    输出: {"parsed_intent": {...}, "reasoning_trace": [...]}
    """
    user_input = state["user_input"]

    # 调用LLM解析
    llm = get_llm()
    prompt = INTENT_PARSER_PROMPT.format_messages(user_input=user_input)
    response = llm.invoke(prompt)

    # 解析输出
    parsed = extract_json(response.content)

    return {
        "parsed_intent": parsed,
        "reasoning_trace": [f"解析意图: {parsed.get('goal')}"]
    }


def retrieve_context(state: AgentState) -> dict:
    """
    节点2: GraphRAG检索

    输入: state["parsed_intent"]
    输出: {"retrieved_context": "...", "retrieval_metadata": {...}}
    """
    intent = state.get("parsed_intent", {})
    retriever = get_retriever()

    context_parts = []
    metadata = {"strategies_used": []}

    # 根据意图选择检索策略
    rooms = intent.get("rooms", [])
    if rooms:
        for room in rooms:
            result = retriever.get_room_context(room)
            context_parts.append(result.formatted_context)
            metadata["strategies_used"].append("room_context")

    # 合并上下文
    combined = "\n\n---\n\n".join(context_parts)

    return {
        "retrieved_context": combined,
        "retrieval_metadata": metadata,
        "reasoning_trace": [f"使用策略: {metadata['strategies_used']}"]
    }


def check_sufficiency(state: AgentState) -> dict:
    """
    节点3: 检查上下文充分性

    这是一个决策节点，不调用LLM，只做逻辑判断
    """
    context = state.get("retrieved_context", "")
    intent = state.get("parsed_intent", {})

    if "No relevant context" in context:
        return {
            "needs_clarification": True,
            "clarification_question": "请问您指的是哪个房间？"
        }

    return {"needs_clarification": False}


def generate_plan(state: AgentState) -> dict:
    """
    节点4: 生成操作计划
    """
    intent = state.get("parsed_intent", {})
    context = state.get("retrieved_context", "")

    llm = get_llm()
    prompt = ACTION_PLAN_PROMPT.format_messages(
        parsed_intent=json.dumps(intent),
        retrieved_context=context
    )
    response = llm.invoke(prompt)

    plan = extract_json(response.content)

    return {
        "action_plan": plan,
        "reasoning_trace": [f"生成计划: {len(plan.get('actions', []))}个操作"]
    }


def validate_plan(state: AgentState) -> dict:
    """
    节点5: 验证计划
    """
    plan = state.get("action_plan", {})
    context = state.get("retrieved_context", "")

    issues = []
    for action in plan.get("actions", []):
        device = action.get("device_name", "")
        if device.lower() not in context.lower():
            issues.append(f"设备 '{device}' 不在上下文中")

    return {
        "validation_result": {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    }


def generate_response(state: AgentState) -> dict:
    """
    节点6: 生成最终响应
    """
    plan = state.get("action_plan", {})

    llm = get_llm(temperature=0.7)
    prompt = RESPONSE_PROMPT.format_messages(
        user_input=state["user_input"],
        action_plan=json.dumps(plan)
    )
    response = llm.invoke(prompt)

    return {"final_response": response.content}
```

### 路由函数

```python
# src/agent/nodes.py

from typing import Literal

def route_after_check(state: AgentState) -> Literal["ask_clarification", "generate_plan"]:
    """
    条件路由: 根据是否需要澄清决定下一步

    返回值是目标节点的名称
    """
    if state.get("needs_clarification", False):
        return "ask_clarification"
    return "generate_plan"


def route_after_validation(state: AgentState) -> Literal["generate_response", "regenerate_plan"]:
    """
    条件路由: 根据验证结果决定下一步
    """
    validation = state.get("validation_result", {})

    if validation.get("is_valid", False):
        return "generate_response"

    # 防止无限循环
    if state.get("iteration_count", 0) >= 2:
        return "generate_response"

    return "regenerate_plan"
```

### 工作流组装

```python
# src/agent/workflow.py

from langgraph.graph import StateGraph, END, START
from src.agent.state import AgentState
from src.agent.nodes import *

def create_workflow() -> StateGraph:
    """创建Agent工作流"""

    # 创建图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("check_sufficiency", check_sufficiency)
    workflow.add_node("ask_clarification", ask_clarification)
    workflow.add_node("generate_plan", generate_plan)
    workflow.add_node("increment_counter", increment_counter)
    workflow.add_node("validate_plan", validate_plan)
    workflow.add_node("generate_response", generate_response)

    # 添加边

    # 开始 → 解析意图
    workflow.add_edge(START, "parse_intent")

    # 解析意图 → 检索上下文
    workflow.add_edge("parse_intent", "retrieve_context")

    # 检索上下文 → 检查充分性
    workflow.add_edge("retrieve_context", "check_sufficiency")

    # 检查充分性 → 条件分支
    workflow.add_conditional_edges(
        "check_sufficiency",
        route_after_check,
        {
            "ask_clarification": "ask_clarification",
            "generate_plan": "generate_plan"
        }
    )

    # 请求澄清 → 结束
    workflow.add_edge("ask_clarification", END)

    # 生成计划 → 计数器 → 验证
    workflow.add_edge("generate_plan", "increment_counter")
    workflow.add_edge("increment_counter", "validate_plan")

    # 验证 → 条件分支
    workflow.add_conditional_edges(
        "validate_plan",
        route_after_validation,
        {
            "generate_response": "generate_response",
            "regenerate_plan": "generate_plan"  # 循环回去
        }
    )

    # 生成响应 → 结束
    workflow.add_edge("generate_response", END)

    return workflow


def compile_workflow():
    """编译工作流"""
    workflow = create_workflow()
    return workflow.compile()
```

---

## 5.4 运行与调试

### 基本运行

```python
# 创建Agent
from src.agent import SmartHomeAgent

agent = SmartHomeAgent()

# 运行
response = agent.run("打开客厅的灯")
print(response)
```

### 流式运行

```python
# 流式查看每一步
for event in agent.run_streaming("把客厅弄舒服一点"):
    for node_name, updates in event.items():
        print(f"节点: {node_name}")
        print(f"更新: {updates.keys()}")
```

### 获取完整状态

```python
# 获取完整的最终状态
state = agent.get_full_state("准备电影之夜")

print("解析的意图:", state["parsed_intent"])
print("检索的上下文长度:", len(state["retrieved_context"]))
print("操作计划:", state["action_plan"])
print("推理轨迹:", state["reasoning_trace"])
```

### 调试技巧

```
┌─────────────────────────────────────────────────────────────────┐
│                     调试技巧                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣ 使用reasoning_trace追踪执行                                 │
│     state["reasoning_trace"] 记录每一步的关键信息               │
│                                                                 │
│  2️⃣ 使用流式执行观察中间状态                                    │
│     for event in agent.run_streaming(...):                      │
│         # 可以看到每个节点的输出                                 │
│                                                                 │
│  3️⃣ 单独测试节点                                                │
│     result = parse_intent({"user_input": "测试"})               │
│     # 直接调用节点函数进行单元测试                               │
│                                                                 │
│  4️⃣ 使用state_summary()查看状态摘要                             │
│     from src.agent.state import state_summary                   │
│     print(state_summary(final_state))                           │
│                                                                 │
│  5️⃣ 检查中间产物                                                │
│     • parsed_intent: 意图解析是否正确？                         │
│     • retrieved_context: 检索到正确的信息了吗？                 │
│     • action_plan: 计划合理吗？                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 本章小结

| 主题 | 要点 |
|------|------|
| **状态机** | 明确状态、显式转换、可追踪 |
| **LangGraph三要素** | State、Node、Edge |
| **节点设计** | 单一职责、读取状态、返回更新 |
| **条件路由** | 根据状态决定下一节点 |
| **调试方法** | 流式执行、推理轨迹、状态摘要 |

---

## 🎯 动手实验

完成 `notebooks/03_full_agent.ipynb` 中的练习：

1. 运行完整Agent
2. 分析每个节点的输入输出
3. 添加新节点扩展功能

---

下一节：[06_系统架构图.md](./06_系统架构图.md)
