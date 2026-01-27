# GraphRAG Teaching Demo

A hands-on educational project for understanding **Graph-based Retrieval-Augmented Generation (GraphRAG)**.

---

## What is GraphRAG?

GraphRAG is an advanced retrieval technique that enhances traditional RAG by:
1. **Extracting entities and relationships** from documents
2. **Building a knowledge graph** to represent structured knowledge
3. **Retrieving relevant subgraphs** instead of just text chunks
4. **Reasoning over graph structure** to answer complex questions

```
Traditional RAG:        Document → Chunks → Vector Search → LLM → Answer
GraphRAG:              Document → Entities/Relations → Graph → Subgraph Retrieval → LLM → Answer
```

---

## Vector RAG vs GraphRAG: A Comparison

| Aspect | Vector RAG | GraphRAG |
|--------|-----------|----------|
| **Knowledge Representation** | Text chunks as vectors | Structured graph (entities + relations) |
| **Retrieval Method** | Semantic similarity search | Graph traversal (k-hop neighbors) |
| **Multi-hop Reasoning** | Difficult (needs multiple chunks) | Natural (follow edges in graph) |
| **Explainability** | Low (why this chunk?) | High (visible reasoning path) |
| **Global Understanding** | Poor | Good (community detection) |
| **Setup Complexity** | Simple | More complex |
| **Best For** | Factual Q&A, similarity search | Relationship queries, complex reasoning |

### When to Use GraphRAG?

✅ **Use GraphRAG when:**
- Questions involve relationships ("How is A connected to B?")
- Multi-hop reasoning is needed ("Who works at the company that acquired X?")
- You need explainable reasoning paths
- Documents describe interconnected entities

❌ **Stick with Vector RAG when:**
- Simple factual lookups
- Documents are independent (no entity overlap)
- Speed is critical
- Limited computational resources

---

## Learning Outcomes

After completing this demo, you will be able to:

1. **Explain** the difference between Vector RAG and GraphRAG
2. **Extract** entities and relationships from text using an LLM
3. **Build** a knowledge graph using NetworkX
4. **Implement** k-hop subgraph retrieval
5. **Generate** answers by reasoning over graph context
6. **Visualize** and debug knowledge graphs

---

## Project Structure

```
teaching_demo/
│
├── README.md                    # This file
├── requirements.txt             # Python dependencies
│
├── 01_concepts/                 # Conceptual explanations
│   └── graphrag_explained.md    # Detailed theory
│
├── 02_data/                     # Sample documents
│   └── sample_corpus.json       # Toy dataset for teaching
│
├── 03_extraction/               # Entity & Relation Extraction
│   ├── prompts.py               # LLM prompts for extraction
│   └── extractor.py             # Extraction pipeline
│
├── 04_graph/                    # Knowledge Graph Construction
│   ├── builder.py               # Build graph from extractions
│   └── visualizer.py            # Graph visualization
│
├── 05_retrieval/                # Graph-based Retrieval
│   └── retriever.py             # k-hop subgraph retrieval
│
├── 06_generation/               # Answer Generation
│   ├── prompts.py               # Reasoning prompts
│   └── generator.py             # LLM answer generation
│
├── 07_pipeline/                 # Complete Pipeline
│   └── graphrag_pipeline.py     # End-to-end system
│
└── run_demo.py                  # Interactive demo script
```

---

## Quick Start

### 1. Install Dependencies

```bash
cd teaching_demo
pip install -r requirements.txt
```

### 2. Start Ollama (for local LLM)

```bash
# Install Ollama: https://ollama.ai
ollama serve

# Pull a model (in another terminal)
ollama pull qwen2.5:7b
```

### 3. Run the Demo

```bash
python run_demo.py
```

---

## Step-by-Step Walkthrough

### Step 1: Load Documents

```python
# Our sample corpus contains tech company information
documents = load_corpus("02_data/sample_corpus.json")
```

### Step 2: Extract Entities & Relations

```python
# Use LLM to extract structured knowledge
extractions = extract_knowledge(documents, llm)
# Output: {"entities": [...], "relations": [...]}
```

### Step 3: Build Knowledge Graph

```python
# Construct graph using NetworkX
graph = build_graph(extractions)
# Nodes = Entities, Edges = Relations
```

### Step 4: Retrieve Relevant Subgraph

```python
# Given a query, find relevant entities and expand k-hops
query = "Who founded the company that� �developed GPT?"
subgraph = retrieve_subgraph(graph, query, k_hops=2)
```

### Step 5: Generate Answer

```python
# Convert subgraph to text and prompt LLM
context = subgraph_to_text(subgraph)
answer = generate_answer(query, context, llm)
```

---

## Example Queries

Try these queries that **require multi-hop reasoning**:

1. **"What products were created by OpenAI?"**
   - Requires: OpenAI → [created] → GPT-4, ChatGPT, DALL-E

2. **"Who are the founders of the company that developed Transformer?"**
   - Requires: Transformer → [developed_by] → Google → [founders] → Larry Page, Sergey Brin

3. **"What technologies use the Transformer architecture?"**
   - Requires: Transformer → [used_by] → GPT, BERT, T5, etc.

---

## Discussion Questions for Class

1. **Why can't Vector RAG easily answer multi-hop questions?**
   - Hint: Think about how chunks are retrieved independently

2. **What are the limitations of LLM-based entity extraction?**
   - Hint: Consider consistency, hallucination, schema adherence

3. **How would you scale this to millions of documents?**
   - Hint: Graph databases, distributed processing, incremental updates

4. **How could you combine Vector RAG and GraphRAG?**
   - Hint: Hybrid retrieval, use vectors to find starting entities

5. **What if the LLM extracts wrong relationships?**
   - Hint: Validation, confidence scores, human-in-the-loop

---

## Student Exercises

### Exercise 1: Add New Entity Types
Modify `03_extraction/prompts.py` to extract a new entity type (e.g., "PRODUCT", "DATE").

### Exercise 2: Implement 3-hop Retrieval
Extend `05_retrieval/retriever.py` to support configurable k-hop depth.

### Exercise 3: Visualize Reasoning Path
Create a function that highlights the reasoning path from query to answer.

### Exercise 4: Add Your Own Corpus
Create a new corpus about a topic you're interested in and test the pipeline.

### Exercise 5: Compare with Vector RAG
Implement a simple vector RAG and compare answers on the same queries.

---

## Common Mistakes to Avoid

| Mistake | Why It's Wrong | How to Fix |
|---------|---------------|------------|
| Extracting too many entities | Noise in graph, slow retrieval | Be selective, filter by importance |
| Ignoring entity normalization | "OpenAI" vs "openai" vs "Open AI" | Normalize names before graph insertion |
| Using k-hop too large | Retrieves irrelevant nodes | Start with k=1 or k=2 |
| Not handling extraction failures | Pipeline crashes | Add try-except, validate JSON |
| Forgetting edge direction | Wrong reasoning | Be consistent with (source, relation, target) |

---

## Further Reading

- [Microsoft GraphRAG Paper](https://arxiv.org/abs/2404.16130) - "From Local to Global"
- [Knowledge Graphs Survey](https://arxiv.org/abs/2003.02320)
- [NetworkX Documentation](https://networkx.org/documentation/)

---

## License

MIT License - Free for educational use.
