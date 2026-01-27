#!/usr/bin/env python3
"""
=============================================================================
GraphRAG Teaching Demo - Interactive Runner
=============================================================================

This script provides an interactive demonstration of GraphRAG concepts.
Run this script to explore how GraphRAG works step by step.

Usage:
    python run_demo.py

TEACHING NOTE:
--------------
This demo is designed to be run INTERACTIVELY in class.
Each step is explained and results are shown clearly.
"""

import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import networkx as nx
import requests


def print_banner():
    """Print welcome banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗██████╗  █████╗  ██████╗       ║
║  ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗██╔════╝       ║
║  ██║  ███╗██████╔╝███████║██████╔╝███████║██████╔╝███████║██║  ███╗      ║
║  ██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║   ██║      ║
║  ╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║██║  ██║██║  ██║╚██████╔╝      ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝       ║
║                                                                           ║
║              📚 Teaching Demo - Learn GraphRAG Step by Step               ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def check_ollama():
    """Check if Ollama is running and return available model."""
    print("\n[System Check] Checking Ollama...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"  ✓ Ollama is running ({len(models)} models available)")
            if models:
                print("  Available models:")
                for m in models[:5]:
                    print(f"    - {m['name']}")
            return True
    except:
        pass

    print("  ✗ Ollama is not running!")
    print("\n  To start Ollama:")
    print("    1. Open a new terminal")
    print("    2. Run: ollama serve")
    print("    3. In another terminal: ollama pull qwen2.5:3b")
    return False


def get_best_model():
    """Get the best available model from Ollama."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m['name'] for m in response.json().get("models", [])]

        # Preference order
        preferred = ['qwen2.5:7b', 'qwen2.5:14b', 'qwen2.5:3b', 'llama3.1:8b',
                     'llama2:latest', 'mistral:latest', 'gemma3:4b']

        for model in preferred:
            if model in models:
                return model

        # Return first available if none preferred
        return models[0] if models else "qwen2.5:3b"
    except:
        return "qwen2.5:3b"


def call_ollama(prompt, temperature=0):
    """Call Ollama API with proper error handling."""
    model = get_best_model()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            },
            timeout=120
        )

        result = response.json()

        # Handle different response formats
        if "response" in result:
            return result["response"]
        elif "message" in result:
            return result["message"].get("content", str(result))
        else:
            return str(result)

    except requests.exceptions.Timeout:
        return "Error: Request timed out. The model might be loading."
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# Create Sample Graph (No LLM needed)
# =============================================================================

def create_sample_graph():
    """
    Create a sample knowledge graph for demonstration.

    TEACHING NOTE:
    In real GraphRAG, this graph would be extracted from documents using LLM.
    For teaching, we create it manually to show the structure clearly.
    """
    G = nx.MultiDiGraph()

    # === Entities (Nodes) ===
    # Format: (node_id, display_name, type, description)
    entities = [
        # Organizations
        ("openai", "OpenAI", "ORGANIZATION", "AI research company, creator of GPT and ChatGPT"),
        ("google", "Google", "ORGANIZATION", "Technology company, developed Transformer and BERT"),
        ("meta", "Meta", "ORGANIZATION", "Social media company, released Llama models"),
        ("anthropic", "Anthropic", "ORGANIZATION", "AI safety company, created Claude"),

        # People
        ("sam_altman", "Sam Altman", "PERSON", "CEO of OpenAI"),
        ("elon_musk", "Elon Musk", "PERSON", "Co-founder of OpenAI, CEO of Tesla and SpaceX"),
        ("ilya_sutskever", "Ilya Sutskever", "PERSON", "Co-founder of OpenAI, former Chief Scientist"),
        ("geoffrey_hinton", "Geoffrey Hinton", "PERSON", "AI pioneer, Turing Award winner"),
        ("yann_lecun", "Yann LeCun", "PERSON", "Chief AI Scientist at Meta, Turing Award winner"),
        ("dario_amodei", "Dario Amodei", "PERSON", "CEO of Anthropic, former VP at OpenAI"),

        # Technologies
        ("gpt4", "GPT-4", "TECHNOLOGY", "Large multimodal model by OpenAI"),
        ("chatgpt", "ChatGPT", "TECHNOLOGY", "Conversational AI interface for GPT models"),
        ("transformer", "Transformer", "TECHNOLOGY", "Neural network architecture, foundation of modern LLMs"),
        ("bert", "BERT", "TECHNOLOGY", "Bidirectional language model by Google"),
        ("llama", "Llama", "TECHNOLOGY", "Open source LLM by Meta"),
        ("claude", "Claude", "TECHNOLOGY", "AI assistant by Anthropic"),

        # Concepts
        ("attention", "Attention Mechanism", "CONCEPT", "Core component of Transformer architecture"),
        ("deep_learning", "Deep Learning", "CONCEPT", "Machine learning using neural networks"),
    ]

    for node_id, name, node_type, description in entities:
        G.add_node(node_id, name=name, type=node_type, description=description)

    # === Relationships (Edges) ===
    # Format: (source, target, relation_type)
    relationships = [
        # Leadership
        ("sam_altman", "openai", "CEO_OF"),
        ("dario_amodei", "anthropic", "CEO_OF"),
        ("yann_lecun", "meta", "WORKS_AT"),
        ("geoffrey_hinton", "google", "WORKS_AT"),

        # Founding
        ("elon_musk", "openai", "CO_FOUNDED"),
        ("sam_altman", "openai", "CO_FOUNDED"),
        ("ilya_sutskever", "openai", "CO_FOUNDED"),
        ("dario_amodei", "anthropic", "FOUNDED"),

        # Development
        ("openai", "gpt4", "DEVELOPED"),
        ("openai", "chatgpt", "DEVELOPED"),
        ("google", "transformer", "DEVELOPED"),
        ("google", "bert", "DEVELOPED"),
        ("meta", "llama", "DEVELOPED"),
        ("anthropic", "claude", "DEVELOPED"),

        # Based on
        ("chatgpt", "gpt4", "BASED_ON"),
        ("gpt4", "transformer", "BASED_ON"),
        ("bert", "transformer", "BASED_ON"),
        ("llama", "transformer", "BASED_ON"),
        ("claude", "transformer", "BASED_ON"),
        ("transformer", "attention", "USES"),

        # Career moves
        ("dario_amodei", "openai", "FORMERLY_AT"),
        ("ilya_sutskever", "google", "FORMERLY_AT"),

        # Awards
        ("geoffrey_hinton", "deep_learning", "PIONEERED"),
        ("yann_lecun", "deep_learning", "PIONEERED"),
    ]

    for source, target, relation in relationships:
        G.add_edge(source, target, key=relation, relation=relation)

    return G


# =============================================================================
# Demo Steps
# =============================================================================

def demo_step1_understand_graph(graph):
    """Step 1: Understand the knowledge graph structure."""
    print("\n" + "=" * 70)
    print("STEP 1: Understanding the Knowledge Graph")
    print("=" * 70)

    print("""
A knowledge graph represents information as:
  - NODES (entities): People, Organizations, Technologies, etc.
  - EDGES (relationships): How entities are connected

This is DIFFERENT from vector RAG which stores text chunks!
    """)

    print(f"Our graph has:")
    print(f"  - {graph.number_of_nodes()} nodes (entities)")
    print(f"  - {graph.number_of_edges()} edges (relationships)")

    # Count by type
    type_counts = {}
    for node in graph.nodes():
        ntype = graph.nodes[node].get("type", "UNKNOWN")
        type_counts[ntype] = type_counts.get(ntype, 0) + 1

    print(f"\nNodes by type:")
    for ntype, count in sorted(type_counts.items()):
        print(f"  {ntype}: {count}")

    input("\nPress Enter to see example nodes...")

    print("\nExample nodes:")
    for i, node in enumerate(list(graph.nodes())[:5]):
        data = graph.nodes[node]
        print(f"  {i+1}. {data.get('name')} ({data.get('type')})")
        print(f"     → {data.get('description')}")

    input("\nPress Enter to see example edges...")

    print("\nExample relationships:")
    for i, (u, v, data) in enumerate(list(graph.edges(data=True))[:5]):
        source_name = graph.nodes[u].get("name", u)
        target_name = graph.nodes[v].get("name", v)
        relation = data.get("relation", "RELATED")
        print(f"  {i+1}. {source_name} --[{relation}]--> {target_name}")


def demo_step2_retrieval(graph):
    """Step 2: Demonstrate graph-based retrieval."""
    print("\n" + "=" * 70)
    print("STEP 2: Graph-Based Retrieval (K-Hop Expansion)")
    print("=" * 70)

    print("""
In GraphRAG, we retrieve by TRAVERSING the graph:

1. Find seed entities mentioned in the query
2. Expand K hops from those seeds
3. Collect the subgraph as context

K-hop means: how many edges to follow from the starting point
  K=1: Direct neighbors only
  K=2: Neighbors + their neighbors
    """)

    # Demo query
    query = "What did OpenAI develop?"
    print(f"\nDemo Query: \"{query}\"")

    # Find seed
    seed = "openai"
    print(f"\nStep 2a: Find seed entity")
    print(f"  → Found: '{graph.nodes[seed].get('name')}'")

    # K=1 expansion
    print(f"\nStep 2b: K=1 expansion (direct neighbors)")
    neighbors_1 = set(graph.successors(seed)) | set(graph.predecessors(seed))
    print(f"  → Found {len(neighbors_1)} neighbors:")
    for n in list(neighbors_1)[:8]:
        name = graph.nodes[n].get("name", n)
        print(f"     - {name}")

    input("\nPress Enter to see K=2 expansion...")

    # K=2 expansion
    all_nodes = {seed} | neighbors_1
    neighbors_2 = set()
    for n in neighbors_1:
        neighbors_2.update(graph.successors(n))
        neighbors_2.update(graph.predecessors(n))
    neighbors_2 -= all_nodes

    print(f"\nStep 2c: K=2 expansion (2 hops away)")
    print(f"  → Found {len(neighbors_2)} additional nodes:")
    for n in list(neighbors_2)[:8]:
        name = graph.nodes[n].get("name", n)
        print(f"     - {name}")

    all_nodes |= neighbors_2
    print(f"\nTotal subgraph: {len(all_nodes)} nodes")


def demo_step3_context(graph):
    """Step 3: Convert subgraph to text context."""
    print("\n" + "=" * 70)
    print("STEP 3: Converting Subgraph to Text Context")
    print("=" * 70)

    print("""
The LLM cannot directly "see" a graph structure.
We must convert the subgraph to TEXT for the LLM to understand.

Format:
- List of entities with their types and descriptions
- List of relationships connecting them
    """)

    # Create sample context
    context = """
=== Knowledge Graph Context ===

Entities:
- OpenAI (ORGANIZATION): AI research company, creator of GPT and ChatGPT
- GPT-4 (TECHNOLOGY): Large multimodal model by OpenAI
- ChatGPT (TECHNOLOGY): Conversational AI interface for GPT models
- Sam Altman (PERSON): CEO of OpenAI
- Transformer (TECHNOLOGY): Neural network architecture

Relationships:
- OpenAI --[DEVELOPED]--> GPT-4
- OpenAI --[DEVELOPED]--> ChatGPT
- ChatGPT --[BASED_ON]--> GPT-4
- GPT-4 --[BASED_ON]--> Transformer
- Sam Altman --[CEO_OF]--> OpenAI
"""

    print("\nGenerated context:")
    print("-" * 50)
    print(context)
    print("-" * 50)


def demo_step4_generation(graph):
    """Step 4: Generate answer using LLM."""
    print("\n" + "=" * 70)
    print("STEP 4: Answer Generation with LLM")
    print("=" * 70)

    print("""
Now we prompt the LLM with:
1. The graph context (from Step 3)
2. The user's question

The LLM reasons over the graph context to produce an answer.
    """)

    # Check if Ollama is available
    if not check_ollama():
        print("\n⚠️  Skipping live LLM generation (Ollama not available)")
        print("\nExpected answer for 'What did OpenAI develop?':")
        print("─" * 50)
        print("""Based on the knowledge graph context, OpenAI developed:
1. GPT-4 - A large multimodal model
2. ChatGPT - A conversational AI interface based on GPT models

ChatGPT is built on top of GPT-4, which itself is based on
the Transformer architecture.""")
        return

    print(f"\nGenerating answer with Ollama (using {get_best_model()})...")

    context = """
Entities:
- OpenAI (ORGANIZATION): AI research company
- GPT-4 (TECHNOLOGY): Large multimodal model
- ChatGPT (TECHNOLOGY): Conversational AI interface

Relationships:
- OpenAI --[DEVELOPED]--> GPT-4
- OpenAI --[DEVELOPED]--> ChatGPT
- ChatGPT --[BASED_ON]--> GPT-4
"""

    question = "What did OpenAI develop?"

    prompt = f"""You are a helpful assistant. Answer the question using ONLY the provided context.

Context:
{context}

Question: {question}

Answer:"""

    answer = call_ollama(prompt)
    print("\n" + "─" * 50)
    print(f"Q: {question}")
    print(f"\nA: {answer}")
    print("─" * 50)


def demo_step5_compare():
    """Step 5: Compare with Vector RAG."""
    print("\n" + "=" * 70)
    print("STEP 5: GraphRAG vs Vector RAG Comparison")
    print("=" * 70)

    print("""
Consider this question:
  "Who founded the company that developed Transformer?"

┌─────────────────────────────────────────────────────────────────┐
│ VECTOR RAG Approach:                                            │
│                                                                 │
│ 1. Embed query → search for similar text chunks                │
│ 2. Might find: "Google developed the Transformer architecture" │
│ 3. But this chunk doesn't mention Google's founders!           │
│ 4. Need ANOTHER retrieval to find founders                     │
│ 5. Result: Often fails or gives incomplete answer              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ GRAPH RAG Approach:                                             │
│                                                                 │
│ 1. Find "Transformer" in graph                                 │
│ 2. Follow edge: Transformer <--[DEVELOPED]-- Google            │
│ 3. Follow edge: Google <--[FOUNDED]-- Larry Page, Sergey Brin  │
│ 4. Result: "Larry Page and Sergey Brin founded Google,         │
│           which developed the Transformer architecture."       │
└─────────────────────────────────────────────────────────────────┘

KEY INSIGHT:
  GraphRAG can follow RELATIONSHIP CHAINS that Vector RAG cannot!
    """)


def simple_retrieve(graph, query, k_hops=2):
    """
    Simple k-hop retrieval (built-in for demo simplicity).

    TEACHING NOTE:
    This is a simplified version of the retriever for the interactive demo.
    See 05_retrieval/retriever.py for the full implementation.
    """
    # Find seed entities by simple string matching
    query_lower = query.lower()
    seeds = set()

    for node in graph.nodes():
        name = graph.nodes[node].get("name", node).lower()
        if name in query_lower or node in query_lower:
            seeds.add(node)

    if not seeds:
        # Try partial matching
        for node in graph.nodes():
            name = graph.nodes[node].get("name", node).lower()
            for word in query_lower.split():
                if len(word) > 3 and word in name:
                    seeds.add(node)

    # K-hop expansion
    visited = set(seeds)
    frontier = set(seeds)

    for _ in range(k_hops):
        new_frontier = set()
        for node in frontier:
            neighbors = set(graph.successors(node)) | set(graph.predecessors(node))
            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    new_frontier.add(n)
        frontier = new_frontier
        if not frontier:
            break

    return graph.subgraph(visited).copy()


def subgraph_to_text(subgraph):
    """Convert subgraph to text context."""
    if subgraph.number_of_nodes() == 0:
        return "No relevant information found."

    lines = ["=== Knowledge Graph Context ===", "", "Entities:"]
    for node in subgraph.nodes():
        data = subgraph.nodes[node]
        name = data.get("name", node)
        ntype = data.get("type", "UNKNOWN")
        desc = data.get("description", "")
        lines.append(f"- {name} ({ntype}): {desc}")

    lines.extend(["", "Relationships:"])
    for u, v, data in subgraph.edges(data=True):
        src = subgraph.nodes[u].get("name", u)
        tgt = subgraph.nodes[v].get("name", v)
        rel = data.get("relation", "RELATED")
        lines.append(f"- {src} --[{rel}]--> {tgt}")

    return "\n".join(lines)


def demo_interactive(graph):
    """Interactive query mode."""
    print("\n" + "=" * 70)
    print("INTERACTIVE MODE: Ask Your Own Questions")
    print("=" * 70)

    if not check_ollama():
        print("\n⚠️  Ollama not available. Cannot run interactive mode.")
        return

    print("""
Try questions that require relationship reasoning:
- "Who is the CEO of OpenAI?"
- "What is ChatGPT based on?"
- "Who founded Anthropic?"
- "What did Meta develop?"
- "Who works at Google?"

Type 'quit' to exit.
    """)

    while True:
        query = input("\nYour question: ").strip()
        if query.lower() in ('quit', 'exit', 'q'):
            break

        if not query:
            continue

        # Retrieve using built-in function
        subgraph = simple_retrieve(graph, query, k_hops=2)
        context = subgraph_to_text(subgraph)

        print(f"\n[Retrieved {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges]")

        # Generate
        prompt = f"""Answer the question using ONLY the provided context.

{context}

Question: {query}

Answer:"""

        answer = call_ollama(prompt)
        print(f"\n📝 Answer: {answer}")


# =============================================================================
# Main Menu
# =============================================================================

def main():
    print_banner()

    # Create graph
    print("\n[Setup] Creating sample knowledge graph...")
    graph = create_sample_graph()
    print(f"[Setup] Graph ready: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    while True:
        print("\n" + "═" * 50)
        print("MAIN MENU")
        print("═" * 50)
        print("""
1. Step 1: Understand the Graph Structure
2. Step 2: Graph-Based Retrieval (K-Hop)
3. Step 3: Convert Subgraph to Text
4. Step 4: Generate Answer with LLM
5. Step 5: Compare with Vector RAG
6. Interactive Q&A Mode
7. Visualize Graph (requires matplotlib)
8. Run Full Pipeline Demo
0. Exit
        """)

        choice = input("Select option (0-8): ").strip()

        if choice == "0":
            print("\nGoodbye! 👋")
            break
        elif choice == "1":
            demo_step1_understand_graph(graph)
        elif choice == "2":
            demo_step2_retrieval(graph)
        elif choice == "3":
            demo_step3_context(graph)
        elif choice == "4":
            demo_step4_generation(graph)
        elif choice == "5":
            demo_step5_compare()
        elif choice == "6":
            demo_interactive(graph)
        elif choice == "7":
            try:
                import matplotlib.pyplot as plt
                import networkx as nx

                # Simple visualization
                plt.figure(figsize=(14, 10))
                pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)

                # Color by type
                colors = {
                    "PERSON": "#FF6B6B", "ORGANIZATION": "#4ECDC4",
                    "TECHNOLOGY": "#45B7D1", "CONCEPT": "#96CEB4"
                }
                node_colors = [colors.get(graph.nodes[n].get("type"), "#DFE6E9") for n in graph.nodes()]

                nx.draw(graph, pos, node_color=node_colors, node_size=800, arrows=True)
                labels = {n: graph.nodes[n].get("name", n) for n in graph.nodes()}
                nx.draw_networkx_labels(graph, pos, labels, font_size=7)

                plt.title("AI Companies Knowledge Graph")
                plt.axis('off')
                plt.tight_layout()
                plt.show()
            except ImportError:
                print("\nmatplotlib not installed. Run: pip install matplotlib")
        elif choice == "8":
            # Run all steps
            demo_step1_understand_graph(graph)
            input("\nPress Enter for next step...")
            demo_step2_retrieval(graph)
            input("\nPress Enter for next step...")
            demo_step3_context(graph)
            input("\nPress Enter for next step...")
            demo_step4_generation(graph)
            input("\nPress Enter for next step...")
            demo_step5_compare()
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
