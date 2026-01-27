"""
=============================================================================
GraphRAG Teaching Demo - Graph Visualizer
=============================================================================

This module provides visualization for knowledge graphs.

TEACHING NOTES:
---------------
1. Visualization is crucial for debugging and understanding
2. We provide two options:
   - matplotlib: Static images, good for reports
   - pyvis: Interactive HTML, good for exploration

WHY VISUALIZE?
--------------
- Verify extraction quality (are relationships correct?)
- Understand graph structure (clusters, hubs, isolated nodes)
- Debug retrieval (did we get the right subgraph?)
- Present results to stakeholders
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional, Set


# Color mapping for entity types
ENTITY_COLORS = {
    "PERSON": "#FF6B6B",        # Red
    "ORGANIZATION": "#4ECDC4",  # Teal
    "TECHNOLOGY": "#45B7D1",    # Blue
    "LOCATION": "#96CEB4",      # Green
    "DATE": "#FFEAA7",          # Yellow
    "UNKNOWN": "#DFE6E9"        # Gray
}


def visualize_graph_matplotlib(
    graph: nx.MultiDiGraph,
    title: str = "Knowledge Graph",
    figsize: tuple = (14, 10),
    highlight_nodes: Optional[Set[str]] = None,
    save_path: Optional[str] = None
):
    """
    Visualize knowledge graph using matplotlib.

    Args:
        graph: NetworkX graph to visualize
        title: Plot title
        figsize: Figure size (width, height)
        highlight_nodes: Optional set of node IDs to highlight
        save_path: Optional path to save the figure

    TEACHING NOTE:
    This creates a static visualization. Good for:
    - Documentation
    - Reports
    - Quick debugging
    """

    if graph.number_of_nodes() == 0:
        print("Graph is empty, nothing to visualize")
        return

    plt.figure(figsize=figsize)

    # Layout algorithm
    # TEACHING NOTE: Different layouts for different purposes:
    # - spring_layout: General purpose, shows clustering
    # - kamada_kawai_layout: More uniform spacing
    # - circular_layout: Good for small graphs
    pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)

    # Prepare node colors based on type
    node_colors = []
    for node in graph.nodes():
        node_type = graph.nodes[node].get("type", "UNKNOWN")
        color = ENTITY_COLORS.get(node_type, ENTITY_COLORS["UNKNOWN"])

        # Highlight specific nodes if requested
        if highlight_nodes and node in highlight_nodes:
            color = "#FFD700"  # Gold for highlighted nodes

        node_colors.append(color)

    # Prepare node sizes based on degree (more connections = bigger)
    # TEACHING NOTE: Node degree = number of edges connected to it
    # Hubs (highly connected nodes) appear larger
    degrees = dict(graph.degree())
    node_sizes = [300 + degrees[node] * 100 for node in graph.nodes()]

    # Draw nodes
    nx.draw_networkx_nodes(
        graph, pos,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9
    )

    # Draw edges
    # TEACHING NOTE: We use different styles for different relation types
    nx.draw_networkx_edges(
        graph, pos,
        edge_color='#888888',
        arrows=True,
        arrowsize=15,
        alpha=0.6,
        connectionstyle="arc3,rad=0.1"  # Curved edges for clarity
    )

    # Draw labels
    # Use original names (not lowercase IDs) for display
    labels = {node: graph.nodes[node].get("name", node) for node in graph.nodes()}
    nx.draw_networkx_labels(
        graph, pos,
        labels=labels,
        font_size=8,
        font_weight='bold'
    )

    # Draw edge labels (relationship types)
    edge_labels = {}
    for u, v, data in graph.edges(data=True):
        relation = data.get("relation", "")
        # TEACHING NOTE: For multigraph, there might be multiple edges
        # We concatenate them or show just one
        if (u, v) in edge_labels:
            edge_labels[(u, v)] += f"\n{relation}"
        else:
            edge_labels[(u, v)] = relation

    nx.draw_networkx_edge_labels(
        graph, pos,
        edge_labels=edge_labels,
        font_size=6,
        font_color='#555555'
    )

    # Legend for entity types
    legend_elements = []
    for entity_type, color in ENTITY_COLORS.items():
        if entity_type == "UNKNOWN":
            continue
        legend_elements.append(
            plt.scatter([], [], c=color, s=100, label=entity_type)
        )
    plt.legend(handles=legend_elements, loc='upper left', fontsize=8)

    plt.title(title, fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Graph saved to {save_path}")

    plt.show()


def visualize_graph_pyvis(
    graph: nx.MultiDiGraph,
    title: str = "Knowledge Graph",
    output_file: str = "graph.html",
    height: str = "800px",
    width: str = "100%"
):
    """
    Create interactive HTML visualization using pyvis.

    TEACHING NOTE:
    pyvis creates an interactive graph you can:
    - Drag nodes around
    - Zoom in/out
    - Click to see node details
    - Filter by node type

    Great for exploration and demos!
    """

    try:
        from pyvis.network import Network
    except ImportError:
        print("pyvis not installed. Install with: pip install pyvis")
        print("Falling back to matplotlib visualization...")
        visualize_graph_matplotlib(graph, title)
        return

    # Create pyvis network
    net = Network(height=height, width=width, directed=True, notebook=False)

    # Configure physics
    # TEACHING NOTE: Physics simulation makes the graph "settle" nicely
    net.set_options("""
    var options = {
      "nodes": {
        "font": {"size": 14}
      },
      "edges": {
        "arrows": {"to": {"enabled": true}},
        "font": {"size": 10},
        "smooth": {"type": "curvedCW"}
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "springLength": 100
        },
        "solver": "forceAtlas2Based"
      }
    }
    """)

    # Add nodes
    for node in graph.nodes():
        node_data = graph.nodes[node]
        node_type = node_data.get("type", "UNKNOWN")
        name = node_data.get("name", node)
        description = node_data.get("description", "")

        color = ENTITY_COLORS.get(node_type, ENTITY_COLORS["UNKNOWN"])

        # Node hover text
        title = f"""
        <b>{name}</b><br>
        Type: {node_type}<br>
        Description: {description}
        """

        net.add_node(
            node,
            label=name,
            title=title,
            color=color,
            size=20 + graph.degree(node) * 5
        )

    # Add edges
    for u, v, data in graph.edges(data=True):
        relation = data.get("relation", "RELATED")
        description = data.get("description", "")

        net.add_edge(
            u, v,
            label=relation,
            title=f"{relation}: {description}"
        )

    # Save to HTML
    net.save_graph(output_file)
    print(f"Interactive graph saved to {output_file}")
    print(f"Open in browser to explore!")


def visualize_subgraph(
    full_graph: nx.MultiDiGraph,
    subgraph_nodes: Set[str],
    title: str = "Retrieved Subgraph",
    save_path: Optional[str] = None
):
    """
    Visualize a subgraph with context from the full graph.

    TEACHING NOTE:
    Shows the retrieved subgraph highlighted within the context of
    the full graph. Useful for understanding what was retrieved.
    """

    # Create subgraph
    subgraph = full_graph.subgraph(subgraph_nodes).copy()

    # Visualize with highlighted nodes
    visualize_graph_matplotlib(
        full_graph,
        title=f"{title} (highlighted in gold)",
        highlight_nodes=subgraph_nodes,
        save_path=save_path
    )


def print_graph_summary(graph: nx.MultiDiGraph):
    """
    Print a text summary of the graph.

    TEACHING NOTE:
    Sometimes a simple text summary is more useful than visualization,
    especially for large graphs or automated reports.
    """

    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH SUMMARY")
    print("=" * 60)

    print(f"\nNodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")

    # Group nodes by type
    print("\nNodes by Type:")
    type_groups = {}
    for node in graph.nodes():
        node_type = graph.nodes[node].get("type", "UNKNOWN")
        if node_type not in type_groups:
            type_groups[node_type] = []
        type_groups[node_type].append(graph.nodes[node].get("name", node))

    for node_type, nodes in sorted(type_groups.items()):
        print(f"\n  {node_type} ({len(nodes)}):")
        for name in sorted(nodes)[:10]:  # Show max 10 per type
            print(f"    - {name}")
        if len(nodes) > 10:
            print(f"    ... and {len(nodes) - 10} more")

    # List all relationships
    print("\nRelationships:")
    for u, v, data in list(graph.edges(data=True))[:20]:
        source_name = graph.nodes[u].get("name", u)
        target_name = graph.nodes[v].get("name", v)
        relation = data.get("relation", "RELATED")
        print(f"  {source_name} --[{relation}]--> {target_name}")

    if graph.number_of_edges() > 20:
        print(f"  ... and {graph.number_of_edges() - 20} more relationships")


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    """Demo visualization with a sample graph."""

    print("=" * 60)
    print("Graph Visualizer Demo")
    print("=" * 60)

    # Create a sample graph
    G = nx.MultiDiGraph()

    # Add nodes
    nodes = [
        ("openai", {"name": "OpenAI", "type": "ORGANIZATION"}),
        ("sam altman", {"name": "Sam Altman", "type": "PERSON"}),
        ("gpt-4", {"name": "GPT-4", "type": "TECHNOLOGY"}),
        ("chatgpt", {"name": "ChatGPT", "type": "TECHNOLOGY"}),
        ("google", {"name": "Google", "type": "ORGANIZATION"}),
        ("transformer", {"name": "Transformer", "type": "TECHNOLOGY"}),
        ("san francisco", {"name": "San Francisco", "type": "LOCATION"})
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
        ("openai", "san francisco", "LOCATED_IN")
    ]

    for source, target, relation in edges:
        G.add_edge(source, target, key=relation, relation=relation)

    # Print summary
    print_graph_summary(G)

    # Visualize
    print("\nGenerating visualization...")
    visualize_graph_matplotlib(G, title="Sample Knowledge Graph")

    # Try pyvis
    print("\nGenerating interactive visualization...")
    visualize_graph_pyvis(G, output_file="sample_graph.html")
