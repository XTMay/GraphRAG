# GraphRAG Architecture Diagrams

This folder contains architecture and workflow diagrams for teaching GraphRAG.

## Files

| File | Description | Format |
|------|-------------|--------|
| `architecture.md` | ASCII art diagrams (works everywhere) | Markdown/Text |
| `mermaid_diagrams.md` | Mermaid diagrams (for GitHub/VS Code) | Markdown + Mermaid |
| `generate_diagrams.py` | Python script to generate PNG images | Python |

---

## Quick View: Main Architecture

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          GraphRAG PIPELINE                                     ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   INDEXING (Offline)                    QUERY (Online)                        ║
║   ══════════════════                    ═══════════════                       ║
║                                                                               ║
║   ┌──────────┐                          ┌──────────┐                          ║
║   │Documents │                          │  Query   │                          ║
║   └────┬─────┘                          └────┬─────┘                          ║
║        │                                     │                                ║
║        ▼                                     ▼                                ║
║   ┌──────────┐                          ┌──────────┐                          ║
║   │   LLM    │                          │  Entity  │                          ║
║   │Extract   │                          │  Match   │                          ║
║   └────┬─────┘                          └────┬─────┘                          ║
║        │                                     │                                ║
║        ▼                                     ▼                                ║
║   ┌──────────┐                          ┌──────────┐                          ║
║   │Knowledge │─────────────────────────►│  K-Hop   │                          ║
║   │  Graph   │                          │ Retrieve │                          ║
║   └──────────┘                          └────┬─────┘                          ║
║                                              │                                ║
║                                              ▼                                ║
║                                         ┌──────────┐                          ║
║                                         │  LLM     │                          ║
║                                         │ Generate │                          ║
║                                         └────┬─────┘                          ║
║                                              │                                ║
║                                              ▼                                ║
║                                         ┌──────────┐                          ║
║                                         │  Answer  │                          ║
║                                         └──────────┘                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## How to Generate PNG Diagrams

```bash
# Install matplotlib
pip install matplotlib

# Generate diagrams
python generate_diagrams.py

# Output:
#   - graphrag_pipeline.png
#   - vector_vs_graph_rag.png
#   - khop_expansion.png
#   - workflow_steps.png
```

---

## How to View Mermaid Diagrams

### Option 1: GitHub
Just view `mermaid_diagrams.md` on GitHub - it renders automatically.

### Option 2: VS Code
1. Install extension: "Markdown Preview Mermaid Support"
2. Open `mermaid_diagrams.md`
3. Press `Cmd+Shift+V` to preview

### Option 3: Online
1. Go to https://mermaid.live
2. Copy-paste the mermaid code blocks
3. See live preview + export options

---

## Diagram Overview

### 1. Pipeline Architecture
Shows the two-phase architecture:
- **Indexing**: Documents → LLM Extraction → Knowledge Graph
- **Query**: Query → Entity Match → K-Hop → LLM Generate → Answer

### 2. Vector RAG vs Graph RAG
Side-by-side comparison showing:
- Vector RAG: Independent chunks, no connections
- Graph RAG: Connected entities, relationship traversal

### 3. K-Hop Expansion
Visualizes how subgraph retrieval works:
- K=0: Just the seed entity
- K=1: Seed + direct neighbors
- K=2: Seed + neighbors + neighbors-of-neighbors

### 4. Workflow Steps
5-step process:
1. User Query → 2. Entity Match → 3. K-Hop Expand → 4. Build Context → 5. LLM Answer

### 5. Component Interaction
How the Python modules work together:
- extractor.py ↔ LLM
- builder.py ↔ NetworkX
- retriever.py ↔ Graph
- generator.py ↔ LLM

---

## For Teaching

Use these diagrams to explain:

1. **"What is GraphRAG?"**
   → Show Pipeline Architecture diagram

2. **"How is it different from Vector RAG?"**
   → Show comparison diagram

3. **"How does retrieval work?"**
   → Show K-Hop Expansion diagram

4. **"What happens step by step?"**
   → Show Workflow Steps diagram
