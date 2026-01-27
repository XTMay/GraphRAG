"""
=============================================================================
GraphRAG Teaching Demo - Graph Retriever
=============================================================================

This module implements graph-based retrieval for GraphRAG.

TEACHING NOTES:
---------------
1. Unlike vector RAG (similarity search), we traverse the graph structure
2. K-hop retrieval: Start from seed nodes, expand K edges outward
3. The retrieved subgraph becomes context for the LLM

KEY CONCEPT: K-hop Retrieval
----------------------------
K=1: Get direct neighbors only
K=2: Get neighbors + neighbors-of-neighbors
K=3: Usually too much (retrieves most of a small graph)

COMMON MISTAKE: Setting K too high retrieves irrelevant nodes!
"""

import networkx as nx
from typing import List, Set, Optional
import requests


class GraphRetriever:
    """
    Retrieves relevant subgraphs from a knowledge graph.

    TEACHING NOTE:
    The retrieval process:
    1. Identify seed entities from the query
    2. Find those entities in the graph
    3. Expand to K-hop neighbors
    4. Return the subgraph
    """

    def __init__(self, graph: nx.MultiDiGraph, llm_base_url: str = "http://localhost:11434"):
        """
        Args:
            graph: The knowledge graph to retrieve from
            llm_base_url: URL for Ollama API (used for entity matching)
        """
        self.graph = graph
        self.llm_base_url = llm_base_url

    def retrieve(
        self,
        query: str,
        k_hops: int = 2,
        max_nodes: int = 20,
        use_llm_matching: bool = True
    ) -> nx.MultiDiGraph:
        """
        Retrieve a relevant subgraph for the query.

        Args:
            query: The user's question
            k_hops: Number of hops to expand from seed nodes
            max_nodes: Maximum nodes in returned subgraph
            use_llm_matching: Whether to use LLM for entity matching

        Returns:
            NetworkX subgraph containing relevant nodes and edges

        TEACHING NOTE:
        This is the core retrieval function. The quality of retrieval
        determines the quality of the final answer!
        """

        print(f"\n[Retriever] Processing query: '{query}'")

        # Step 1: Find seed entities
        # TEACHING NOTE: Seeds are the starting points for graph traversal
        seed_entities = self._find_seed_entities(query, use_llm_matching)
        print(f"[Retriever] Found {len(seed_entities)} seed entities: {seed_entities}")

        if not seed_entities:
            print("[Retriever] Warning: No seed entities found!")
            return nx.MultiDiGraph()  # Return empty graph

        # Step 2: Expand K hops from seeds
        # TEACHING NOTE: This is where graph structure shines!
        # We follow relationships to find connected information
        expanded_nodes = self._expand_k_hops(seed_entities, k_hops)
        print(f"[Retriever] Expanded to {len(expanded_nodes)} nodes")

        # Step 3: Limit size if necessary
        # TEACHING NOTE: Too many nodes = too much context = LLM confusion
        if len(expanded_nodes) > max_nodes:
            expanded_nodes = self._rank_and_limit(expanded_nodes, seed_entities, max_nodes)
            print(f"[Retriever] Limited to {len(expanded_nodes)} most relevant nodes")

        # Step 4: Extract subgraph
        subgraph = self.graph.subgraph(expanded_nodes).copy()

        print(f"[Retriever] Final subgraph: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")

        return subgraph

    def _find_seed_entities(self, query: str, use_llm: bool = True) -> Set[str]:
        """
        Find entities in the query that match nodes in the graph.

        TEACHING NOTE:
        Two approaches:
        1. Simple: Substring matching (fast but imprecise)
        2. LLM-based: Ask LLM to identify relevant entities (slower but smarter)

        STUDENT EXERCISE: Implement embedding-based matching!
        """

        if use_llm:
            return self._find_seeds_with_llm(query)
        else:
            return self._find_seeds_simple(query)

    def _find_seeds_simple(self, query: str) -> Set[str]:
        """
        Simple substring matching for seed finding.

        TEACHING NOTE:
        This is fast but has issues:
        - "gpt" matches "gpt-4" but also "egypt" if you're not careful
        - Case sensitivity issues
        - No understanding of synonyms
        """

        query_lower = query.lower()
        seeds = set()

        for node in self.graph.nodes():
            # Get the display name
            name = self.graph.nodes[node].get("name", node).lower()

            # Check if entity name appears in query
            # TEACHING NOTE: Longer names are checked first to avoid
            # matching "AI" when "OpenAI" is in the query
            if name in query_lower or node in query_lower:
                seeds.add(node)

        return seeds

    def _find_seeds_with_llm(self, query: str) -> Set[str]:
        """
        Use LLM to identify relevant entities from the query.

        TEACHING NOTE:
        This is more accurate but:
        - Adds latency (LLM call)
        - Costs money (if using paid API)
        - Can fail if LLM doesn't follow instructions
        """

        # Get all entity names from graph
        entities_list = []
        for node in self.graph.nodes():
            name = self.graph.nodes[node].get("name", node)
            node_type = self.graph.nodes[node].get("type", "UNKNOWN")
            entities_list.append(f"- {name} ({node_type})")

        entities_text = "\n".join(entities_list)

        # Create prompt
        prompt = f"""Given a question and a list of entities from a knowledge graph,
identify which entities are DIRECTLY mentioned or relevant to the question.

Question: {query}

Available Entities:
{entities_text}

Return ONLY a JSON list of relevant entity names (maximum 5).
Example: ["OpenAI", "GPT-4"]

Relevant Entities (JSON list only):
"""

        try:
            # Call Ollama
            response = requests.post(
                f"{self.llm_base_url}/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "temperature": 0,
                    "stream": False
                },
                timeout=60
            )
            result = response.json()["response"]

            # Parse JSON from response
            import json
            import re

            # Try to extract JSON list
            match = re.search(r'\[.*?\]', result, re.DOTALL)
            if match:
                entities = json.loads(match.group())
                # Convert to node IDs (lowercase)
                return {e.lower() for e in entities if e.lower() in self.graph}

        except Exception as e:
            print(f"[Retriever] LLM matching failed: {e}")
            print("[Retriever] Falling back to simple matching")

        # Fallback to simple matching
        return self._find_seeds_simple(query)

    def _expand_k_hops(self, seeds: Set[str], k: int) -> Set[str]:
        """
        Expand from seed nodes by K hops.

        TEACHING NOTE:
        K-hop expansion using BFS (Breadth-First Search):
        - K=0: Just the seeds
        - K=1: Seeds + direct neighbors
        - K=2: Seeds + neighbors + neighbors-of-neighbors

        WHY BFS? Because we want nodes CLOSEST to seeds first.
        """

        visited = set(seeds)
        frontier = set(seeds)

        for hop in range(k):
            new_frontier = set()

            for node in frontier:
                # Get all neighbors (both directions)
                neighbors = set(self.graph.successors(node))
                neighbors.update(self.graph.predecessors(node))

                # Add unvisited neighbors to new frontier
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        new_frontier.add(neighbor)

            frontier = new_frontier

            # TEACHING NOTE: Early termination if no new nodes found
            if not frontier:
                break

        return visited

    def _rank_and_limit(self, nodes: Set[str], seeds: Set[str], max_nodes: int) -> Set[str]:
        """
        Rank nodes by relevance and keep top-k.

        TEACHING NOTE:
        When we have too many nodes, we need to prioritize. Ranking criteria:
        1. Seed nodes always included
        2. Closer to seeds = higher rank
        3. Higher degree (more connections) = higher rank

        STUDENT EXERCISE: Implement PageRank-based ranking!
        """

        # Always include seeds
        result = set(seeds)

        # Calculate distance from nearest seed
        distances = {}
        for node in nodes:
            if node in seeds:
                distances[node] = 0
            else:
                # Find shortest path to any seed
                min_dist = float('inf')
                for seed in seeds:
                    try:
                        # Try both directions
                        try:
                            d1 = nx.shortest_path_length(self.graph, seed, node)
                        except nx.NetworkXNoPath:
                            d1 = float('inf')
                        try:
                            d2 = nx.shortest_path_length(self.graph, node, seed)
                        except nx.NetworkXNoPath:
                            d2 = float('inf')
                        min_dist = min(min_dist, d1, d2)
                    except:
                        pass
                distances[node] = min_dist

        # Rank by: (distance, -degree)
        # Lower distance = better, higher degree = better
        ranked = sorted(
            nodes - seeds,
            key=lambda n: (distances.get(n, float('inf')), -self.graph.degree(n))
        )

        # Add top nodes until we reach max
        for node in ranked:
            if len(result) >= max_nodes:
                break
            result.add(node)

        return result

    def subgraph_to_text(self, subgraph: nx.MultiDiGraph) -> str:
        """
        Convert subgraph to natural language text for LLM context.

        TEACHING NOTE:
        The LLM doesn't understand graph structure directly.
        We need to convert it to text. Options:
        1. List of facts (what we do here)
        2. Natural language paragraph
        3. Structured format (JSON)

        STUDENT EXERCISE: Try different formats and compare!
        """

        if subgraph.number_of_nodes() == 0:
            return "No relevant information found in the knowledge graph."

        lines = []
        lines.append("=== Knowledge Graph Context ===")
        lines.append("")

        # List entities
        lines.append("Entities:")
        for node in subgraph.nodes():
            data = subgraph.nodes[node]
            name = data.get("name", node)
            node_type = data.get("type", "UNKNOWN")
            desc = data.get("description", "")
            lines.append(f"- {name} ({node_type}): {desc}")

        lines.append("")

        # List relationships
        lines.append("Relationships:")
        for u, v, data in subgraph.edges(data=True):
            source_name = subgraph.nodes[u].get("name", u)
            target_name = subgraph.nodes[v].get("name", v)
            relation = data.get("relation", "RELATED")
            desc = data.get("description", "")
            lines.append(f"- {source_name} --[{relation}]--> {target_name}")
            if desc:
                lines.append(f"  ({desc})")

        return "\n".join(lines)


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    """Demo retrieval with a sample graph."""

    print("=" * 60)
    print("Graph Retriever Demo")
    print("=" * 60)

    # Create a sample graph
    G = nx.MultiDiGraph()

    # Add nodes
    nodes = [
        ("openai", {"name": "OpenAI", "type": "ORGANIZATION", "description": "AI research company"}),
        ("sam altman", {"name": "Sam Altman", "type": "PERSON", "description": "CEO of OpenAI"}),
        ("gpt-4", {"name": "GPT-4", "type": "TECHNOLOGY", "description": "Large language model"}),
        ("chatgpt", {"name": "ChatGPT", "type": "TECHNOLOGY", "description": "Conversational AI"}),
        ("google", {"name": "Google", "type": "ORGANIZATION", "description": "Technology company"}),
        ("transformer", {"name": "Transformer", "type": "TECHNOLOGY", "description": "Neural network architecture"}),
        ("bert", {"name": "BERT", "type": "TECHNOLOGY", "description": "Bidirectional encoder model"}),
    ]

    for node_id, attrs in nodes:
        G.add_node(node_id, **attrs)

    # Add edges
    edges = [
        ("sam altman", "openai", "CEO_OF"),
        ("openai", "gpt-4", "DEVELOPED"),
        ("openai", "chatgpt", "DEVELOPED"),
        ("chatgpt", "gpt-4", "BASED_ON"),
        ("gpt-4", "transformer", "BASED_ON"),
        ("google", "transformer", "DEVELOPED"),
        ("google", "bert", "DEVELOPED"),
        ("bert", "transformer", "BASED_ON"),
    ]

    for source, target, relation in edges:
        G.add_edge(source, target, key=relation, relation=relation)

    # Test retrieval
    retriever = GraphRetriever(G)

    # Test query
    query = "What did OpenAI develop?"

    print(f"\nQuery: {query}")
    print("-" * 40)

    # Retrieve with simple matching (no LLM)
    subgraph = retriever.retrieve(query, k_hops=2, use_llm_matching=False)

    # Convert to text
    context = retriever.subgraph_to_text(subgraph)
    print("\nRetrieved Context:")
    print(context)
