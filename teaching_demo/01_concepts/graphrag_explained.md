# GraphRAG: A Conceptual Deep Dive

## 1. The Problem with Traditional RAG

Traditional RAG (Retrieval-Augmented Generation) works like this:

```
Document → Split into chunks → Embed chunks → Store in vector DB
Query → Embed query → Find similar chunks → Feed to LLM → Answer
```

**This works well for:**
- "What is the capital of France?" → Find chunk mentioning Paris
- "Summarize the main points of section 3" → Retrieve section 3

**This fails for:**
- "Who works at the company that acquired Twitter?"
  - Needs: Query → Elon Musk → Tesla/SpaceX/X Corp → Twitter acquisition → Answer
  - Vector search might find chunks about Twitter OR Elon Musk, but not connect them

### The Core Issue: Lost Structure

When we chunk documents, we **lose the relationships** between entities:

```
Original: "Sam Altman is CEO of OpenAI. OpenAI created ChatGPT."

Chunk 1: "Sam Altman is CEO of OpenAI."
Chunk 2: "OpenAI created ChatGPT."

Query: "Who leads the company that made ChatGPT?"
Vector search might return Chunk 2, but doesn't connect to Sam Altman!
```

---

## 2. GraphRAG: The Key Insight

**Key Insight**: Represent knowledge as a **graph**, not just text chunks.

```
Instead of: [chunk1] [chunk2] [chunk3] ...

Build:     (Sam Altman) --[CEO_OF]--> (OpenAI) --[CREATED]--> (ChatGPT)
```

Now we can **traverse relationships** to answer complex queries:

```
Query: "Who leads the company that made ChatGPT?"

Step 1: Find "ChatGPT" in graph
Step 2: Follow edge backwards: ChatGPT <--[CREATED]-- OpenAI
Step 3: Follow another edge: OpenAI <--[CEO_OF]-- Sam Altman
Step 4: Answer: "Sam Altman"
```

---

## 3. The GraphRAG Pipeline

### Stage 1: Knowledge Extraction

Use an LLM to extract **entities** and **relationships** from text:

```
Input Text: "Google, founded by Larry Page and Sergey Brin,
            developed the Transformer architecture in 2017."

Extracted:
  Entities:
    - (Google, ORGANIZATION)
    - (Larry Page, PERSON)
    - (Sergey Brin, PERSON)
    - (Transformer, TECHNOLOGY)
    - (2017, DATE)

  Relations:
    - (Larry Page, FOUNDED, Google)
    - (Sergey Brin, FOUNDED, Google)
    - (Google, DEVELOPED, Transformer)
    - (Transformer, CREATED_IN, 2017)
```

### Stage 2: Graph Construction

Build a graph where:
- **Nodes** = Entities (with type and description)
- **Edges** = Relationships (with type and description)

```
      ┌──────────────┐
      │  Larry Page  │
      │   (PERSON)   │
      └──────┬───────┘
             │ FOUNDED
             ▼
      ┌──────────────┐       DEVELOPED      ┌─────────────┐
      │    Google    │─────────────────────►│ Transformer │
      │(ORGANIZATION)│                      │ (TECHNOLOGY)│
      └──────▲───────┘                      └─────────────┘
             │ FOUNDED
      ┌──────┴───────┐
      │ Sergey Brin  │
      │   (PERSON)   │
      └──────────────┘
```

### Stage 3: Subgraph Retrieval

Given a query, find relevant nodes and expand to neighbors:

```
Query: "Who founded Google?"

Step 1: Entity Recognition
        → Identify "Google" in query

Step 2: Find in Graph
        → Locate node (Google, ORGANIZATION)

Step 3: K-hop Expansion (k=1)
        → Get all nodes within 1 edge of Google
        → Returns: Larry Page, Sergey Brin, Transformer

Step 4: Extract Subgraph
        → Nodes: Google, Larry Page, Sergey Brin
        → Edges: (Larry Page, FOUNDED, Google),
                 (Sergey Brin, FOUNDED, Google)
```

### Stage 4: Context Generation

Convert subgraph to natural language for LLM:

```
Subgraph Context:
- Entity: Google (type: ORGANIZATION)
- Entity: Larry Page (type: PERSON)
- Entity: Sergey Brin (type: PERSON)
- Relation: Larry Page FOUNDED Google
- Relation: Sergey Brin FOUNDED Google
```

### Stage 5: Answer Generation

Prompt LLM with query + graph context:

```
Context from Knowledge Graph:
- Larry Page FOUNDED Google
- Sergey Brin FOUNDED Google

Question: Who founded Google?

Answer: Google was founded by Larry Page and Sergey Brin.
```

---

## 4. Microsoft GraphRAG Enhancements

Microsoft's GraphRAG adds two key innovations:

### Community Detection

Group related entities into **communities** using algorithms like Leiden:

```
Community 1: [Google, Larry Page, Sergey Brin, Alphabet]  → "Google Founders"
Community 2: [OpenAI, Sam Altman, GPT-4, ChatGPT]         → "OpenAI Products"
Community 3: [Meta, Mark Zuckerberg, Llama, Facebook]     → "Meta AI"
```

### Hierarchical Summarization

Generate summaries at different levels:

```
Level 0 (Entire Graph): "This corpus covers major AI companies and their products..."
Level 1 (Communities):  "Google community focuses on search and AI research..."
Level 2 (Sub-communities): "Transformer architecture developed by Google..."
```

### Two Search Modes

**Global Search**: For questions about the entire corpus
- Uses community summaries
- Map-reduce over all communities
- Good for: "What are the main themes in these documents?"

**Local Search**: For specific entity questions
- Uses k-hop subgraph retrieval
- Good for: "What did OpenAI create?"

---

## 5. Trade-offs and Limitations

### Advantages of GraphRAG

1. **Multi-hop Reasoning**: Natural path following
2. **Explainability**: Can show reasoning path
3. **Structure Preservation**: Relationships are explicit
4. **Global Understanding**: Community summaries

### Disadvantages

1. **Extraction Quality**: LLM may hallucinate entities/relations
2. **Computational Cost**: More expensive than vector search
3. **Schema Rigidity**: Need to define entity/relation types
4. **Update Complexity**: Adding new docs requires re-extraction

### When Each Approach Wins

| Query Type | Vector RAG | GraphRAG |
|------------|-----------|----------|
| "What is X?" | ✅ | ✅ |
| "Summarize document Y" | ✅ | ⚠️ |
| "How is A related to B?" | ❌ | ✅ |
| "List all companies that..." | ❌ | ✅ |
| "What's the theme of these docs?" | ❌ | ✅ |

---

## 6. Implementation Choices

### Graph Storage Options

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **NetworkX** | Simple, in-memory, Python-native | Not scalable | Teaching, prototypes |
| **Neo4j** | Powerful queries, visualization | Complex setup | Production |
| **NebulaGraph** | Distributed, scalable | Steep learning curve | Large scale |

### LLM Choices for Extraction

| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| GPT-4 | Excellent | Slow | High |
| Qwen2.5-14B | Very Good | Medium | Free (local) |
| Llama3-8B | Good | Fast | Free (local) |
| Mistral-7B | Good | Fast | Free (local) |

---

## 7. Summary

```
GraphRAG = Knowledge Extraction + Graph Storage + Graph Retrieval + LLM Generation

Key Steps:
1. Extract (entities, relations) from documents using LLM
2. Build knowledge graph (nodes = entities, edges = relations)
3. Retrieve relevant subgraph for query (k-hop expansion)
4. Generate answer using subgraph context

Key Benefit: Enables multi-hop reasoning that vector RAG cannot do

Key Challenge: Extraction quality determines overall system quality
```
