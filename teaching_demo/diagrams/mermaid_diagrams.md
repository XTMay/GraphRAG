# GraphRAG Mermaid Diagrams

These diagrams can be rendered in GitHub, VS Code (with Mermaid extension), Notion, or https://mermaid.live

---

## 1. Overall Pipeline Flow

```mermaid
flowchart TB
    subgraph Indexing["📥 INDEXING PHASE (Offline)"]
        D[("📄 Documents")] --> E["🔍 LLM Extraction"]
        E --> |"entities, relations"| G[("🕸️ Knowledge Graph")]
    end

    subgraph Query["🔎 QUERY PHASE (Online)"]
        Q["❓ User Question"] --> M["🎯 Entity Matching"]
        M --> R["🔗 K-Hop Retrieval"]
        R --> |"subgraph"| C["📝 Context Text"]
        C --> L["🤖 LLM Generation"]
        L --> A["✅ Answer"]
    end

    G --> R

    style Indexing fill:#e1f5fe
    style Query fill:#f3e5f5
```

---

## 2. Indexing Pipeline Detail

```mermaid
flowchart LR
    subgraph Input
        D1["doc1.txt"]
        D2["doc2.txt"]
        D3["doc3.txt"]
    end

    subgraph Extraction["LLM Extraction"]
        LLM["🤖 Qwen/Llama"]
    end

    subgraph Output
        ENT["Entities<br/>- OpenAI (ORG)<br/>- GPT-4 (TECH)<br/>- Sam Altman (PERSON)"]
        REL["Relationships<br/>- OpenAI → DEVELOPED → GPT-4<br/>- Sam Altman → CEO_OF → OpenAI"]
    end

    subgraph Graph["Knowledge Graph"]
        KG[("NetworkX<br/>MultiDiGraph")]
    end

    D1 & D2 & D3 --> LLM
    LLM --> ENT & REL
    ENT & REL --> KG
```

---

## 3. Query Pipeline Detail

```mermaid
flowchart LR
    Q["🔍 Query:<br/>'What did OpenAI develop?'"]

    subgraph Match["Step 1: Entity Match"]
        M["Find 'OpenAI'<br/>in graph"]
    end

    subgraph Retrieve["Step 2: K-Hop Retrieval"]
        R["Expand from<br/>seed nodes"]
    end

    subgraph Context["Step 3: Build Context"]
        C["Convert subgraph<br/>to text"]
    end

    subgraph Generate["Step 4: Generate"]
        G["🤖 LLM answers<br/>using context"]
    end

    A["✅ Answer:<br/>'OpenAI developed<br/>GPT-4 and ChatGPT'"]

    Q --> M --> R --> C --> G --> A
```

---

## 4. K-Hop Expansion Visualization

```mermaid
flowchart TB
    subgraph K0["K=0: Seed Only"]
        O0[OpenAI]
    end

    subgraph K1["K=1: Direct Neighbors"]
        O1[OpenAI]
        G1[GPT-4]
        C1[ChatGPT]
        S1[Sam Altman]
        O1 --> G1
        O1 --> C1
        S1 --> O1
    end

    subgraph K2["K=2: 2-Hop Neighbors"]
        O2[OpenAI]
        G2[GPT-4]
        C2[ChatGPT]
        S2[Sam Altman]
        T2[Transformer]
        O2 --> G2
        O2 --> C2
        S2 --> O2
        G2 --> T2
        C2 -.-> G2
    end
```

---

## 5. Vector RAG vs Graph RAG

```mermaid
flowchart TB
    subgraph VectorRAG["📊 Vector RAG"]
        VD["Documents"] --> VC["Chunks"]
        VC --> VE["Embeddings"]
        VE --> VS[("Vector DB")]
        VQ["Query"] --> VSearch["Similarity Search"]
        VS --> VSearch
        VSearch --> VChunks["Top-K Chunks"]
        VChunks --> VLLM["LLM"]
        VLLM --> VA["Answer"]
    end

    subgraph GraphRAG["🕸️ Graph RAG"]
        GD["Documents"] --> GE["Entity Extraction"]
        GE --> GG[("Knowledge Graph")]
        GQ["Query"] --> GM["Entity Match"]
        GM --> GR["K-Hop Traverse"]
        GG --> GR
        GR --> GC["Subgraph Context"]
        GC --> GLLM["LLM"]
        GLLM --> GA["Answer"]
    end

    style VectorRAG fill:#fff3e0
    style GraphRAG fill:#e8f5e9
```

---

## 6. Component Architecture

```mermaid
flowchart TB
    subgraph UI["User Interface"]
        CLI["run_demo.py"]
    end

    subgraph Core["Core Components"]
        EXT["Extractor<br/>03_extraction/"]
        BLD["Graph Builder<br/>04_graph/"]
        RET["Retriever<br/>05_retrieval/"]
        GEN["Generator<br/>06_generation/"]
    end

    subgraph External["External Services"]
        LLM["🤖 Ollama<br/>localhost:11434"]
        NX[("NetworkX<br/>Graph")]
    end

    CLI --> EXT & RET & GEN
    EXT --> LLM
    EXT --> BLD
    BLD --> NX
    RET --> NX
    GEN --> LLM
```

---

## 7. Data Transformation Flow

```mermaid
flowchart LR
    subgraph Types["Data Types at Each Stage"]
        T1["📄 str<br/>(raw text)"]
        T2["📋 JSON<br/>(entities, relations)"]
        T3["🕸️ Graph<br/>(NetworkX object)"]
        T4["📝 str<br/>(context text)"]
        T5["✅ str<br/>(answer)"]
    end

    T1 -->|"LLM Extract"| T2
    T2 -->|"Build Graph"| T3
    T3 -->|"K-hop + Format"| T4
    T4 -->|"LLM Generate"| T5
```

---

## 8. Sequence Diagram: Query Processing

```mermaid
sequenceDiagram
    participant U as User
    participant P as Pipeline
    participant R as Retriever
    participant G as Graph (NetworkX)
    participant L as LLM (Ollama)

    U->>P: "Who is the CEO of OpenAI?"
    P->>R: retrieve(query)
    R->>R: find_seeds("openai")
    R->>G: get_neighbors(openai, k=2)
    G-->>R: subgraph nodes
    R->>R: subgraph_to_text()
    R-->>P: context string
    P->>L: generate(context, question)
    L-->>P: "Sam Altman is the CEO..."
    P-->>U: Answer
```

---

## 9. Entity-Relationship Example

```mermaid
erDiagram
    OPENAI ||--o{ GPT4 : developed
    OPENAI ||--o{ CHATGPT : developed
    SAM_ALTMAN ||--|| OPENAI : ceo_of
    ELON_MUSK ||--|| OPENAI : co_founded
    GPT4 ||--|| TRANSFORMER : based_on
    CHATGPT ||--|| GPT4 : based_on
    GOOGLE ||--|| TRANSFORMER : developed
    GOOGLE ||--|| BERT : developed
    BERT ||--|| TRANSFORMER : based_on
```

---

## 10. Decision Flow: When to Use GraphRAG

```mermaid
flowchart TD
    Q["Does your question<br/>involve relationships?"]
    Q -->|Yes| R["Do you need to connect<br/>multiple facts?"]
    Q -->|No| V["Use Vector RAG ✅"]

    R -->|Yes| G["Use GraphRAG ✅"]
    R -->|No| M["Multi-hop reasoning<br/>required?"]

    M -->|Yes| G
    M -->|No| V

    style G fill:#c8e6c9
    style V fill:#fff9c4
```

---

## How to Render These Diagrams

1. **GitHub**: Just paste the markdown - GitHub renders Mermaid natively

2. **VS Code**: Install "Markdown Preview Mermaid Support" extension

3. **Online**: Paste code blocks at https://mermaid.live

4. **Export**: Use mermaid-cli to export as PNG/SVG:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   mmdc -i mermaid_diagrams.md -o output.png
   ```
