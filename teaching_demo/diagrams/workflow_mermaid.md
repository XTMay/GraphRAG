# GraphRAG Workflow - Mermaid Diagrams

> These diagrams can be rendered on GitHub, VS Code (with Mermaid extension), or https://mermaid.live

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph System["🏗️ GraphRAG System Architecture"]
        subgraph Indexing["📥 INDEXING PHASE (Offline)"]
            direction LR
            D["📄 Documents<br/>(Raw Text)"]
            E["🤖 LLM-based<br/>Extraction"]
            KG["🕸️ Knowledge<br/>Graph"]
            D --> E --> KG

            D2["Text Chunks"]
            E2["Entities &<br/>Relations"]
            KG2["Nodes &<br/>Edges"]
            D -.-> D2
            E -.-> E2
            KG -.-> KG2
        end

        subgraph Query["🔎 QUERY PHASE (Online)"]
            direction LR
            Q["❓ User<br/>Query"]
            EM["🎯 Entity<br/>Matching"]
            KH["🔗 K-Hop<br/>Retrieval"]
            SG["📊 Sub-<br/>graph"]
            CT["📝 Context<br/>Text"]
            LLM["🤖 LLM<br/>Generation"]
            A["✅ Answer"]

            Q --> EM --> KH --> SG --> CT --> LLM --> A
        end

        KG -.->|"Graph DB"| KH
    end

    style Indexing fill:#e3f2fd,stroke:#1976d2
    style Query fill:#fce4ec,stroke:#c2185b
```

---

## 2. Detailed Indexing Pipeline

```mermaid
flowchart LR
    subgraph Step1["Step 1.1: Document Ingestion"]
        doc1["📄 doc1.txt"]
        doc2["📄 doc2.txt"]
        doc3["📄 doc3.txt"]
        loader["📂 Text Loader<br/>(UTF-8)"]
        raw["📋 Raw Text<br/>Collection"]

        doc1 --> loader
        doc2 --> loader
        doc3 --> loader
        loader --> raw
    end

    subgraph Step2["Step 1.2: Entity Extraction"]
        rawtext["📋 Raw Text"]
        llm["🤖 LLM + Prompt<br/>(Extraction)"]
        json["📊 Structured<br/>JSON Output"]

        rawtext --> llm --> json
    end

    subgraph Step3["Step 1.3: Graph Construction"]
        struct["📊 JSON<br/>Extractions"]
        graph["🕸️ NetworkX Graph"]

        struct --> graph
    end

    raw --> rawtext
    json --> struct

    style Step1 fill:#fff9c4
    style Step2 fill:#f3e5f5
    style Step3 fill:#e8f5e9
```

---

## 3. Entity Extraction Detail

```mermaid
flowchart TB
    subgraph Input
        text["📄 Raw Text:<br/>'OpenAI developed GPT-4...'"]
    end

    subgraph LLM["🤖 LLM Processing"]
        prompt["📝 Prompt Template:<br/>'Extract entities and<br/>relationships from: {text}'"]
        model["Qwen/Llama/GPT"]
    end

    subgraph Output["📊 JSON Output"]
        entities["entities: [<br/>  {name: 'OpenAI', type: 'ORG'},<br/>  {name: 'GPT-4', type: 'TECH'}<br/>]"]
        relations["relationships: [<br/>  {source: 'OpenAI',<br/>   relation: 'DEVELOPED',<br/>   target: 'GPT-4'}<br/>]"]
    end

    text --> prompt --> model
    model --> entities
    model --> relations

    style LLM fill:#f3e5f5
    style Output fill:#e8f5e9
```

---

## 4. Knowledge Graph Structure

```mermaid
flowchart TB
    subgraph KnowledgeGraph["🕸️ Knowledge Graph (NetworkX)"]
        Sam["👤 Sam Altman<br/>(PERSON)"]
        OpenAI["🏢 OpenAI<br/>(ORGANIZATION)"]
        GPT4["💻 GPT-4<br/>(TECHNOLOGY)"]
        ChatGPT["💬 ChatGPT<br/>(TECHNOLOGY)"]
        Transformer["⚡ Transformer<br/>(TECHNOLOGY)"]

        Sam -->|"CEO_OF"| OpenAI
        OpenAI -->|"DEVELOPED"| GPT4
        OpenAI -->|"DEVELOPED"| ChatGPT
        ChatGPT -->|"BASED_ON"| GPT4
        GPT4 -->|"BASED_ON"| Transformer
    end

    style Sam fill:#ffcdd2
    style OpenAI fill:#bbdefb
    style GPT4 fill:#c8e6c9
    style ChatGPT fill:#c8e6c9
    style Transformer fill:#fff9c4
```

---

## 5. Query Pipeline - Step by Step

```mermaid
flowchart LR
    subgraph S1["Step 2.1"]
        Q["❓ User Query:<br/>'What did OpenAI develop?'"]
        EM["🎯 Entity Matching<br/>Find 'OpenAI' in graph"]
        Seeds["🌱 Seeds: [openai]"]
        Q --> EM --> Seeds
    end

    subgraph S2["Step 2.2"]
        KHop["🔗 K-Hop Retrieval<br/>Expand k=2 hops"]
        Sub["📊 Subgraph"]
        Seeds2["🌱 Seeds"]
        Seeds2 --> KHop --> Sub
    end

    subgraph S3["Step 2.3"]
        Sub2["📊 Subgraph"]
        Convert["⚙️ Convert to Text"]
        Context["📝 Context:<br/>'Entities: OpenAI, GPT-4...<br/>Relations: DEVELOPED...'"]
        Sub2 --> Convert --> Context
    end

    subgraph S4["Step 2.4"]
        Context2["📝 Context + Question"]
        LLM["🤖 LLM Generation"]
        Answer["✅ Answer:<br/>'OpenAI developed<br/>GPT-4 and ChatGPT'"]
        Context2 --> LLM --> Answer
    end

    Seeds --> Seeds2
    Sub --> Sub2
    Context --> Context2

    style S1 fill:#e1f5fe
    style S2 fill:#fff3e0
    style S3 fill:#f5f5f5
    style S4 fill:#e8f5e9
```

---

## 6. K-Hop Retrieval Visualization

```mermaid
flowchart TB
    subgraph K0["K = 0 (Seed Only)"]
        O0["🏢 OpenAI"]
    end

    subgraph K1["K = 1 (Direct Neighbors)"]
        O1["🏢 OpenAI"]
        G1["💻 GPT-4"]
        C1["💬 ChatGPT"]
        S1["👤 Sam Altman"]

        O1 --> G1
        O1 --> C1
        S1 --> O1
    end

    subgraph K2["K = 2 (2-Hop Neighbors)"]
        O2["🏢 OpenAI"]
        G2["💻 GPT-4"]
        C2["💬 ChatGPT"]
        S2["👤 Sam Altman"]
        T2["⚡ Transformer"]

        O2 --> G2
        O2 --> C2
        S2 --> O2
        G2 --> T2
        C2 -.-> G2
    end

    K0 -.->|"expand"| K1
    K1 -.->|"expand"| K2

    style O0 fill:#bbdefb
    style O1 fill:#bbdefb
    style O2 fill:#bbdefb
    style T2 fill:#fff9c4
```

---

## 7. Vector RAG vs Graph RAG Comparison

```mermaid
flowchart TB
    subgraph VectorRAG["📊 Vector RAG"]
        direction TB
        VD["📄 Documents"]
        VC["✂️ Chunks"]
        VE["🔢 Embeddings"]
        VDB[("🗄️ Vector DB")]
        VQ["❓ Query"]
        VS["🔍 Similarity Search"]
        VCh["📋 Top-K Chunks"]
        VLLM["🤖 LLM"]
        VA["✅ Answer"]

        VD --> VC --> VE --> VDB
        VQ --> VS
        VDB --> VS
        VS --> VCh --> VLLM --> VA
    end

    subgraph GraphRAG["🕸️ Graph RAG"]
        direction TB
        GD["📄 Documents"]
        GE["🔍 Entity Extraction"]
        GG[("🕸️ Knowledge Graph")]
        GQ["❓ Query"]
        GM["🎯 Entity Match"]
        GR["🔗 K-Hop Traverse"]
        GC["📝 Subgraph Context"]
        GLLM["🤖 LLM"]
        GA["✅ Answer"]

        GD --> GE --> GG
        GQ --> GM --> GR
        GG --> GR
        GR --> GC --> GLLM --> GA
    end

    style VectorRAG fill:#fff3e0
    style GraphRAG fill:#e8f5e9
```

---

## 8. Multi-Hop Reasoning Example

```mermaid
flowchart LR
    subgraph Question
        Q["❓ Who founded the company<br/>that developed GPT-4?"]
    end

    subgraph VectorApproach["❌ Vector RAG Approach"]
        VC1["Chunk: 'OpenAI<br/>developed GPT-4'"]
        VC2["Chunk: 'Sam Altman<br/>founded OpenAI'"]
        VFail["❌ May not retrieve<br/>both chunks!"]

        VC1 -.-> VFail
        VC2 -.-> VFail
    end

    subgraph GraphApproach["✅ Graph RAG Approach"]
        GPT4["💻 GPT-4"]
        OpenAI["🏢 OpenAI"]
        Sam["👤 Sam Altman"]
        Elon["👤 Elon Musk"]

        GPT4 -->|"DEVELOPED_BY"| OpenAI
        OpenAI -->|"FOUNDED_BY"| Sam
        OpenAI -->|"FOUNDED_BY"| Elon
    end

    Q --> VectorApproach
    Q --> GraphApproach

    style VFail fill:#ffcdd2
    style GraphApproach fill:#c8e6c9
```

---

## 9. Component Interaction

```mermaid
flowchart TB
    UI["🖥️ User Interface<br/>(run_demo.py)"]

    subgraph Pipeline["Pipeline Orchestrator"]
        PO["graphrag_pipeline.py"]
    end

    subgraph Components["Core Components"]
        EXT["📤 Extractor<br/>extractor.py"]
        RET["🔍 Retriever<br/>retriever.py"]
        GEN["✍️ Generator<br/>generator.py"]
    end

    subgraph Infrastructure["Infrastructure"]
        BLD["🏗️ Graph Builder<br/>builder.py"]
        NX[("🕸️ NetworkX<br/>Graph")]
        LLM["🤖 Ollama<br/>LLM API"]
    end

    UI --> PO
    PO --> EXT & RET & GEN
    EXT --> BLD --> NX
    EXT --> LLM
    RET --> NX
    GEN --> LLM

    style Pipeline fill:#e3f2fd
    style Components fill:#f3e5f5
    style Infrastructure fill:#fff9c4
```

---

## 10. Data Flow Diagram

```mermaid
flowchart LR
    subgraph IndexFlow["📥 Indexing Flow"]
        IF1["📄 Files<br/>(.txt, .json)"]
        IF2["📋 String<br/>(raw text)"]
        IF3["📊 JSON<br/>(entities, relations)"]
        IF4["🕸️ NetworkX<br/>Graph Object"]

        IF1 -->|"load"| IF2 -->|"LLM extract"| IF3 -->|"build"| IF4
    end

    subgraph QueryFlow["🔎 Query Flow"]
        QF1["❓ User Query<br/>(string)"]
        QF2["🌱 Seed Entities<br/>(list)"]
        QF3["📊 Subgraph<br/>(nodes + edges)"]
        QF4["📝 Text Context<br/>(string)"]
        QF5["🤖 LLM Output<br/>(string)"]
        QF6["✅ Final Answer<br/>(string)"]

        QF1 -->|"match"| QF2 -->|"k-hop"| QF3 -->|"format"| QF4 -->|"generate"| QF5 --> QF6
    end

    IF4 -.->|"graph storage"| QF3

    style IndexFlow fill:#e3f2fd
    style QueryFlow fill:#fce4ec
```

---

## 11. LLM Call Points

```mermaid
flowchart TB
    subgraph IndexPhase["📥 INDEXING PHASE"]
        ID["📄 Document"]
        ILLM["🤖 LLM CALL #1<br/>Entity/Relation<br/>Extraction"]
        IBuild["🏗️ Build Graph<br/>(No LLM)"]

        ID --> ILLM --> IBuild
    end

    subgraph QueryPhase["🔎 QUERY PHASE"]
        QD["❓ Query"]
        QLLM1["🤖 LLM CALL #2<br/>Entity Matching<br/>(Optional)"]
        QRet["🔗 K-hop Retrieve<br/>(No LLM)"]
        QLLM2["🤖 LLM CALL #3<br/>Answer Generation"]
        QA["✅ Answer"]

        QD --> QLLM1 --> QRet --> QLLM2 --> QA
    end

    IBuild -.->|"Graph"| QRet

    style ILLM fill:#f3e5f5,stroke:#7b1fa2
    style QLLM1 fill:#f3e5f5,stroke:#7b1fa2
    style QLLM2 fill:#f3e5f5,stroke:#7b1fa2
```

---

## 12. Complete End-to-End Workflow

```mermaid
flowchart TB
    subgraph Phase1["📥 PHASE 1: INDEXING (One-time)"]
        P1S1["1️⃣ Load Documents"]
        P1S2["2️⃣ LLM Extracts<br/>Entities & Relations"]
        P1S3["3️⃣ Build Knowledge Graph"]
        P1S4["4️⃣ Store Graph"]

        P1S1 --> P1S2 --> P1S3 --> P1S4
    end

    subgraph Phase2["🔎 PHASE 2: QUERY (Per question)"]
        P2S1["1️⃣ Receive Query"]
        P2S2["2️⃣ Match Entities"]
        P2S3["3️⃣ K-Hop Expand"]
        P2S4["4️⃣ Build Context"]
        P2S5["5️⃣ LLM Generate"]
        P2S6["6️⃣ Return Answer"]

        P2S1 --> P2S2 --> P2S3 --> P2S4 --> P2S5 --> P2S6
    end

    P1S4 -.->|"Graph DB"| P2S3

    style Phase1 fill:#e3f2fd,stroke:#1976d2
    style Phase2 fill:#fce4ec,stroke:#c2185b
```

---

## 13. Entity-Relationship Diagram (Sample Graph)

```mermaid
erDiagram
    OPENAI ||--o{ GPT4 : "DEVELOPED"
    OPENAI ||--o{ CHATGPT : "DEVELOPED"
    SAM_ALTMAN ||--|| OPENAI : "CEO_OF"
    ELON_MUSK ||--|| OPENAI : "CO_FOUNDED"
    ILYA_SUTSKEVER ||--|| OPENAI : "CO_FOUNDED"
    GPT4 ||--|| TRANSFORMER : "BASED_ON"
    CHATGPT ||--|| GPT4 : "BASED_ON"
    GOOGLE ||--|| TRANSFORMER : "DEVELOPED"
    GOOGLE ||--|| BERT : "DEVELOPED"
    BERT ||--|| TRANSFORMER : "BASED_ON"
    META ||--|| LLAMA : "DEVELOPED"
    LLAMA ||--|| TRANSFORMER : "BASED_ON"
    YANN_LECUN ||--|| META : "WORKS_AT"
```

---

## 14. Sequence Diagram: Query Processing

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant P as 🎛️ Pipeline
    participant R as 🔍 Retriever
    participant G as 🕸️ Graph (NetworkX)
    participant L as 🤖 LLM (Ollama)

    U->>P: "Who is the CEO of OpenAI?"
    activate P

    P->>R: retrieve(query, k=2)
    activate R

    R->>R: find_seeds("openai")
    R->>G: get_neighbors(openai, k=2)
    G-->>R: subgraph nodes & edges
    R->>R: subgraph_to_text()
    R-->>P: context string
    deactivate R

    P->>L: generate(context, question)
    activate L
    L-->>P: "Sam Altman is the CEO of OpenAI"
    deactivate L

    P-->>U: Answer: "Sam Altman is the CEO of OpenAI"
    deactivate P
```

---

## 15. Decision Flowchart: When to Use GraphRAG

```mermaid
flowchart TD
    Start["🤔 New RAG Project"]
    Q1{"Does your data have<br/>entities & relationships?"}
    Q2{"Do questions require<br/>multi-hop reasoning?"}
    Q3{"Need explainable<br/>reasoning paths?"}
    Q4{"Is global understanding<br/>important?"}

    VR["✅ Use Vector RAG<br/>Simpler, faster"]
    GR["✅ Use GraphRAG<br/>Better reasoning"]
    HY["🔀 Consider Hybrid<br/>Vector + Graph"]

    Start --> Q1
    Q1 -->|"No"| VR
    Q1 -->|"Yes"| Q2
    Q2 -->|"No"| Q3
    Q2 -->|"Yes"| GR
    Q3 -->|"No"| Q4
    Q3 -->|"Yes"| GR
    Q4 -->|"No"| VR
    Q4 -->|"Yes"| HY

    style VR fill:#fff9c4
    style GR fill:#c8e6c9
    style HY fill:#e1f5fe
```

---

## How to Use These Diagrams

### GitHub
Just view this file on GitHub - diagrams render automatically.

### VS Code
1. Install extension: **Markdown Preview Mermaid Support**
2. Open this file
3. Press `Cmd+Shift+V` (Mac) or `Ctrl+Shift+V` (Windows) to preview

### Export to Images
1. Go to https://mermaid.live
2. Paste any diagram code block
3. Download as PNG/SVG

### In Presentations
- Use screenshots from mermaid.live
- Or embed in tools that support Mermaid (Notion, Obsidian, etc.)
