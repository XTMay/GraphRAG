# GraphRAG Architecture & Workflow Diagrams

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GraphRAG System Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        INDEXING PHASE (Offline)                      │   │
│  │                                                                      │   │
│  │   ┌──────────┐    ┌──────────────┐    ┌──────────────┐             │   │
│  │   │          │    │              │    │              │             │   │
│  │   │ Documents│───►│  LLM-based   │───►│  Knowledge   │             │   │
│  │   │  (Raw)   │    │  Extraction  │    │    Graph     │             │   │
│  │   │          │    │              │    │  (NetworkX)  │             │   │
│  │   └──────────┘    └──────────────┘    └──────────────┘             │   │
│  │        │                 │                   │                      │   │
│  │        ▼                 ▼                   ▼                      │   │
│  │   ┌──────────┐    ┌──────────────┐    ┌──────────────┐             │   │
│  │   │  Text    │    │  Entities &  │    │    Nodes     │             │   │
│  │   │  Chunks  │    │  Relations   │    │   & Edges    │             │   │
│  │   └──────────┘    └──────────────┘    └──────────────┘             │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         QUERY PHASE (Online)                         │   │
│  │                                                                      │   │
│  │   ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────┐ │   │
│  │   │          │    │              │    │              │    │      │ │   │
│  │   │  User    │───►│   Entity     │───►│   K-Hop      │───►│ Sub- │ │   │
│  │   │  Query   │    │   Matching   │    │  Retrieval   │    │graph │ │   │
│  │   │          │    │              │    │              │    │      │ │   │
│  │   └──────────┘    └──────────────┘    └──────────────┘    └──┬───┘ │   │
│  │                                                               │     │   │
│  │                                                               ▼     │   │
│  │   ┌──────────┐    ┌──────────────┐    ┌──────────────┐           │   │
│  │   │          │    │              │    │              │           │   │
│  │   │  Answer  │◄───│     LLM      │◄───│   Context    │           │   │
│  │   │          │    │  Generation  │    │    Text      │           │   │
│  │   │          │    │              │    │              │           │   │
│  │   └──────────┘    └──────────────┘    └──────────────┘           │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Pipeline Workflow

```
═══════════════════════════════════════════════════════════════════════════════
                              GRAPHRAG PIPELINE
═══════════════════════════════════════════════════════════════════════════════

PHASE 1: INDEXING (Build Knowledge Graph)
─────────────────────────────────────────

Step 1.1: Document Ingestion
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    doc1.txt ─────┐                                                          │
│                  │      ┌─────────────────┐      ┌─────────────────┐       │
│    doc2.txt ─────┼─────►│  Text Loader    │─────►│  Raw Text       │       │
│                  │      │  (UTF-8)        │      │  Collection     │       │
│    doc3.txt ─────┘      └─────────────────┘      └─────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1.2: Entity & Relationship Extraction (LLM Call #1)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐   │
│    │                 │      │                 │      │                 │   │
│    │   Raw Text      │─────►│   LLM + Prompt  │─────►│  Structured     │   │
│    │                 │      │   (Extraction)  │      │  JSON Output    │   │
│    │                 │      │                 │      │                 │   │
│    └─────────────────┘      └─────────────────┘      └─────────────────┘   │
│                                    │                         │              │
│                                    │                         ▼              │
│    Prompt Template:                │         {                              │
│    "Extract entities and           │           "entities": [                │
│     relationships from:            │             {"name": "OpenAI",         │
│     {text}"                        │              "type": "ORG"},           │
│                                    │             {"name": "GPT-4",          │
│                                    │              "type": "TECH"}           │
│                                    │           ],                           │
│                                    │           "relationships": [           │
│                                    │             {"source": "OpenAI",       │
│                                    │              "relation": "DEVELOPED",  │
│                                    │              "target": "GPT-4"}        │
│                                    │           ]                            │
│                                    │         }                              │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1.3: Knowledge Graph Construction
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    ┌─────────────────┐      ┌─────────────────────────────────────────┐    │
│    │  Structured     │      │           NetworkX Graph                 │    │
│    │  Extractions    │─────►│                                         │    │
│    │  (JSON)         │      │     (Sam Altman)                        │    │
│    └─────────────────┘      │          │                              │    │
│                             │          │ CEO_OF                       │    │
│                             │          ▼                              │    │
│    Processing:              │     ┌─────────┐     DEVELOPED           │    │
│    • Add nodes              │     │ OpenAI  │─────────────►(GPT-4)    │    │
│    • Add edges              │     └─────────┘                  │      │    │
│    • Store attributes       │          │                       │      │    │
│    • Deduplicate            │          │ DEVELOPED       BASED_ON     │    │
│                             │          ▼                       │      │    │
│                             │     (ChatGPT)◄───────────────────┘      │    │
│                             │                                         │    │
│                             └─────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


PHASE 2: QUERY (Answer Questions)
─────────────────────────────────

Step 2.1: Entity Matching
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    User Query                        Entity Matching                        │
│    ┌─────────────────┐              ┌─────────────────┐                    │
│    │                 │              │                 │                    │
│    │ "What did       │    ──────►   │  Find "OpenAI"  │                    │
│    │  OpenAI         │   String     │  in graph       │                    │
│    │  develop?"      │   Match or   │  nodes          │                    │
│    │                 │   LLM Match  │                 │                    │
│    └─────────────────┘              └────────┬────────┘                    │
│                                              │                              │
│                                              ▼                              │
│                                     Seed Entities: [openai]                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Step 2.2: K-Hop Subgraph Retrieval
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    Full Graph                           K=1 Expansion                       │
│    ──────────                           ──────────────                      │
│                                                                             │
│    (Hinton)──WORKS_AT──►(Google)        Seed: [openai]                     │
│                           │                    │                            │
│                       DEVELOPED                │ expand                     │
│                           │                    ▼                            │
│    (Sam)──CEO_OF──►[OpenAI]◄───────    [OpenAI]──►(GPT-4)                  │
│                       │    │                   │                            │
│                  DEVELOPED DEVELOPED           └──►(ChatGPT)               │
│                       │    │                   │                            │
│                       ▼    ▼                   └──►(Sam Altman)             │
│                   (GPT-4) (ChatGPT)                                        │
│                       │                                                     │
│                   BASED_ON                      K=2 Expansion               │
│                       │                         ──────────────              │
│                       ▼                                                     │
│                 (Transformer)◄──DEVELOPED──(Google)   Also includes:       │
│                                                       • Transformer         │
│                                                       (from GPT-4)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Step 2.3: Context Generation
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    Subgraph                              Text Context                       │
│    ────────                              ────────────                       │
│                                                                             │
│    [OpenAI]──►(GPT-4)         ═══════►   "Entities:                        │
│        │                                  - OpenAI (ORGANIZATION)          │
│        └──►(ChatGPT)                      - GPT-4 (TECHNOLOGY)             │
│        │                                  - ChatGPT (TECHNOLOGY)           │
│        └──►(Sam Altman)                   - Sam Altman (PERSON)            │
│                                                                             │
│                                           Relationships:                    │
│                                           - OpenAI DEVELOPED GPT-4         │
│                                           - OpenAI DEVELOPED ChatGPT       │
│                                           - Sam Altman CEO_OF OpenAI"      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Step 2.4: Answer Generation (LLM Call #2)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐       │
│    │                 │    │                 │    │                 │       │
│    │  Context Text   │───►│   LLM + Prompt  │───►│     Answer      │       │
│    │  + Question     │    │   (Generation)  │    │                 │       │
│    │                 │    │                 │    │                 │       │
│    └─────────────────┘    └─────────────────┘    └─────────────────┘       │
│                                                                             │
│    Prompt:                              Output:                             │
│    "Given this context:                 "Based on the knowledge graph,     │
│     {context}                            OpenAI developed two major        │
│                                          products:                         │
│     Answer: {question}"                  1. GPT-4 - a large language model │
│                                          2. ChatGPT - a conversational AI" │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
```

---

## 3. Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        COMPONENT INTERACTIONS                                 │
└──────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │            USER INTERFACE            │
                    │         (run_demo.py / API)         │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │         PIPELINE ORCHESTRATOR        │
                    │       (graphrag_pipeline.py)        │
                    └──────────────────┬──────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│      EXTRACTOR      │    │      RETRIEVER      │    │      GENERATOR      │
│   (extractor.py)    │    │   (retriever.py)    │    │   (generator.py)    │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • Parse documents   │    │ • Entity matching   │    │ • Format prompt     │
│ • Call LLM          │    │ • K-hop expansion   │    │ • Call LLM          │
│ • Parse JSON output │    │ • Subgraph extract  │    │ • Return answer     │
│ • Validate entities │    │ • Convert to text   │    │                     │
└──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
           │                           │                           │
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│    GRAPH BUILDER    │    │   KNOWLEDGE GRAPH   │    │     LLM CLIENT      │
│    (builder.py)     │◄───│    (NetworkX)       │───►│   (Ollama API)      │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • Create nodes      │    │ • Store entities    │    │ • HTTP requests     │
│ • Create edges      │    │ • Store relations   │    │ • Handle responses  │
│ • Add attributes    │    │ • Graph algorithms  │    │ • Error handling    │
│ • Deduplicate       │    │ • Traversal ops     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## 4. Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                        │
└──────────────────────────────────────────────────────────────────────────────┘

INDEXING FLOW:
══════════════

    ┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  .txt   │────►│   String    │────►│    JSON     │────►│  NetworkX   │
    │  .json  │     │   (text)    │     │ (entities,  │     │   Graph     │
    │  .pdf   │     │             │     │  relations) │     │  Object     │
    └─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       Files           Raw Text          Extractions          Graph DB


QUERY FLOW:
═══════════

    ┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  User   │────►│   Seed      │────►│  Subgraph   │────►│   Text      │
    │  Query  │     │  Entities   │     │  (nodes +   │     │  Context    │
    │(string) │     │   (list)    │     │   edges)    │     │  (string)   │
    └─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
    ┌─────────┐     ┌─────────────┐                                │
    │  Final  │◄────│    LLM      │◄───────────────────────────────┘
    │  Answer │     │   Output    │
    │(string) │     │  (string)   │
    └─────────┘     └─────────────┘
```

---

## 5. Comparison: Vector RAG vs Graph RAG

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      VECTOR RAG vs GRAPH RAG                                  │
└──────────────────────────────────────────────────────────────────────────────┘

VECTOR RAG ARCHITECTURE:
════════════════════════

    Documents          Chunks            Vectors           Query
    ─────────          ──────            ───────           ─────
    ┌───────┐         ┌──────┐         ┌───────┐
    │ Doc 1 │────────►│Chunk1│────────►│[0.1,..]│
    │       │         │Chunk2│────────►│[0.3,..]│         User Query
    └───────┘         │Chunk3│────────►│[0.2,..]│              │
                      └──────┘         └───────┘              │
                                            │                 ▼
                                            │         ┌──────────────┐
                                            └────────►│ Similarity   │
                                                      │   Search     │
                                                      └──────┬───────┘
                                                             │
                                                    Top-K Chunks
                                                             │
                                                             ▼
                                                      ┌────────────┐
                                                      │    LLM     │───► Answer
                                                      └────────────┘

    LIMITATION: Each chunk is INDEPENDENT. No connections between chunks!


GRAPH RAG ARCHITECTURE:
═══════════════════════

    Documents         Extraction        Graph              Query
    ─────────         ──────────        ─────              ─────
    ┌───────┐         ┌────────┐       ┌───────────────────────────┐
    │ Doc 1 │────────►│Entities│       │                           │
    │       │         │Relations│─────►│  (A)───[r1]───►(B)        │
    └───────┘         └────────┘       │   │              │        │
                                       │ [r2]          [r3]        │
                                       │   ▼              ▼        │
                                       │  (C)◄──[r4]───(D)        │
                                       │                           │
                                       └───────────────────────────┘
                                                  │
                                                  │ Graph
                                            User Query  Traversal
                                                  │         │
                                                  ▼         ▼
                                           ┌──────────────────┐
                                           │   K-hop          │
                                           │   Retrieval      │
                                           └────────┬─────────┘
                                                    │
                                              Subgraph + Relations
                                                    │
                                                    ▼
                                             ┌────────────┐
                                             │    LLM     │───► Answer
                                             └────────────┘

    ADVANTAGE: Follows RELATIONSHIPS to find connected information!


MULTI-HOP QUESTION EXAMPLE:
═══════════════════════════

    Question: "Who founded the company that developed GPT-4?"

    VECTOR RAG:                          GRAPH RAG:
    ───────────                          ──────────

    Chunk 1: "OpenAI developed          Graph traversal:
             GPT-4 in 2023"
                                         GPT-4 ◄──[DEVELOPED]── OpenAI
    Chunk 2: "Sam Altman and                                      │
             Elon Musk founded                              [FOUNDED]
             OpenAI"                                              │
                                                                  ▼
    ❌ May not retrieve                  Sam Altman, Elon Musk
       both chunks!
                                         ✅ Follows path directly!

    ❌ No explicit connection            ✅ Explicit relationship chain
```

---

## 6. K-Hop Retrieval Visualization

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         K-HOP RETRIEVAL EXPLAINED                             │
└──────────────────────────────────────────────────────────────────────────────┘

Given seed entity: [OpenAI]

K = 0 (Seed Only)
─────────────────
                              ┌─────────┐
                              │ OpenAI  │  ← Only seed
                              └─────────┘


K = 1 (Direct Neighbors)
────────────────────────
                              ┌─────────┐
              ┌───────────────│ OpenAI  │───────────────┐
              │               └─────────┘               │
              ▼                    │                    ▼
         ┌─────────┐               │              ┌─────────┐
         │ GPT-4   │               ▼              │ ChatGPT │
         └─────────┘          ┌─────────┐         └─────────┘
                              │Sam Altman│
                              └─────────┘

         Retrieved: {OpenAI, GPT-4, ChatGPT, Sam Altman}


K = 2 (Neighbors of Neighbors)
──────────────────────────────
                                         ┌───────────┐
                                         │Transformer│  ← 2 hops from OpenAI
                                         └───────────┘
                                               ▲
                              ┌─────────┐      │
              ┌───────────────│ OpenAI  │──────┼───────────┐
              │               └─────────┘      │           │
              ▼                    │           │           ▼
         ┌─────────┐               │           │      ┌─────────┐
         │ GPT-4   │───────────────┼───────────┘      │ ChatGPT │
         └─────────┘               │                  └─────────┘
                                   ▼
                              ┌─────────┐
                              │Sam Altman│
                              └─────────┘

         Retrieved: {OpenAI, GPT-4, ChatGPT, Sam Altman, Transformer}


⚠️  WARNING: K = 3+ often retrieves TOO MUCH!
    In small graphs, K=3 may retrieve the entire graph.
    Recommended: Start with K=1 or K=2
```

---

## 7. LLM Interaction Points

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    WHERE LLM IS CALLED IN GRAPHRAG                            │
└──────────────────────────────────────────────────────────────────────────────┘

                           GraphRAG Pipeline
    ════════════════════════════════════════════════════════════════════

    INDEXING PHASE                         QUERY PHASE
    ──────────────                         ───────────

    ┌────────────────┐                     ┌────────────────┐
    │   Document     │                     │     Query      │
    └───────┬────────┘                     └───────┬────────┘
            │                                      │
            ▼                                      ▼
    ┌───────────────────┐              ┌───────────────────┐
    │                   │              │                   │
    │   🤖 LLM CALL #1  │              │   🤖 LLM CALL #2  │  (Optional)
    │                   │              │                   │
    │   Entity/Relation │              │   Entity Matching │
    │   Extraction      │              │   from Query      │
    │                   │              │                   │
    └─────────┬─────────┘              └─────────┬─────────┘
              │                                  │
              ▼                                  ▼
    ┌────────────────┐                 ┌────────────────┐
    │  Build Graph   │                 │  K-hop Retrieve│
    │  (No LLM)      │                 │  (No LLM)      │
    └────────────────┘                 └───────┬────────┘
                                               │
                                               ▼
                                   ┌───────────────────┐
                                   │                   │
                                   │   🤖 LLM CALL #3  │
                                   │                   │
                                   │   Answer          │
                                   │   Generation      │
                                   │                   │
                                   └─────────┬─────────┘
                                             │
                                             ▼
                                   ┌────────────────┐
                                   │    Answer      │
                                   └────────────────┘

    ═══════════════════════════════════════════════════════════════════

    TOTAL LLM CALLS:
    • Indexing: 1 call per document (or chunk)
    • Query: 1-2 calls per question

    COST CONSIDERATION:
    • Indexing is expensive but done ONCE
    • Query cost is similar to Vector RAG
```
