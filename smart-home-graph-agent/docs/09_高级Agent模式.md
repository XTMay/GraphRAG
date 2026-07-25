# 模块九：高级 Agent 模式

## 学习目标

-   理解 Tool Use / Function Calling 的工作原理
-   掌握 Agent 对话记忆的设计与实现
-   了解流式处理（Streaming）的不同方式
-   对比显式工作流与工具调用两种 Agent 设计模式

------------------------------------------------------------------------

## 9.1 Tool Use / Function Calling

### 概念

**Function Calling** 是 LLM 的一项能力：LLM 不仅能生成文本，还能"调用函数"——它输出结构化的函数调用请求，由我们的代码执行后将结果返回给 LLM。

```{mermaid}
sequenceDiagram
    participant U as 用户
    participant LLM as LLM
    participant T as Tool代码

    U->>LLM: 客厅有什么设备
    Note over LLM: 思考：需要查询客厅设备信息
    LLM->>T: query_room_devices(客厅)
    T-->>LLM: 吸顶灯, 电视, ...
    LLM-->>U: 客厅有以下设备：吸顶灯、智能电视...
```

### ReAct 模式

Tool Use 通常与 **ReAct**（Reasoning + Acting）模式结合：

```{mermaid}
graph LR
    R1["思考<br/>Reason"] --> A1["行动<br/>Act"]
    A1 --> O1["观察<br/>Observe"]
    O1 --> R2["思考"]
    R2 --> A2["行动"]
    A2 --> O2["观察"]
    O2 --> DONE["最终回复"]
```

**示例：打开客厅灯**

```{mermaid}
graph TD
    S1["Step 1 思考: 需要先查询客厅有什么灯"]
    S2["Step 2 行动: query_room_devices 客厅"]
    S3["Step 3 观察: 找到 Ceiling Light 有 power 能力"]
    S4["Step 4 思考: 可以执行命令了"]
    S5["Step 5 行动: execute_device_command"]
    S6["Step 6 观察: 命令执行成功"]
    S7["Step 7 最终回复: 已为您打开客厅吸顶灯"]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7
```

### 代码实现

#### 定义 Tool

``` python
from langchain_core.tools import tool

@tool
def query_room_devices(room_name: str) -> str:
    """查询指定房间的所有设备和能力。
    当用户提到特定房间时使用此工具。

    Args:
        room_name: 房间名称，支持模糊匹配
    """
    conn = get_connection()
    results = conn.query(cypher, {"room_name": room_name})
    return format_results(results)
```

**关键点：** - `@tool` 装饰器将函数转为 LangChain Tool - **函数签名**（参数名 + 类型）会传给 LLM - **docstring** 会作为 Tool 描述传给 LLM，直接影响 LLM 的调用判断 - 返回值是字符串，LLM 可以理解

#### 绑定 Tools 到 LLM

``` python
from src.agent.tools import get_all_tools

tools = get_all_tools()
llm = get_llm()

# bind_tools 告诉 LLM "你可以调用这些函数"
llm_with_tools = llm.bind_tools(tools)
```

#### LangGraph 工作流

``` python
from langgraph.prebuilt import ToolNode

workflow = StateGraph(ToolAgentState)

workflow.add_node("agent", agent_node)       # LLM 决策节点
workflow.add_node("tools", ToolNode(tools))  # 工具执行节点

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,    # LLM 是否还要调用工具？
    {"tools": "tools", "end": END},
)
workflow.add_edge("tools", "agent")  # 工具结果返回给 LLM
```

工作流结构：

```{mermaid}
graph LR
    START(["START"]) --> agent["agent<br/>(LLM)"]
    agent -->|有 tool_calls| tools["tools<br/>(执行工具)"]
    tools --> agent
    agent -->|无 tool_calls| END_(["END"])
```

### 与显式工作流对比

**显式工作流 (SmartHomeAgent)** — 流程预先定义，每步固定：

```{mermaid}
graph TD
    A["parse_intent"] --> B["retrieve_context"]
    B --> C{"check_sufficiency"}
    C -->|充分| D["generate_plan"]
    C -->|不足| E["ask_clarification"]
    D --> F{"validate_plan"}
    F -->|有效| G["generate_response"]
    F -->|无效| D
    G --> H(["END"])
    E --> H
```

**工具调用 (ToolCallingAgent)** — 流程由 LLM 动态决定：

```{mermaid}
graph TD
    A2["agent LLM"] -->|调用工具| B2["tools"]
    B2 --> A2
    A2 -->|调用工具| C2["tools"]
    C2 --> D2["agent LLM"]
    D2 -->|完成| E2(["END"])
```

------------------------------------------------------------------------

## 9.2 Agent 记忆

### 为什么需要记忆？

没有记忆的 Agent：

```         
用户: "客厅有什么灯？"
Agent: "客厅有吸顶灯和落地灯。"

用户: "把那个亮一点的调暗"      ← Agent 不知道"那个"指什么！
Agent: "请问您指哪个灯？"
```

有记忆的 Agent：

```         
用户: "客厅有什么灯？"
Agent: "客厅有吸顶灯和落地灯。"

用户: "把那个亮一点的调暗"      ← Agent 记得上一轮对话
Agent: "好的，已将客厅吸顶灯亮度调低。"
```

### 记忆类型

| 类型                   | 原理             | 优点            | 缺点             |
|------------------|------------------|------------------|------------------|
| **Buffer（完整缓冲）** | 存储所有历史消息 | 完整上下文      | Token 消耗大     |
| **Window（滑动窗口）** | 只保留最近 N 轮  | 控制 Token 用量 | 可能丢失早期信息 |
| **Summary（摘要）**    | LLM 总结历史     | 压缩率高        | 可能丢失细节     |

我们实现的是 **Window（滑动窗口）** 记忆：

``` python
class ConversationMemory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._sessions: dict[str, list[Message]] = {}

    def add_message(self, session_id, role, content):
        self._sessions[session_id].append(Message(role, content))
        # 滑动窗口：只保留最近 max_turns 轮
        max_messages = self.max_turns * 2
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]
```

### 多会话管理

每个 `session_id` 对应一个独立的对话：

``` python
memory = ConversationMemory()

# 用户 A 的对话
memory.add_message("user-a", "user", "客厅有什么灯？")
memory.add_message("user-a", "assistant", "有吸顶灯和落地灯。")

# 用户 B 的对话（独立的！）
memory.add_message("user-b", "user", "卧室温度多少？")
memory.add_message("user-b", "assistant", "当前卧室温度 24°C。")
```

### 与 API 集成

``` python
class ToolCallingAgent:
    def run(self, user_input, session_id=None):
        # 1. 构建消息列表（包含历史）
        messages = self._build_messages(user_input, session_id)

        # 2. 执行 Agent 工作流
        result = self.workflow.invoke({"messages": messages})
        response = result["messages"][-1].content

        # 3. 保存到记忆
        if session_id:
            self.memory.add_message(session_id, "user", user_input)
            self.memory.add_message(session_id, "assistant", response)

        return response
```

------------------------------------------------------------------------

## 9.3 流式处理

### Token 级 vs 节点级 Streaming

| 方式         | 粒度           | 用户体验        | 实现复杂度 |
|--------------|----------------|-----------------|------------|
| **Token 级** | 每个 Token     | 文字逐字出现    | 较高       |
| **节点级**   | 每个工作流节点 | 进度条/步骤显示 | 较低       |

我们的实现使用**节点级 Streaming**：

``` python
# 节点级流式（SmartHomeAgent）
for event in agent.run_streaming("打开客厅灯"):
    for node_name, data in event.items():
        print(f"[{node_name}] 完成")

# 输出：
# [parse_intent] 完成
# [retrieve_context] 完成
# [check_sufficiency] 完成
# [generate_plan] 完成
# [increment_counter] 完成
# [validate_plan] 完成
# [generate_response] 完成
```

### SSE vs WebSocket

| 特性       | SSE             | WebSocket  |
|------------|-----------------|------------|
| 通信方向   | 服务端 → 客户端 | 双向       |
| 协议       | HTTP            | ws://      |
| 自动重连   | 浏览器内置      | 需自己实现 |
| 适合场景   | LLM 流式输出    | 实时聊天   |
| 防火墙友好 | 是（HTTP）      | 可能被拦截 |

> **AI 应用推荐 SSE**：因为流式输出是单向的（服务端 → 客户端），SSE 更简单。

------------------------------------------------------------------------

## 9.4 Agent 设计模式对比

### 显式工作流 vs 工具调用

| 维度             | 显式工作流 (SmartHomeAgent) | 工具调用 (ToolCallingAgent) |
|---------------|-----------------------------|-----------------------------|
| **流程控制**     | 预定义的状态图              | LLM 动态决定                |
| **可预测性**     | 高（每次走固定路径）        | 低（LLM 可能选不同工具）    |
| **灵活性**       | 低（新场景需改代码）        | 高（LLM 自行组合工具）      |
| **调试难度**     | 容易（看 trace 即可）       | 较难（需看完整消息链）      |
| **LLM 调用次数** | 固定（3次：解析+规划+回复） | 不固定（取决于 LLM 决策）   |
| **成本**         | 可预测                      | 波动大                      |
| **适用场景**     | 流程明确、需要可靠性        | 开放域、需要灵活性          |

### 何时选择哪种模式？

```{mermaid}
graph LR
    subgraph 高可预测性
        A["业务流程 / 合规系统<br/>→ 显式工作流"]
        B["智能家居控制<br/>→ 混合模式"]
    end
    subgraph 低可预测性
        C["通用助手 / 开放对话<br/>→ 工具调用"]
    end
    A -.- B
    B -.- C
    style A fill:#d4edda
    style B fill:#fff3cd
    style C fill:#cce5ff
```

> -   **左上角**（高可预测 + 低灵活）→ 显式工作流：业务流程、合规系统
> -   **中间**（中等灵活 + 中等可预测）→ 混合模式：智能家居控制
> -   **右下角**（高灵活 + 低可预测）→ 工具调用：通用助手、开放对话

### 实际建议

1.  **从显式工作流开始** — 更容易理解、调试、控制成本
2.  **在需要灵活性时引入工具调用** — 当预定义流程无法覆盖所有场景
3.  **混合模式** — 核心流程用显式工作流，扩展功能用工具调用

------------------------------------------------------------------------

## 9.5 动手实验

请打开 `notebooks/06_advanced_agent_patterns.ipynb`，完成以下实验：

### 实验 1：Tool 定义和手动调用

``` python
from src.agent.tools import get_all_tools

tools = get_all_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description[:50]}...")

# 手动调用 Tool
result = tools[0].invoke({"room_name": "living"})
print(result)
```

### 实验 2：ToolCallingAgent vs SmartHomeAgent

``` python
from src.agent.workflow import SmartHomeAgent
from src.agent.tool_agent import ToolCallingAgent

# 显式工作流 Agent
explicit_agent = SmartHomeAgent()
response1, trace1 = explicit_agent.run_with_trace("打开客厅灯")

# 工具调用 Agent
tool_agent = ToolCallingAgent()
response2, trace2 = tool_agent.run_with_trace("打开客厅灯")

# 对比
print("=== 显式工作流 ===")
print(f"响应: {response1}")
print(f"步骤数: {len(trace1)}")

print("\n=== 工具调用 ===")
print(f"响应: {response2}")
print(f"步骤数: {len(trace2)}")
```

### 实验 3：对话记忆

``` python
agent = ToolCallingAgent()

# 多轮对话
r1 = agent.run("客厅有什么设备？", session_id="test-1")
print(f"第一轮: {r1}")

r2 = agent.run("把灯调暗一点", session_id="test-1")
print(f"第二轮: {r2}")

r3 = agent.run("再暗一些", session_id="test-1")
print(f"第三轮: {r3}")
```

### 实验 4：Streaming 对比

``` python
# SmartHomeAgent 流式
print("=== SmartHomeAgent 流式 ===")
for event in explicit_agent.run_streaming("电影模式"):
    for node, data in event.items():
        print(f"  [{node}] → keys: {list(data.keys())}")

# ToolCallingAgent 流式
print("\n=== ToolCallingAgent 流式 ===")
for event in tool_agent.run_streaming("电影模式"):
    for node, data in event.items():
        print(f"  [{node}] → messages: {len(data.get('messages', []))}")
```

------------------------------------------------------------------------

## 关键代码文件

| 文件                      | 内容                     |
|---------------------------|--------------------------|
| `src/agent/tools.py`      | LangChain Tool 定义      |
| `src/agent/memory.py`     | 对话记忆管理             |
| `src/agent/tool_agent.py` | ReAct 工具调用 Agent     |
| `src/agent/workflow.py`   | 显式工作流 Agent（对比） |

------------------------------------------------------------------------

上一节：[08_Docker容器化部署.md](./08_Docker容器化部署.md)