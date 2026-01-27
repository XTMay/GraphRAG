"""
=============================================================================
GraphRAG Teaching Demo - Knowledge Graph Builder
=============================================================================

This module builds a NetworkX graph from extracted entities and relationships.

TEACHING NOTES:
---------------
1. We use NetworkX for simplicity - it's pure Python and easy to understand
2. Graph structure: Nodes = Entities, Edges = Relationships
3. Both nodes and edges can have attributes (metadata)

WHY NETWORKX?
-------------
- Pure Python, no external database needed
- Great for teaching and prototyping
- Rich algorithm library (shortest path, community detection, etc.)
- Easy visualization
- NOT for production at scale (use Neo4j, NebulaGraph for that)
"""

import networkx as nx
from typing import Optional


class KnowledgeGraphBuilder:
    """
    Builds a NetworkX knowledge graph from extracted entities and relationships.

    TEACHING NOTE:
    We use a MultiDiGraph because:
    - MultiDi: Allows multiple edges between same nodes (important!)
    - Di (Directed): Relationships have direction (A → B is different from B → A)

    Example: Two people can have multiple relationships:
      (Sam) --[WORKS_AT]--> (OpenAI)
      (Sam) --[CEO_OF]--> (OpenAI)
    """

    def __init__(self):
        # TEACHING NOTE: MultiDiGraph allows multiple edges between same node pair
        self.graph = nx.MultiDiGraph()

    def build(self, extractions: dict) -> nx.MultiDiGraph:
        """
        Build knowledge graph from extraction results.

        Args:
            extractions: Dict with 'entities' and 'relationships' lists

        Returns:
            NetworkX MultiDiGraph

        PIPELINE:
        extractions → add nodes → add edges → return graph
        """
        entities = extractions.get("entities", [])
        relationships = extractions.get("relationships", [])

        print(f"Building graph from {len(entities)} entities and {len(relationships)} relationships...")

        # Step 1: Add entity nodes
        self._add_entities(entities)

        # Step 2: Add relationship edges
        self._add_relationships(relationships)

        print(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

        return self.graph

    def _add_entities(self, entities: list):
        """
        Add entities as nodes to the graph.

        TEACHING NOTE:
        Each node has:
        - ID: normalized entity name (lowercase, for consistent matching)
        - Attributes: original name, type, description, source_doc
        """
        for entity in entities:
            name = entity.get("name", "")
            if not name:
                continue

            # TEACHING NOTE: Use lowercase ID for matching, but keep original name
            node_id = name.lower()

            # Add node with attributes
            # TEACHING NOTE: Node attributes are like a dictionary attached to each node
            self.graph.add_node(
                node_id,
                name=name,  # Original name (for display)
                type=entity.get("type", "UNKNOWN"),
                description=entity.get("description", ""),
                source_doc=entity.get("source_doc", "")
            )

    def _add_relationships(self, relationships: list):
        """
        Add relationships as edges to the graph.

        TEACHING NOTE:
        Each edge has:
        - Source: normalized source entity name
        - Target: normalized target entity name
        - Key: relation type (allows multiple edges of different types)
        - Attributes: relation type, description, source_doc
        """
        for rel in relationships:
            source = rel.get("source", "").lower()
            target = rel.get("target", "").lower()
            relation = rel.get("relation", "RELATED_TO")

            if not source or not target:
                continue

            # TEACHING NOTE: Check that both nodes exist before adding edge
            # This prevents dangling edges
            if source not in self.graph or target not in self.graph:
                print(f"  Warning: Skipping edge, node not found: {source} or {target}")
                continue

            # Add edge with attributes
            self.graph.add_edge(
                source,
                target,
                key=relation,  # This is the edge "type" - allows multiple edges
                relation=relation,
                description=rel.get("description", ""),
                source_doc=rel.get("source_doc", "")
            )

    def get_node(self, name: str) -> Optional[dict]:
        """
        Get node attributes by name.

        TEACHING NOTE:
        Node lookup is O(1) in NetworkX using the node ID.
        """
        node_id = name.lower()
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def get_neighbors(self, name: str, direction: str = "both") -> list:
        """
        Get neighboring nodes.

        Args:
            name: Entity name
            direction: "in" (predecessors), "out" (successors), or "both"

        TEACHING NOTE:
        In a directed graph:
        - Successors: nodes this node points TO (outgoing edges)
        - Predecessors: nodes that point TO this node (incoming edges)
        """
        node_id = name.lower()
        if node_id not in self.graph:
            return []

        neighbors = set()

        if direction in ("out", "both"):
            neighbors.update(self.graph.successors(node_id))

        if direction in ("in", "both"):
            neighbors.update(self.graph.predecessors(node_id))

        return list(neighbors)

    def get_edges_for_node(self, name: str) -> list:
        """
        Get all edges connected to a node.

        Returns list of (source, target, relation, attributes) tuples.
        """
        node_id = name.lower()
        if node_id not in self.graph:
            return []

        edges = []

        # Outgoing edges
        for target in self.graph.successors(node_id):
            for key, attrs in self.graph[node_id][target].items():
                edges.append({
                    "source": node_id,
                    "target": target,
                    "relation": attrs.get("relation", key),
                    "description": attrs.get("description", "")
                })

        # Incoming edges
        for source in self.graph.predecessors(node_id):
            for key, attrs in self.graph[source][node_id].items():
                edges.append({
                    "source": source,
                    "target": node_id,
                    "relation": attrs.get("relation", key),
                    "description": attrs.get("description", "")
                })

        return edges

    def get_stats(self) -> dict:
        """
        Get graph statistics.

        TEACHING NOTE:
        Useful for sanity checking the graph:
        - Too few nodes? Extraction might have failed
        - Too many edges? Might have noise
        - No edges? Relationship extraction failed
        """
        # Count nodes by type
        type_counts = {}
        for node_id in self.graph.nodes():
            node_type = self.graph.nodes[node_id].get("type", "UNKNOWN")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        # Count edges by relation type
        relation_counts = {}
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get("relation", "UNKNOWN")
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1

        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "node_types": type_counts,
            "relation_types": relation_counts,
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }

    def save(self, filepath: str):
        """Save graph to file (GraphML format)."""
        nx.write_graphml(self.graph, filepath)
        print(f"Graph saved to {filepath}")

    def load(self, filepath: str):
        """Load graph from file."""
        self.graph = nx.read_graphml(filepath)
        print(f"Graph loaded from {filepath}")


# =============================================================================
# Demo / Test
# =============================================================================

if __name__ == "__main__":
    """
    Demo: Build a small knowledge graph manually.
    """

    print("=" * 60)
    print("Knowledge Graph Builder Demo")
    print("=" * 60)

    # Sample extraction result
    extractions = {
        "entities": [
            {"name": "OpenAI", "type": "ORGANIZATION", "description": "AI research company"},
            {"name": "Sam Altman", "type": "PERSON", "description": "CEO of OpenAI"},
            {"name": "GPT-4", "type": "TECHNOLOGY", "description": "Large language model"},
            {"name": "ChatGPT", "type": "TECHNOLOGY", "description": "Conversational AI"},
            {"name": "San Francisco", "type": "LOCATION", "description": "City in California"}
        ],
        "relationships": [
            {"source": "Sam Altman", "relation": "CEO_OF", "target": "OpenAI"},
            {"source": "OpenAI", "relation": "DEVELOPED", "target": "GPT-4"},
            {"source": "OpenAI", "relation": "DEVELOPED", "target": "ChatGPT"},
            {"source": "ChatGPT", "relation": "BASED_ON", "target": "GPT-4"},
            {"source": "OpenAI", "relation": "LOCATED_IN", "target": "San Francisco"}
        ]
    }

    # Build graph
    builder = KnowledgeGraphBuilder()
    graph = builder.build(extractions)

    # Print stats
    print("\nGraph Statistics:")
    stats = builder.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test queries
    print("\nNeighbors of 'OpenAI':")
    for neighbor in builder.get_neighbors("OpenAI"):
        print(f"  - {neighbor}")

    print("\nEdges connected to 'OpenAI':")
    for edge in builder.get_edges_for_node("OpenAI"):
        print(f"  - {edge['source']} --[{edge['relation']}]--> {edge['target']}")
