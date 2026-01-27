"""
=============================================================================
GraphRAG Teaching Demo - Complete Pipeline
=============================================================================

This module combines all components into a complete GraphRAG system.

TEACHING NOTES:
---------------
This is the END-TO-END pipeline:

Documents → Extraction → Graph → Retrieval → Generation → Answer
   │            │          │         │            │          │
 Input       LLM call   NetworkX   K-hop      LLM call    Output
              (1)                   (2)         (3)

Three LLM calls in total:
1. Extract entities/relations from documents
2. Match query entities (optional)
3. Generate final answer

IMPORTANT INSIGHT:
------------------
GraphRAG trades LATENCY for REASONING CAPABILITY.
- More LLM calls = slower
- But: Can answer questions Vector RAG cannot
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional
import networkx as nx


class GraphRAGPipeline:
    """
    Complete GraphRAG pipeline from documents to answers.

    TEACHING NOTE:
    This class orchestrates the entire GraphRAG process.
    Each step is modular and can be replaced/improved independently.
    """

    def __init__(
        self,
        llm_model: str = "qwen2.5:7b",
        llm_base_url: str = "http://localhost:11434"
    ):
        """
        Initialize the pipeline.

        Args:
            llm_model: Ollama model name
            llm_base_url: Ollama API URL
        """
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url

        # These will be initialized when needed
        self.graph: Optional[nx.MultiDiGraph] = None
        self.documents = []

        print(f"[Pipeline] Initialized with model: {llm_model}")

    def load_documents(self, filepath: str) -> list:
        """
        Load documents from JSON file.

        Expected format:
        {
            "documents": [
                {"id": "...", "title": "...", "content": "..."},
                ...
            ]
        }
        """
        print(f"[Pipeline] Loading documents from {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.documents = data.get("documents", [])
        print(f"[Pipeline] Loaded {len(self.documents)} documents")

        return self.documents

    def build_graph(self) -> nx.MultiDiGraph:
        """
        Extract knowledge and build graph from loaded documents.

        TEACHING NOTE:
        This is the INDEXING phase of GraphRAG.
        - Expensive (many LLM calls)
        - Should be done ONCE and saved
        - Takes time proportional to document length
        """
        if not self.documents:
            raise ValueError("No documents loaded. Call load_documents() first.")

        print("\n" + "=" * 60)
        print("[Pipeline] BUILDING KNOWLEDGE GRAPH")
        print("=" * 60)

        # Import extractor
        from _03_extraction.extractor import OllamaClient, KnowledgeExtractor

        # Initialize components
        llm = OllamaClient(base_url=self.llm_base_url, model=self.llm_model)
        extractor = KnowledgeExtractor(llm)

        # Extract from all documents
        extractions = extractor.extract_from_documents(self.documents)

        print(f"\n[Pipeline] Extraction complete:")
        print(f"  Entities: {len(extractions['entities'])}")
        print(f"  Relationships: {len(extractions['relationships'])}")

        # Build graph
        from _04_graph.builder import KnowledgeGraphBuilder

        builder = KnowledgeGraphBuilder()
        self.graph = builder.build(extractions)

        return self.graph

    def query(
        self,
        question: str,
        k_hops: int = 2,
        max_nodes: int = 20,
        generation_mode: str = "standard"
    ) -> dict:
        """
        Answer a question using the knowledge graph.

        Args:
            question: The user's question
            k_hops: How many hops to expand from seed entities
            max_nodes: Maximum nodes in retrieved subgraph
            generation_mode: "standard", "reasoning", or "strict"

        Returns:
            Dict with answer, context, and metadata

        TEACHING NOTE:
        This is the QUERY phase of GraphRAG:
        1. Find relevant entities in question
        2. Retrieve subgraph around those entities
        3. Generate answer using subgraph context
        """
        if self.graph is None or self.graph.number_of_nodes() == 0:
            raise ValueError("Graph not built. Call build_graph() first.")

        print("\n" + "=" * 60)
        print(f"[Pipeline] ANSWERING QUESTION")
        print(f"[Pipeline] Q: {question}")
        print("=" * 60)

        # Step 1: Retrieve relevant subgraph
        from _05_retrieval.retriever import GraphRetriever

        retriever = GraphRetriever(self.graph, self.llm_base_url)
        subgraph = retriever.retrieve(
            query=question,
            k_hops=k_hops,
            max_nodes=max_nodes,
            use_llm_matching=True
        )

        # Step 2: Convert subgraph to text context
        context = retriever.subgraph_to_text(subgraph)

        print(f"\n[Pipeline] Retrieved context ({len(context)} chars)")

        # Step 3: Generate answer
        from _06_generation.generator import AnswerGenerator

        generator = AnswerGenerator(
            llm_base_url=self.llm_base_url,
            model=self.llm_model
        )

        result = generator.generate(
            question=question,
            context=context,
            mode=generation_mode
        )

        # Add metadata
        result["subgraph_nodes"] = list(subgraph.nodes())
        result["subgraph_edges"] = subgraph.number_of_edges()
        result["context"] = context

        print(f"\n[Pipeline] Answer generated")
        print("-" * 40)
        print(result["answer"])

        return result

    def visualize(self, save_path: Optional[str] = None):
        """
        Visualize the knowledge graph.
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        from _04_graph.visualizer import visualize_graph_matplotlib

        visualize_graph_matplotlib(
            self.graph,
            title="Knowledge Graph",
            save_path=save_path
        )

    def save_graph(self, filepath: str):
        """Save graph to file."""
        if self.graph is None:
            raise ValueError("Graph not built.")

        nx.write_graphml(self.graph, filepath)
        print(f"[Pipeline] Graph saved to {filepath}")

    def load_graph(self, filepath: str):
        """Load graph from file."""
        self.graph = nx.read_graphml(filepath)
        print(f"[Pipeline] Graph loaded from {filepath}")
        print(f"[Pipeline] {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def get_stats(self) -> dict:
        """Get pipeline statistics."""
        if self.graph is None:
            return {"status": "Graph not built"}

        from _04_graph.builder import KnowledgeGraphBuilder
        builder = KnowledgeGraphBuilder()
        builder.graph = self.graph
        return builder.get_stats()


# =============================================================================
# Simplified Interface
# =============================================================================

def create_simple_graph_manually() -> nx.MultiDiGraph:
    """
    Create a simple knowledge graph manually for testing.

    TEACHING NOTE:
    This is useful when you want to test retrieval/generation
    without running the full extraction pipeline.
    """
    G = nx.MultiDiGraph()

    # Add nodes (entities)
    entities = [
        ("openai", "OpenAI", "ORGANIZATION", "AI research company"),
        ("sam altman", "Sam Altman", "PERSON", "CEO of OpenAI"),
        ("elon musk", "Elon Musk", "PERSON", "Co-founder of OpenAI"),
        ("gpt-4", "GPT-4", "TECHNOLOGY", "Large language model"),
        ("chatgpt", "ChatGPT", "TECHNOLOGY", "Conversational AI"),
        ("google", "Google", "ORGANIZATION", "Technology company"),
        ("transformer", "Transformer", "TECHNOLOGY", "Neural network architecture"),
        ("bert", "BERT", "TECHNOLOGY", "Bidirectional encoder model"),
        ("meta", "Meta", "ORGANIZATION", "Social media and AI company"),
        ("llama", "Llama", "TECHNOLOGY", "Open source LLM"),
        ("yann lecun", "Yann LeCun", "PERSON", "Chief AI Scientist at Meta"),
        ("geoffrey hinton", "Geoffrey Hinton", "PERSON", "AI pioneer"),
    ]

    for node_id, name, node_type, desc in entities:
        G.add_node(node_id, name=name, type=node_type, description=desc)

    # Add edges (relationships)
    relationships = [
        ("sam altman", "openai", "CEO_OF"),
        ("elon musk", "openai", "FOUNDED"),
        ("openai", "gpt-4", "DEVELOPED"),
        ("openai", "chatgpt", "DEVELOPED"),
        ("chatgpt", "gpt-4", "BASED_ON"),
        ("gpt-4", "transformer", "BASED_ON"),
        ("google", "transformer", "DEVELOPED"),
        ("google", "bert", "DEVELOPED"),
        ("bert", "transformer", "BASED_ON"),
        ("meta", "llama", "DEVELOPED"),
        ("llama", "transformer", "BASED_ON"),
        ("yann lecun", "meta", "WORKS_AT"),
        ("geoffrey hinton", "google", "WORKS_AT"),
    ]

    for source, target, relation in relationships:
        G.add_edge(source, target, key=relation, relation=relation)

    return G


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    """
    Demo the complete pipeline.

    This shows two modes:
    1. Quick demo with manual graph (no extraction)
    2. Full pipeline with extraction (slower)
    """

    print("=" * 60)
    print("GraphRAG Pipeline Demo")
    print("=" * 60)
    print("\nChoose demo mode:")
    print("1. Quick demo (use pre-built graph, no LLM extraction)")
    print("2. Full demo (extract from documents, slower)")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        # Quick demo with manual graph
        print("\n[Demo] Creating sample graph...")
        graph = create_simple_graph_manually()

        print(f"[Demo] Graph created: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Create pipeline and set graph
        pipeline = GraphRAGPipeline()
        pipeline.graph = graph

        # Test queries
        queries = [
            "Who is the CEO of OpenAI?",
            "What did Google develop?",
            "Who founded OpenAI?",
            "What is ChatGPT based on?",
            "Who works at Meta?",
        ]

        print("\n" + "=" * 60)
        print("Testing Queries")
        print("=" * 60)

        for query in queries:
            print(f"\n{'─' * 60}")
            result = pipeline.query(query, k_hops=2, generation_mode="standard")
            print(f"\nQ: {query}")
            print(f"A: {result['answer']}")

    else:
        # Full demo with extraction
        print("\n[Demo] Running full pipeline...")
        print("[Demo] Make sure Ollama is running!")

        pipeline = GraphRAGPipeline(llm_model="qwen2.5:7b")

        # Load documents
        data_path = Path(__file__).parent.parent / "02_data" / "sample_corpus.json"
        if not data_path.exists():
            print(f"[Demo] Error: Data file not found at {data_path}")
            sys.exit(1)

        pipeline.load_documents(str(data_path))

        # Build graph (this takes time!)
        print("\n[Demo] Building graph (this may take a few minutes)...")
        pipeline.build_graph()

        # Save for later use
        pipeline.save_graph("knowledge_graph.graphml")

        # Visualize
        print("\n[Demo] Visualizing graph...")
        pipeline.visualize(save_path="knowledge_graph.png")

        # Query
        query = input("\nEnter your question: ")
        result = pipeline.query(query)

        print(f"\nAnswer: {result['answer']}")
