"""
Smart Home Graph Agent - Streamlit UI
=====================================

A visual interface for the Smart Home Agent demo.

Features:
- Interactive chat with the agent
- Knowledge graph visualization
- Retrieval strategy explorer
- Debug trace viewer
- System status dashboard

Run with:
    streamlit run streamlit_app.py
"""

import os
import sys
import json
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="🏠 Smart Home Agent",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# =========================================
# CACHED RESOURCES
# =========================================

@st.cache_resource
def get_agent():
    """Get or create the Smart Home Agent (cached)."""
    try:
        from src.agent import SmartHomeAgent
        return SmartHomeAgent(debug=False)
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None


@st.cache_resource
def get_retriever():
    """Get or create the GraphRAG retriever (cached)."""
    try:
        from src.graph.retriever import SmartHomeRetriever
        return SmartHomeRetriever()
    except Exception as e:
        st.error(f"Failed to initialize retriever: {e}")
        return None


@st.cache_resource
def get_connection():
    """Get Neo4j connection (cached)."""
    try:
        from src.graph.connection import Neo4jConnection
        conn = Neo4jConnection()
        conn.connect()
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {e}")
        return None


# =========================================
# SIDEBAR
# =========================================

def render_sidebar():
    """Render the sidebar with navigation and status."""
    with st.sidebar:
        st.title("🏠 Smart Home Agent")
        st.caption("GraphRAG + LangGraph Demo")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            ["💬 Chat", "🔍 Graph Explorer", "🧪 Retrieval Lab", "📊 System Status"],
            label_visibility="collapsed"
        )

        st.divider()

        # Quick status
        st.subheader("System Status")

        # Check LLM provider
        from src.llm import get_llm_info
        llm_info = get_llm_info()
        if llm_info["status"] == "ok":
            st.success(f"✓ LLM: {llm_info['provider'].upper()} ({llm_info['model']})")
        else:
            st.error(f"✗ LLM: {llm_info['detail']}")

        # Check Neo4j
        conn = get_connection()
        if conn:
            try:
                health = conn.health_check()
                if health.get("status") == "healthy":
                    st.success(f"✓ Neo4j ({health.get('node_count', 0)} nodes)")
                else:
                    st.error("✗ Neo4j unhealthy")
            except:
                st.error("✗ Neo4j connection failed")
        else:
            st.error("✗ Neo4j not connected")

        st.divider()

        # Debug mode toggle
        st.session_state.debug_mode = st.toggle("🐛 Debug Mode", value=False)

        st.divider()

        # Info
        st.caption("Built with LangChain, LangGraph, and Neo4j")
        st.caption("[View Source Code](https://github.com)")

    return page


# =========================================
# PAGE: CHAT
# =========================================

def render_chat_page():
    """Render the main chat interface."""
    st.header("💬 Chat with Smart Home Agent")

    st.markdown("""
    Ask the agent to control your smart home! Try requests like:
    - *"Make the living room cozy for movie night"*
    - *"Turn on the kitchen lights"*
    - *"Set up the bedroom for sleep"*
    """)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "traces" not in st.session_state:
        st.session_state.traces = []

    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show trace in debug mode
            if st.session_state.get("debug_mode") and message["role"] == "assistant":
                if i // 2 < len(st.session_state.traces):
                    trace = st.session_state.traces[i // 2]
                    if trace:
                        with st.expander("🔍 Reasoning Trace"):
                            for j, step in enumerate(trace, 1):
                                st.text(f"{j}. {step}")

    # Chat input
    if prompt := st.chat_input("What would you like to do?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent = get_agent()
                if agent:
                    try:
                        if st.session_state.get("debug_mode"):
                            response, trace = agent.run_with_trace(prompt)
                            st.session_state.traces.append(trace)
                        else:
                            response = agent.run(prompt)
                            st.session_state.traces.append([])

                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

                        # Show trace
                        if st.session_state.get("debug_mode") and trace:
                            with st.expander("🔍 Reasoning Trace"):
                                for j, step in enumerate(trace, 1):
                                    st.text(f"{j}. {step}")

                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
                else:
                    st.error("Agent not available. Check system status.")

    # Clear chat button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear"):
            st.session_state.messages = []
            st.session_state.traces = []
            st.rerun()


# =========================================
# PAGE: GRAPH EXPLORER
# =========================================

def render_graph_explorer():
    """Render the knowledge graph explorer."""
    st.header("🔍 Knowledge Graph Explorer")

    conn = get_connection()
    if not conn:
        st.error("Neo4j connection not available")
        return

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Rooms", "📱 Devices", "🎬 Scenes", "📊 Graph Stats"])

    with tab1:
        st.subheader("Rooms")
        rooms = conn.query("""
            MATCH (r:Room)
            OPTIONAL MATCH (r)-[:CONTAINS]->(d:Device)
            RETURN r.name AS room, r.floor AS floor, r.type AS type,
                   count(d) AS device_count
            ORDER BY r.floor, r.name
        """)

        if rooms:
            for room in rooms:
                with st.expander(f"🏠 {room['room']} ({room['type']})"):
                    st.write(f"**Floor:** {room['floor']}")
                    st.write(f"**Devices:** {room['device_count']}")

                    # Get devices in room
                    devices = conn.query("""
                        MATCH (r:Room {name: $room_name})-[:CONTAINS]->(d:Device)
                        OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)
                        RETURN d.name AS device, d.device_type AS type,
                               d.status AS status, collect(c.name) AS capabilities
                    """, {"room_name": room['room']})

                    if devices:
                        for device in devices:
                            status_icon = "🟢" if device['status'] == 'online' else "🔴"
                            st.write(f"{status_icon} **{device['device']}** ({device['type']})")
                            st.caption(f"Capabilities: {', '.join(device['capabilities'])}")

    with tab2:
        st.subheader("All Devices")

        # Filter by type
        device_types = conn.query("""
            MATCH (d:Device)
            RETURN DISTINCT d.device_type AS type
            ORDER BY type
        """)
        type_options = ["All"] + [d['type'] for d in device_types]
        selected_type = st.selectbox("Filter by type:", type_options)

        # Query devices
        if selected_type == "All":
            devices = conn.query("""
                MATCH (r:Room)-[:CONTAINS]->(d:Device)
                OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)
                RETURN d.name AS device, d.device_type AS type, d.brand AS brand,
                       d.status AS status, r.name AS room, collect(c.name) AS capabilities
                ORDER BY r.name, d.name
            """)
        else:
            devices = conn.query("""
                MATCH (r:Room)-[:CONTAINS]->(d:Device)
                WHERE d.device_type = $type
                OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)
                RETURN d.name AS device, d.device_type AS type, d.brand AS brand,
                       d.status AS status, r.name AS room, collect(c.name) AS capabilities
                ORDER BY r.name, d.name
            """, {"type": selected_type})

        if devices:
            # Convert to dataframe-like display
            for device in devices:
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    status = "🟢" if device['status'] == 'online' else "🔴"
                    st.write(f"{status} **{device['device']}**")
                with col2:
                    st.write(f"{device['room']}")
                with col3:
                    st.caption(", ".join(device['capabilities'][:4]))

    with tab3:
        st.subheader("Scenes")

        scenes = conn.query("""
            MATCH (s:Scene)
            OPTIONAL MATCH (s)-[:APPLIES_TO]->(r:Room)
            OPTIONAL MATCH (s)-[uses:USES_DEVICE]->(d:Device)
            RETURN s.name AS scene, s.description AS description, s.mood AS mood,
                   collect(DISTINCT r.name) AS rooms,
                   collect(DISTINCT {device: d.name, action: uses.action}) AS actions
        """)

        if scenes:
            for scene in scenes:
                mood_emoji = {
                    "relaxed": "😌",
                    "energetic": "⚡",
                    "calm": "🧘",
                    "focused": "🎯",
                    "exciting": "🎉"
                }.get(scene['mood'], "🎬")

                with st.expander(f"{mood_emoji} {scene['scene']}"):
                    st.write(f"**Description:** {scene['description']}")
                    st.write(f"**Mood:** {scene['mood']}")
                    st.write(f"**Rooms:** {', '.join(filter(None, scene['rooms']))}")

                    st.write("**Actions:**")
                    for action in scene['actions']:
                        if action.get('device'):
                            st.write(f"  - {action['device']}: {action['action']}")

    with tab4:
        st.subheader("Graph Statistics")

        stats = conn.query("""
            MATCH (r:Room) WITH count(r) AS rooms
            MATCH (d:Device) WITH rooms, count(d) AS devices
            MATCH (c:Capability) WITH rooms, devices, count(c) AS capabilities
            MATCH (s:Scene) WITH rooms, devices, capabilities, count(s) AS scenes
            MATCH ()-[rel]->()
            RETURN rooms, devices, capabilities, scenes, count(rel) AS relationships
        """)

        if stats:
            stat = stats[0]
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("🏠 Rooms", stat['rooms'])
            col2.metric("📱 Devices", stat['devices'])
            col3.metric("⚡ Capabilities", stat['capabilities'])
            col4.metric("🎬 Scenes", stat['scenes'])
            col5.metric("🔗 Relationships", stat['relationships'])

        # Node distribution
        st.subheader("Node Distribution")
        labels = conn.query("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY count DESC
        """)

        if labels:
            import pandas as pd
            df = pd.DataFrame(labels)
            st.bar_chart(df.set_index('label'))


# =========================================
# PAGE: RETRIEVAL LAB
# =========================================

def render_retrieval_lab():
    """Render the retrieval strategy testing lab."""
    st.header("🧪 Retrieval Lab")

    st.markdown("""
    Test different GraphRAG retrieval strategies and see what context is retrieved.
    """)

    retriever = get_retriever()
    if not retriever:
        st.error("Retriever not available")
        return

    # Strategy selection
    strategy = st.selectbox(
        "Select Retrieval Strategy",
        ["Room Context", "Capability Search", "Scene Lookup", "Keyword Search", "Multi-Room"]
    )

    st.divider()

    if strategy == "Room Context":
        st.subheader("🏠 Room Context Retrieval")
        room_name = st.text_input("Room name:", "living room")

        if st.button("Retrieve", key="room"):
            with st.spinner("Querying graph..."):
                result = retriever.get_room_context(room_name)
                display_retrieval_result(result)

    elif strategy == "Capability Search":
        st.subheader("⚡ Capability Search")
        capabilities = st.multiselect(
            "Select capabilities:",
            ["power", "dim", "color", "volume", "play_music", "temperature", "announce"],
            default=["dim"]
        )

        if st.button("Retrieve", key="cap"):
            with st.spinner("Querying graph..."):
                result = retriever.get_devices_by_capability(capabilities)
                display_retrieval_result(result)

    elif strategy == "Scene Lookup":
        st.subheader("🎬 Scene Lookup")
        scene_name = st.text_input("Scene name:", "movie")

        if st.button("Retrieve", key="scene"):
            with st.spinner("Querying graph..."):
                result = retriever.get_scene_context(scene_name)
                display_retrieval_result(result)

    elif strategy == "Keyword Search":
        st.subheader("🔎 Keyword Search")
        keywords = st.text_input("Keywords (comma-separated):", "cozy, relax")
        keyword_list = [k.strip() for k in keywords.split(",")]

        if st.button("Retrieve", key="keyword"):
            with st.spinner("Querying graph..."):
                result = retriever.search_by_keywords(keyword_list)
                display_retrieval_result(result)

    elif strategy == "Multi-Room":
        st.subheader("🏘️ Multi-Room Context")
        rooms = st.multiselect(
            "Select rooms:",
            ["living", "kitchen", "bedroom", "office", "bathroom"],
            default=["living", "kitchen"]
        )

        if st.button("Retrieve", key="multi"):
            with st.spinner("Querying graph..."):
                result = retriever.get_multi_room_context(rooms)
                display_retrieval_result(result)


def display_retrieval_result(result):
    """Display a retrieval result with tabs."""
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Strategy", result.strategy.value)
    with col2:
        st.metric("Context Length", f"{len(result.formatted_context)} chars")

    tab1, tab2, tab3 = st.tabs(["📝 Formatted Context", "📊 Raw Results", "ℹ️ Metadata"])

    with tab1:
        st.markdown(result.formatted_context)

    with tab2:
        st.json(result.raw_results)

    with tab3:
        st.json(result.metadata)
        st.json(result.query_params)


# =========================================
# PAGE: SYSTEM STATUS
# =========================================

def render_system_status():
    """Render the system status dashboard."""
    st.header("📊 System Status")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔑 LLM Configuration")

        from src.llm import get_llm_info
        llm_info = get_llm_info()
        st.info(f"Provider: **{llm_info['provider'].upper()}**")
        st.info(f"Model: `{llm_info['model']}`")

        if llm_info["status"] == "ok":
            st.success(f"✓ {llm_info['detail']}")
        else:
            st.error(f"✗ {llm_info['detail']}")
            st.code("# Set LLM_PROVIDER and credentials in .env", language="bash")

        st.divider()

        # Neo4j
        st.subheader("🗄️ Neo4j Connection")
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        st.info(f"URI: `{neo4j_uri}`")

        conn = get_connection()
        if conn:
            try:
                health = conn.health_check()
                if health.get("status") == "healthy":
                    st.success("✓ Connected")
                    st.write(f"**Database:** {health.get('database', 'N/A')}")
                    st.write(f"**Version:** {health.get('version', 'N/A')}")
                    st.write(f"**Edition:** {health.get('edition', 'N/A')}")
                else:
                    st.error(f"✗ Unhealthy: {health.get('error', 'Unknown')}")
            except Exception as e:
                st.error(f"✗ Error: {e}")
        else:
            st.error("✗ Not connected")

    with col2:
        st.subheader("🤖 Agent Status")

        agent = get_agent()
        if agent:
            st.success("✓ Agent initialized")

            # Test agent
            if st.button("🧪 Test Agent"):
                with st.spinner("Testing..."):
                    try:
                        response = agent.run("Turn on the living room lights")
                        st.success("✓ Agent working!")
                        st.write("**Test response:**")
                        st.write(response)
                    except Exception as e:
                        st.error(f"✗ Agent error: {e}")
        else:
            st.error("✗ Agent not initialized")

        st.divider()

        st.subheader("📚 Graph Data")
        retriever = get_retriever()
        if retriever:
            try:
                stats = retriever.get_graph_stats()
                if stats:
                    st.write(f"**Rooms:** {stats.get('rooms', 0)}")
                    st.write(f"**Devices:** {stats.get('devices', 0)}")
                    st.write(f"**Capabilities:** {stats.get('capabilities', 0)}")
                    st.write(f"**Scenes:** {stats.get('scenes', 0)}")

                    if stats.get('devices', 0) == 0:
                        st.warning("⚠️ No data in graph. Load seed data!")
                        st.code("# Run in Neo4j Browser:\n# Copy data/seed_graph.cypher")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # Setup instructions
    st.subheader("📋 Setup Instructions")

    with st.expander("1. Start Neo4j"):
        st.code("""
docker run --name neo4j-smarthome \\
  -p 7474:7474 -p 7687:7687 \\
  -e NEO4J_AUTH=neo4j/password123 \\
  -d neo4j:latest
        """, language="bash")

    with st.expander("2. Configure .env"):
        st.markdown("Choose your LLM provider:")

        st.markdown("**Option A: OpenAI (cloud)**")
        st.code("""LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini""", language="bash")

        st.markdown("**Option B: Qwen/DashScope (cloud)**")
        st.code("""LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=sk-your-key-here
QWEN_MODEL=qwen-turbo""", language="bash")

        st.markdown("**Option C: Ollama (local, no API key)**")
        st.code("""LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434""", language="bash")

        st.markdown("**Neo4j (required for all providers):**")
        st.code("""NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123""", language="bash")

    with st.expander("3. Load Seed Data"):
        st.markdown("""
        1. Open Neo4j Browser: http://localhost:7474
        2. Copy contents of `data/seed_graph.cypher`
        3. Paste and run in the query editor
        """)


# =========================================
# MAIN APP
# =========================================

def main():
    """Main application entry point."""
    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "💬 Chat":
        render_chat_page()
    elif page == "🔍 Graph Explorer":
        render_graph_explorer()
    elif page == "🧪 Retrieval Lab":
        render_retrieval_lab()
    elif page == "📊 System Status":
        render_system_status()


if __name__ == "__main__":
    main()
