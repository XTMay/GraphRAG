"""
LangChain Tool Definitions
===========================

Define tools that the LLM can call via Function Calling / Tool Use.

Teaching Points:
- Tools are functions with typed signatures that LLMs can invoke
- The @tool decorator converts a function into a LangChain Tool
- Tool descriptions are part of the LLM prompt (they matter!)
- Tools bridge the gap between LLM reasoning and external systems
"""

from langchain_core.tools import tool

from src.graph.connection import get_connection
from src.graph.queries import SmartHomeQueries


# Shared query templates
_queries = SmartHomeQueries()


# =========================================
# TOOL: Query Room Devices
# =========================================

@tool
def query_room_devices(room_name: str) -> str:
    """查询指定房间的所有设备和能力。

    当用户提到特定房间时使用此工具，例如"客厅有什么设备"、"打开卧室的灯"。

    Args:
        room_name: 房间名称，支持模糊匹配（如 "living" 匹配 "Living Room"）
    """
    conn = get_connection()
    query = _queries.get_room_with_devices()
    results = conn.query(query, {"room_name": room_name})

    if not results:
        return f"未找到匹配 '{room_name}' 的房间。"

    lines = []
    for row in results:
        lines.append(f"房间: {row['room_name']} ({row.get('room_type', '')}, {row.get('floor', '')})")
        for device in row.get("devices", []):
            caps = ", ".join(device.get("capabilities", []))
            status = device.get("status", "unknown")
            lines.append(f"  - {device['name']} ({device.get('type', '')}), 状态: {status}")
            lines.append(f"    能力: {caps}")

    return "\n".join(lines)


# =========================================
# TOOL: Query Device Capabilities
# =========================================

@tool
def query_device_capabilities(device_name: str) -> str:
    """查询指定设备的详细信息和所有能力。

    当用户询问某个设备能做什么时使用，例如"智能音箱能做什么"。

    Args:
        device_name: 设备名称，支持模糊匹配
    """
    conn = get_connection()
    query = _queries.get_device_details()
    results = conn.query(query, {"device_name": device_name})

    if not results:
        return f"未找到匹配 '{device_name}' 的设备。"

    lines = []
    for row in results:
        lines.append(f"设备: {row['name']} (ID: {row['device_id']})")
        lines.append(f"  类型: {row.get('type', 'N/A')}, 品牌: {row.get('brand', 'N/A')}")
        lines.append(f"  位置: {row.get('room', 'N/A')}, 状态: {row.get('status', 'N/A')}")
        lines.append("  能力:")
        for cap in row.get("capabilities", []):
            desc = cap.get("description", "")
            params = cap.get("parameters", "")
            lines.append(f"    - {cap.get('name', 'N/A')}: {desc}")
            if params:
                lines.append(f"      参数: {params}")

    return "\n".join(lines)


# =========================================
# TOOL: Search Scenes
# =========================================

@tool
def search_scenes(keyword: str) -> str:
    """搜索智能家居场景（预设模式）。

    当用户提到场景或氛围时使用，例如"电影模式"、"睡前模式"、"派对模式"。

    Args:
        keyword: 搜索关键词，匹配场景名称、描述或氛围
    """
    conn = get_connection()
    query = _queries.get_scene_details()
    results = conn.query(query, {"scene_name": keyword})

    if not results:
        return f"未找到匹配 '{keyword}' 的场景。"

    lines = []
    for scene in results:
        lines.append(f"场景: {scene.get('scene_name', 'N/A')}")
        lines.append(f"  描述: {scene.get('description', 'N/A')}")
        lines.append(f"  氛围: {scene.get('mood', 'N/A')}")
        rooms = scene.get("applicable_rooms", [])
        if rooms:
            lines.append(f"  适用房间: {', '.join(filter(None, rooms))}")
        actions = scene.get("device_actions", [])
        if actions:
            lines.append("  设备动作:")
            for action in actions:
                if action.get("device"):
                    lines.append(f"    - {action['device']}: {action.get('action', 'N/A')}")

    return "\n".join(lines)


# =========================================
# TOOL: Execute Device Command (Simulated)
# =========================================

@tool
def execute_device_command(device_id: str, capability: str, value: str) -> str:
    """执行设备命令（模拟执行）。

    控制智能家居设备。在真实系统中，这会调用设备的API。这里是模拟执行。

    Args:
        device_id: 设备ID（如 "living_ceiling_01"）
        capability: 要使用的能力（如 "dim", "power", "color"）
        value: 设置的值（如 "on", "50", "warm"）
    """
    # In a real system, this would call the device's API
    # For teaching purposes, we simulate success
    return (
        f"✅ 命令已执行（模拟）:\n"
        f"  设备: {device_id}\n"
        f"  操作: {capability} = {value}\n"
        f"  状态: 成功"
    )


# =========================================
# UTILITY: Get All Tools
# =========================================

def get_all_tools() -> list:
    """
    Return all available tools for the agent.

    Teaching Point:
        This function collects all tools in one place,
        making it easy to bind them to an LLM or agent.
    """
    return [
        query_room_devices,
        query_device_capabilities,
        search_scenes,
        execute_device_command,
    ]


if __name__ == "__main__":
    print("Smart Home Tools")
    print("=" * 50)
    for t in get_all_tools():
        print(f"\n{t.name}: {t.description[:80]}...")
