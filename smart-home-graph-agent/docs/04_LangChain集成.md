# 第四章：LangChain集成

## 📖 本章目标

1. 掌握LangChain的核心组件
2. 理解Prompt工程最佳实践
3. 学会结构化输出解析
4. 完成动手实验：LLM调用

---

## 4.1 LangChain核心组件

### 组件架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                   LangChain 组件架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Model I/O 层                            │ │
│  │                                                            │ │
│  │   输入处理          模型调用           输出处理             │ │
│  │  ┌─────────┐      ┌─────────┐      ┌─────────┐            │ │
│  │  │ Prompts │ ───→ │  LLMs   │ ───→ │ Parsers │            │ │
│  │  │         │      │         │      │         │            │ │
│  │  │•Template│      │•ChatGPT │      │•JSON    │            │ │
│  │  │•Messages│      │•Claude  │      │•Pydantic│            │ │
│  │  │•Examples│      │•Local   │      │•Regex   │            │ │
│  │  └─────────┘      └─────────┘      └─────────┘            │ │
│  │                                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Chain 组合层                            │ │
│  │                                                            │ │
│  │   简单Chain              复杂Chain                         │ │
│  │  ┌─────────────┐      ┌─────────────────────────┐         │ │
│  │  │   prompt    │      │  prompt1 → llm1         │         │ │
│  │  │     │       │      │      │                  │         │ │
│  │  │     ▼       │      │      ▼                  │         │ │
│  │  │    llm      │      │  prompt2 → llm2         │         │ │
│  │  │     │       │      │      │                  │         │ │
│  │  │     ▼       │      │      ▼                  │         │ │
│  │  │  parser     │      │   output                │         │ │
│  │  └─────────────┘      └─────────────────────────┘         │ │
│  │                                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ChatPromptTemplate详解

```python
# ============================================
# ChatPromptTemplate 使用方式
# ============================================

from langchain_core.prompts import ChatPromptTemplate

# 方式1: 从消息列表创建
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}。"),
    ("human", "{question}")
])

# 方式2: 使用Message类
from langchain_core.messages import SystemMessage, HumanMessage

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="你是一个智能家居助手。"),
    HumanMessage(content="{user_input}")
])

# 调用方式
messages = prompt.format_messages(
    role="智能家居助手",
    question="打开客厅的灯"
)
# 或者使用invoke
messages = prompt.invoke({
    "role": "智能家居助手",
    "question": "打开客厅的灯"
})
```

### Chat Model调用

```python
# ============================================
# LLM调用方式
# ============================================

from langchain_openai import ChatOpenAI

# 创建模型实例
llm = ChatOpenAI(
    model="gpt-4o-mini",    # 模型名称
    temperature=0,           # 0=确定性输出，1=创造性输出
    max_tokens=1000,        # 最大输出token数
)

# 直接调用
response = llm.invoke("你好，请介绍一下自己")
print(response.content)

# 使用消息列表调用
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="你是一个智能家居助手"),
    HumanMessage(content="打开客厅的灯")
]
response = llm.invoke(messages)

# 流式输出
for chunk in llm.stream("讲一个故事"):
    print(chunk.content, end="", flush=True)
```

### Chain组合 (LCEL语法)

```python
# ============================================
# LangChain Expression Language (LCEL)
# ============================================

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 定义组件
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能家居助手。"),
    ("human", "{input}")
])

llm = ChatOpenAI(model="gpt-4o-mini")

parser = StrOutputParser()  # 提取content字符串

# 使用 | 操作符组合 (类似Unix管道)
chain = prompt | llm | parser

# 调用
result = chain.invoke({"input": "打开客厅的灯"})
print(result)  # 直接是字符串

# 更复杂的组合
from langchain_core.runnables import RunnablePassthrough

chain = (
    {"input": RunnablePassthrough()}  # 传递输入
    | prompt
    | llm
    | parser
)
```

---

## 4.2 Prompt工程

### 本项目的Prompt设计

```
┌─────────────────────────────────────────────────────────────────┐
│                   Prompt设计架构                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 1. 意图解析Prompt                        │   │
│  │                                                          │   │
│  │  目的: 从自然语言提取结构化意图                          │   │
│  │                                                          │   │
│  │  System:                                                 │   │
│  │  ┌───────────────────────────────────────────────────┐  │   │
│  │  │ 你是一个意图解析器。提取以下信息:                  │  │   │
│  │  │ - goal: 用户目标                                  │  │   │
│  │  │ - rooms: 涉及的房间                               │  │   │
│  │  │ - mood: 期望的氛围                                │  │   │
│  │  │ - scene_hint: 提到的场景                          │  │   │
│  │  │ 返回JSON格式。                                    │  │   │
│  │  └───────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  Human: "把客厅弄得舒服一点"                             │   │
│  │                                                          │   │
│  │  Output:                                                 │   │
│  │  {                                                       │   │
│  │    "goal": "创造舒适氛围",                               │   │
│  │    "rooms": ["客厅"],                                    │   │
│  │    "mood": "cozy",                                       │   │
│  │    "scene_hint": null                                    │   │
│  │  }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 2. 计划生成Prompt                        │   │
│  │                                                          │   │
│  │  目的: 根据意图和上下文生成设备操作计划                  │   │
│  │                                                          │   │
│  │  System:                                                 │   │
│  │  ┌───────────────────────────────────────────────────┐  │   │
│  │  │ 你是一个智能家居规划器。                           │  │   │
│  │  │ 规则:                                             │  │   │
│  │  │ - 只使用上下文中存在的设备                         │  │   │
│  │  │ - 只使用设备支持的能力                             │  │   │
│  │  │ - 为每个操作提供理由                               │  │   │
│  │  │ 返回JSON格式的action plan。                       │  │   │
│  │  └───────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  Human:                                                  │   │
│  │  意图: {parsed_intent}                                   │   │
│  │  上下文: {retrieved_context}                             │   │
│  │                                                          │   │
│  │  Output:                                                 │   │
│  │  {                                                       │   │
│  │    "reasoning": "为创造舒适氛围，调暗灯光...",           │   │
│  │    "actions": [                                          │   │
│  │      {"device": "吊灯", "action": "dim", "value": 30}   │   │
│  │    ]                                                     │   │
│  │  }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 3. 响应生成Prompt                        │   │
│  │                                                          │   │
│  │  目的: 将技术性计划转为友好的用户响应                    │   │
│  │                                                          │   │
│  │  System:                                                 │   │
│  │  ┌───────────────────────────────────────────────────┐  │   │
│  │  │ 你是一个友好的智能家居助手。                       │  │   │
│  │  │ 将操作计划转换为自然语言回复。                     │  │   │
│  │  │ - 简洁友好                                         │  │   │
│  │  │ - 提及关键操作                                     │  │   │
│  │  │ - 适当使用表情（仅在轻松场景）                     │  │   │
│  │  └───────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  Output:                                                 │   │
│  │  "好的！我把吊灯调暗到30%，落地灯调到40%，              │   │
│  │   现在客厅应该很舒服了～"                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Prompt设计原则

```
┌─────────────────────────────────────────────────────────────────┐
│                   Prompt设计原则                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣ 明确角色 (Role)                                            │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ✅ "你是一个智能家居助手，负责解析用户指令"          │    │
│     │ ❌ "解析用户指令"                                    │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
│  2️⃣ 明确输出格式 (Format)                                      │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ✅ "返回JSON格式，包含以下字段: ..."                 │    │
│     │ ❌ "返回结果"                                        │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
│  3️⃣ 提供约束条件 (Constraints)                                 │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ✅ "只使用上下文中存在的设备"                        │    │
│     │    "如果信息不足，返回null"                          │    │
│     │ ❌ 无约束 (可能产生幻觉)                             │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
│  4️⃣ 提供示例 (Few-shot)                                        │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ✅ 输入: "打开客厅灯"                                │    │
│     │    输出: {"goal": "打开灯", "rooms": ["客厅"]}       │    │
│     │                                                      │    │
│     │    输入: "太暗了"                                    │    │
│     │    输出: {"goal": "增加亮度", "rooms": []}           │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
│  5️⃣ 处理边界情况 (Edge Cases)                                  │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ ✅ "如果无法理解请求，返回 {\"error\": \"...\"}      │    │
│     │    "如果字段不确定，使用null而非猜测"                │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 本项目Prompt代码

```python
# src/agent/prompts.py

# 意图解析Prompt
INTENT_PARSER_SYSTEM = """你是一个意图解析器，从自然语言请求中提取结构化信息。

提取以下字段:
1. goal: 用户想要达成的目标
2. rooms: 涉及的房间列表
3. actions: 提到的具体动作
4. mood: 期望的氛围/情绪
5. scene_hint: 提到的场景名称
6. constraints: 任何约束条件

返回JSON格式。如果某字段无法确定，使用null。

示例输出:
{
    "goal": "准备观影",
    "rooms": ["客厅"],
    "actions": ["调暗灯光", "关窗帘"],
    "mood": "relaxed",
    "scene_hint": "movie night",
    "constraints": ["温度舒适"]
}"""

# 计划生成Prompt
ACTION_PLAN_SYSTEM = """你是一个智能家居规划器，根据用户意图和可用设备生成操作计划。

规则:
1. 只使用上下文中存在的设备
2. 只使用设备实际具有的能力
3. 为每个操作提供简短理由
4. 参考相关场景但可以调整

输出JSON格式:
{
    "reasoning": "简短的规划理由",
    "actions": [
        {
            "device_id": "设备ID",
            "device_name": "设备名称",
            "capability": "使用的能力",
            "value": "设置的值",
            "reason": "操作理由"
        }
    ]
}"""
```

---

## 4.3 输出解析

### 为什么需要输出解析？

```
┌─────────────────────────────────────────────────────────────────┐
│                   输出解析的必要性                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LLM输出是字符串，但程序需要结构化数据                          │
│                                                                 │
│  LLM输出:                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ "好的，我来帮你规划一下：                                │   │
│  │                                                          │   │
│  │ ```json                                                  │   │
│  │ {                                                        │   │
│  │   \"reasoning\": \"为了舒适...\",                        │   │
│  │   \"actions\": [{...}]                                   │   │
│  │ }                                                        │   │
│  │ ```                                                      │   │
│  │                                                          │   │
│  │ 这样设置应该会很舒服！"                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  需要解析:                                                      │
│  1. 提取JSON部分 (去掉markdown标记)                             │
│  2. 解析为Python字典                                            │
│  3. 验证数据结构                                                │
│  4. 转换为类型化对象                                            │
│                                                                 │
│  解析后:                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ActionPlan(                                              │   │
│  │     reasoning="为了舒适...",                             │   │
│  │     actions=[                                            │   │
│  │         DeviceAction(                                    │   │
│  │             device_id="living_ceiling_01",               │   │
│  │             device_name="吊灯",                          │   │
│  │             capability="dim",                            │   │
│  │             value=30,                                    │   │
│  │             reason="营造氛围"                            │   │
│  │         )                                                │   │
│  │     ]                                                    │   │
│  │ )                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Pydantic数据模型

```python
# src/utils/output_parser.py

from pydantic import BaseModel, Field
from typing import Any, Optional

class ParsedIntent(BaseModel):
    """解析后的用户意图"""

    goal: str = Field(description="用户目标")
    rooms: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    mood: Optional[str] = None
    scene_hint: Optional[str] = None
    constraints: list[str] = Field(default_factory=list)


class DeviceAction(BaseModel):
    """单个设备操作"""

    device_id: str
    device_name: str
    capability: str
    value: Any
    reason: Optional[str] = None


class ActionPlan(BaseModel):
    """完整的操作计划"""

    reasoning: str
    actions: list[DeviceAction] = Field(default_factory=list)

    def to_display_string(self) -> str:
        """转换为显示字符串"""
        lines = [f"**规划理由:** {self.reasoning}", "", "**操作列表:**"]
        for i, action in enumerate(self.actions, 1):
            lines.append(f"  {i}. {action.device_name}: "
                        f"{action.capability} → {action.value}")
        return "\n".join(lines)
```

### JSON提取函数

```python
import json
import re

def extract_json(text: str) -> dict:
    """
    从LLM输出中提取JSON

    处理情况:
    1. 纯JSON字符串
    2. Markdown代码块包裹的JSON
    3. 混合文本中的JSON
    """
    # 尝试直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 尝试提取代码块中的JSON
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 尝试提取JSON对象
    json_pattern = r'\{[\s\S]*\}'
    matches = re.findall(json_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"无法从文本中提取JSON: {text[:100]}...")


def parse_action_plan(llm_output: str) -> ActionPlan:
    """解析LLM输出为ActionPlan对象"""
    data = extract_json(llm_output)
    return ActionPlan(**data)
```

---

## 4.4 完整调用流程

### 代码示例

```python
# 完整的LangChain调用流程

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 1. 创建Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", INTENT_PARSER_SYSTEM),
    ("human", "解析这个请求: {user_input}")
])

# 2. 创建LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3. 调用
messages = prompt.format_messages(user_input="把客厅弄得舒服一点")
response = llm.invoke(messages)

# 4. 解析输出
from src.utils.output_parser import extract_json, ParsedIntent

data = extract_json(response.content)
intent = ParsedIntent(**data)

print(f"目标: {intent.goal}")
print(f"房间: {intent.rooms}")
print(f"氛围: {intent.mood}")
```

### 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                   LangChain调用流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入: "把客厅弄得舒服一点"                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ChatPromptTemplate                          │   │
│  │                                                          │   │
│  │  format_messages(user_input="把客厅弄得舒服一点")        │   │
│  │                      │                                   │   │
│  │                      ▼                                   │   │
│  │  [                                                       │   │
│  │    SystemMessage(content="你是意图解析器..."),           │   │
│  │    HumanMessage(content="解析: 把客厅弄得舒服一点")      │   │
│  │  ]                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ChatOpenAI (LLM)                            │   │
│  │                                                          │   │
│  │  invoke(messages)                                        │   │
│  │       │                                                  │   │
│  │       ▼                                                  │   │
│  │  AIMessage(content="{\"goal\": \"创造舒适...\", ...}")   │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Output Parser                               │   │
│  │                                                          │   │
│  │  extract_json(response.content)                          │   │
│  │       │                                                  │   │
│  │       ▼                                                  │   │
│  │  ParsedIntent(                                           │   │
│  │      goal="创造舒适氛围",                                │   │
│  │      rooms=["客厅"],                                     │   │
│  │      mood="cozy"                                         │   │
│  │  )                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 本章小结

| 主题 | 要点 |
|------|------|
| **核心组件** | Prompt Template, Chat Model, Output Parser |
| **LCEL** | 使用 `\|` 操作符组合组件 |
| **Prompt设计** | 明确角色、格式、约束、示例 |
| **输出解析** | JSON提取 + Pydantic验证 |

---

## 🎯 动手实验

1. 修改意图解析Prompt，添加新的字段
2. 测试不同temperature对输出的影响
3. 实现自定义的OutputParser

---

下一节：[05_LangGraph工作流.md](./05_LangGraph工作流.md)
