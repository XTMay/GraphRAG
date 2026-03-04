# Smart Home Graph Agent

A teaching demo for **GraphRAG** with **LangChain** and **LangGraph**.

This project demonstrates how to build an AI agent that:
1. Understands vague natural language instructions
2. Retrieves relevant context from a Knowledge Graph (Neo4j)
3. Reasons about available devices and capabilities
4. Generates structured action plans

## 🎯 Example

**User:** "Make the living room cozy for movie night"

**Agent:**
1. Queries knowledge graph for living room devices
2. Finds "Movie Night" scene as reference
3. Generates action plan:
   - Ceiling Light: dim to 20%, warm color
   - Floor Lamp: dim to 30%
   - Window Blinds: close
   - Smart TV: power on

---

## 📁 Project Structure

```
smart-home-graph-agent/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── api_server.py                # FastAPI REST API entry point
├── app.py                       # CLI entry point
├── streamlit_app.py             # Streamlit UI entry point
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Multi-service orchestration
├── .dockerignore                # Docker build exclusions
│
├── data/
│   └── seed_graph.cypher        # Neo4j seed data
│
├── src/
│   ├── __init__.py
│   ├── api/                     # FastAPI web service
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic request/response models
│   │   ├── server.py            # FastAPI app and endpoints
│   │   └── middleware.py        # Logging, rate limiting
│   ├── agent/                   # Agent implementations
│   │   ├── __init__.py
│   │   ├── state.py             # AgentState definition
│   │   ├── workflow.py          # Explicit workflow agent
│   │   ├── nodes.py             # Workflow node functions
│   │   ├── prompts.py           # Prompt templates
│   │   ├── tools.py             # LangChain Tool definitions
│   │   ├── memory.py            # Conversation memory
│   │   └── tool_agent.py        # ReAct tool-calling agent
│   ├── graph/                   # Neo4j knowledge graph
│   │   ├── __init__.py
│   │   ├── connection.py        # Neo4j connection
│   │   ├── queries.py           # Cypher templates
│   │   └── retriever.py         # GraphRAG retriever
│   ├── llm/                     # LLM factory
│   │   ├── __init__.py
│   │   └── factory.py           # Multi-LLM factory (OpenAI/Qwen/Ollama)
│   └── utils/                   # Utilities
│       ├── __init__.py
│       └── output_parser.py     # JSON/output parsing
│
├── docs/                        # Teaching documentation (Chinese)
│   ├── 00_课程概述.md ~ 06_系统架构图.md
│   ├── 07_FastAPI_Web服务.md    # FastAPI + REST API + SSE
│   ├── 08_Docker容器化部署.md   # Dockerfile + Docker Compose
│   └── 09_高级Agent模式.md      # Tool Use + Memory + Patterns
│
└── notebooks/                   # Interactive labs
    ├── 01_explore_neo4j.ipynb ~ 04_multi_llm.ipynb
    ├── 05_fastapi_web_service.ipynb      # API testing lab
    └── 06_advanced_agent_patterns.ipynb  # Advanced agent lab
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd smart-home-graph-agent
pip install -r requirements.txt
```

### 2. Start Neo4j

**Option A: Docker (Recommended)**

```bash
docker run \
  --name neo4j-smarthome \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -d neo4j:latest
```

**Option B: Neo4j Aura (Cloud - Free)**

1. Go to https://neo4j.com/cloud/aura/
2. Create a free instance
3. Note the connection URI and password

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Neo4j credentials and OpenAI key
```

### 4. Load Seed Data

1. Open Neo4j Browser: http://localhost:7474
2. Login with credentials (default: neo4j/password123)
3. Copy contents of `data/seed_graph.cypher`
4. Paste into query editor and run

### 5. Verify Setup

```bash
python -m src.graph.connection
```

Expected output:
```
Testing Neo4j Connection...
----------------------------------------
Health Check: healthy
  Database: neo4j
  Nodes: ~30
  Relationships: ~50
```

### 6. Run the Demo

**Option A: Streamlit UI (Recommended for teaching)**

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser.

**Option B: REST API**

```bash
python api_server.py
```

Open http://localhost:8000/docs for Swagger UI.

**Option C: Command Line Interface**

```bash
python app.py              # Interactive mode
python app.py --debug      # Debug mode with trace
```

**Option D: Docker Deployment (all services)**

```bash
docker compose up
```

This starts Neo4j + API + Streamlit together.

**Option E: Jupyter Notebooks**

```bash
jupyter notebook notebooks/
```

Start with `01_explore_neo4j.ipynb`.

---

## 🖥️ Demo Interfaces

### Streamlit UI (Recommended)

```bash
streamlit run streamlit_app.py
```

**Features:**
| Page | Description |
|------|-------------|
| 💬 Chat | Interactive chat with the smart home agent |
| 🔍 Graph Explorer | Browse rooms, devices, scenes in Neo4j |
| 🧪 Retrieval Lab | Test different GraphRAG strategies |
| 📊 System Status | Check Neo4j/OpenAI connections |

**Screenshots:**
- Chat interface with reasoning trace
- Graph visualization by room
- Retrieval strategy comparison

### REST API

```bash
python api_server.py                    # Start API server
python api_server.py --port 8080        # Custom port
python api_server.py --reload           # Dev mode with auto-reload
```

Access Swagger UI at http://localhost:8000/docs

### Command Line Interface

```bash
python app.py                    # Interactive mode
python app.py "your request"     # Single request
python app.py --debug "request"  # With reasoning trace
python app.py --status           # System check
```

---

## 📚 Learning Path

| Notebook | Topic | Duration |
|----------|-------|----------|
| 01_explore_neo4j | Graph basics, Cypher queries | 30 min |
| 02_graphrag_basics | Retrieval strategies | 30 min |
| 03_full_agent | LangGraph workflow (Phase 3-4) | 45 min |
| 04_multi_llm | Multi-LLM backends & Factory Pattern | 30 min |
| 05_fastapi_web_service | REST API, SSE streaming, middleware | 45 min |
| 06_advanced_agent_patterns | Tool Use, memory, agent comparison | 45 min |

---

## 🔧 LLM Provider Configuration

This project supports **three LLM backends**. Set `LLM_PROVIDER` in `.env` to switch:

| Provider | `LLM_PROVIDER` | Required Env Vars | Install |
|----------|----------------|-------------------|---------|
| **OpenAI** (default) | `openai` | `OPENAI_API_KEY`, `OPENAI_MODEL` | `pip install langchain-openai` |
| **Qwen/通义千问** | `qwen` | `DASHSCOPE_API_KEY`, `QWEN_MODEL` | `pip install dashscope` |
| **Ollama** (local) | `ollama` | `OLLAMA_MODEL`, `OLLAMA_BASE_URL` | `pip install langchain-ollama` + [Ollama](https://ollama.ai) |

### Example `.env` Configurations

**OpenAI (cloud, default):**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Qwen/DashScope (cloud):**
```bash
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=sk-your-key-here
QWEN_MODEL=qwen-turbo
```

**Ollama (local, no API key):**
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

> **Backward compatible:** If `LLM_PROVIDER` is not set, it defaults to `openai`.

### Architecture: Factory Pattern

```
.env (LLM_PROVIDER=openai/qwen/ollama)
         |
         v
    get_llm()  ← Factory Function
    /    |    \
   v     v     v
ChatOpenAI  ChatTongyi  ChatOllama
   \     |     /
    v    v    v
  BaseChatModel.invoke()  ← Unified interface
```

All agent nodes call `get_llm()` — switching providers requires **zero code changes**.

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│                  User Interfaces                  │
│  CLI (app.py)  │  Streamlit  │  REST API (FastAPI)│
└───────┬────────┴─────┬───────┴──────┬─────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
          ┌────────────────────────┐
          │     Agent Layer        │
          │  SmartHomeAgent        │  ← Explicit Workflow
          │  ToolCallingAgent      │  ← ReAct + Tool Use
          │  ConversationMemory    │  ← Multi-turn Support
          └───────────┬────────────┘
                      │
          ┌───────────▼────────────┐
          │    GraphRAG Retrieval  │
          │  Room / Scene / Cap /  │
          │  Keyword strategies    │
          └───────────┬────────────┘
                      │
          ┌───────────▼────────────┐
          │   Neo4j Knowledge      │
          │   Graph Database       │
          └────────────────────────┘
```

---

## 🗃️ Knowledge Graph Schema

### Node Types

| Label | Description | Key Properties |
|-------|-------------|----------------|
| `Room` | Physical spaces | name, floor, type |
| `Device` | Smart devices | device_id, name, device_type, status |
| `Capability` | Device actions | name, parameters, description |
| `Scene` | Preset configurations | name, mood, typical_actions |

### Relationships

| Type | From | To | Description |
|------|------|-----|-------------|
| `CONTAINS` | Room | Device | Room contains device |
| `HAS_CAPABILITY` | Device | Capability | Device can do action |
| `APPLIES_TO` | Scene | Room | Scene for room |
| `USES_DEVICE` | Scene | Device | Scene controls device |
| `ADJACENT_TO` | Room | Room | Spatial relationship |

---

## 🔍 Retrieval Strategies

| Strategy | Use When | Example Query |
|----------|----------|---------------|
| `ROOM_CONTEXT` | Specific room mentioned | "Turn on living room lights" |
| `CAPABILITY_SEARCH` | Action mentioned | "Dim all lights" |
| `SCENE_LOOKUP` | Mood/scene mentioned | "Movie night mode" |
| `KEYWORD_SEARCH` | Vague request | "Make it comfortable" |
| `MULTI_ROOM` | Multiple rooms | "Prepare the house" |

---

## 🛠️ Implementation Status

- [x] **Phase 1**: Neo4j setup + seed data
- [x] **Phase 2**: GraphRAG retriever
- [x] **Phase 3**: LangChain LLM integration
- [x] **Phase 4**: LangGraph agent workflow
- [x] **Phase 5**: CLI demo interface
- [x] **Phase 6**: FastAPI REST API + SSE streaming
- [x] **Phase 7**: Docker containerization + Compose orchestration
- [x] **Phase 8**: Advanced Agent patterns (Tool Use + Memory + ReAct)

---

## 📖 Teaching Notes

### Key Concepts Demonstrated

1. **Knowledge Graphs** - Structured relationships vs flat documents
2. **GraphRAG** - Traversal-based retrieval
3. **Multi-step Agents** - State machines for reasoning
4. **Tool Use** - LLM + external systems

### Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "RAG = vector search" | GraphRAG uses relationship traversal |
| "Graphs need big data" | Small graphs (50 nodes) are valuable |
| "LLM does everything" | LLM reasons; graph stores knowledge |

---

## 🤝 Contributing

This is a teaching project. Feel free to:
- Add more scenes/devices to seed data
- Create additional notebooks
- Improve documentation

---

## 📄 License

MIT License - Use freely for learning and teaching.
