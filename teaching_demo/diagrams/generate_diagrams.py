#!/usr/bin/env python3
"""
Generate GraphRAG architecture diagrams using matplotlib.
Run: python generate_diagrams.py
Output: PNG files in current directory
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def create_pipeline_diagram():
    """Create the main GraphRAG pipeline diagram."""

    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_aspect('equal')

    # Title
    ax.text(8, 9.5, 'GraphRAG Pipeline Architecture', fontsize=20, fontweight='bold',
            ha='center', va='center')

    # === INDEXING PHASE ===
    # Background box
    indexing_box = FancyBboxPatch((0.5, 5.5), 7, 3.5, boxstyle="round,pad=0.1",
                                   facecolor='#e3f2fd', edgecolor='#1976d2', linewidth=2)
    ax.add_patch(indexing_box)
    ax.text(4, 8.7, 'INDEXING PHASE (Offline)', fontsize=12, fontweight='bold',
            ha='center', color='#1976d2')

    # Documents
    doc_box = FancyBboxPatch((1, 6.5), 1.5, 1.2, boxstyle="round,pad=0.05",
                              facecolor='#fff9c4', edgecolor='#f57f17', linewidth=1.5)
    ax.add_patch(doc_box)
    ax.text(1.75, 7.1, '📄\nDocuments', fontsize=9, ha='center', va='center')

    # LLM Extraction
    llm_box = FancyBboxPatch((3.5, 6.5), 1.5, 1.2, boxstyle="round,pad=0.05",
                              facecolor='#f3e5f5', edgecolor='#7b1fa2', linewidth=1.5)
    ax.add_patch(llm_box)
    ax.text(4.25, 7.1, '🤖\nLLM\nExtraction', fontsize=9, ha='center', va='center')

    # Knowledge Graph
    kg_box = FancyBboxPatch((6, 6.5), 1.5, 1.2, boxstyle="round,pad=0.05",
                             facecolor='#e8f5e9', edgecolor='#388e3c', linewidth=1.5)
    ax.add_patch(kg_box)
    ax.text(6.75, 7.1, '🕸️\nKnowledge\nGraph', fontsize=9, ha='center', va='center')

    # Arrows in indexing
    ax.annotate('', xy=(3.4, 7.1), xytext=(2.6, 7.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(5.9, 7.1), xytext=(5.1, 7.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))

    # === QUERY PHASE ===
    # Background box
    query_box = FancyBboxPatch((0.5, 0.8), 15, 4.2, boxstyle="round,pad=0.1",
                                facecolor='#fce4ec', edgecolor='#c2185b', linewidth=2)
    ax.add_patch(query_box)
    ax.text(8, 4.7, 'QUERY PHASE (Online)', fontsize=12, fontweight='bold',
            ha='center', color='#c2185b')

    # Query
    q_box = FancyBboxPatch((1, 2.5), 1.8, 1.2, boxstyle="round,pad=0.05",
                            facecolor='#e1f5fe', edgecolor='#0288d1', linewidth=1.5)
    ax.add_patch(q_box)
    ax.text(1.9, 3.1, '❓\nUser Query', fontsize=9, ha='center', va='center')

    # Entity Matching
    em_box = FancyBboxPatch((4, 2.5), 1.8, 1.2, boxstyle="round,pad=0.05",
                             facecolor='#fff3e0', edgecolor='#ef6c00', linewidth=1.5)
    ax.add_patch(em_box)
    ax.text(4.9, 3.1, '🎯\nEntity\nMatching', fontsize=9, ha='center', va='center')

    # K-Hop Retrieval
    kh_box = FancyBboxPatch((7, 2.5), 1.8, 1.2, boxstyle="round,pad=0.05",
                             facecolor='#e0f7fa', edgecolor='#00796b', linewidth=1.5)
    ax.add_patch(kh_box)
    ax.text(7.9, 3.1, '🔗\nK-Hop\nRetrieval', fontsize=9, ha='center', va='center')

    # Context
    ctx_box = FancyBboxPatch((10, 2.5), 1.8, 1.2, boxstyle="round,pad=0.05",
                              facecolor='#f5f5f5', edgecolor='#616161', linewidth=1.5)
    ax.add_patch(ctx_box)
    ax.text(10.9, 3.1, '📝\nContext\nText', fontsize=9, ha='center', va='center')

    # LLM Generation
    gen_box = FancyBboxPatch((13, 2.5), 1.8, 1.2, boxstyle="round,pad=0.05",
                              facecolor='#f3e5f5', edgecolor='#7b1fa2', linewidth=1.5)
    ax.add_patch(gen_box)
    ax.text(13.9, 3.1, '🤖\nLLM\nGenerate', fontsize=9, ha='center', va='center')

    # Answer
    ans_box = FancyBboxPatch((13, 1), 1.8, 1, boxstyle="round,pad=0.05",
                              facecolor='#c8e6c9', edgecolor='#2e7d32', linewidth=1.5)
    ax.add_patch(ans_box)
    ax.text(13.9, 1.5, '✅ Answer', fontsize=10, ha='center', va='center', fontweight='bold')

    # Arrows in query phase
    ax.annotate('', xy=(3.9, 3.1), xytext=(2.9, 3.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(6.9, 3.1), xytext=(5.9, 3.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(9.9, 3.1), xytext=(8.9, 3.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(12.9, 3.1), xytext=(11.9, 3.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))
    ax.annotate('', xy=(13.9, 2.4), xytext=(13.9, 2.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))

    # Connection from Knowledge Graph to Retrieval
    ax.annotate('', xy=(7.9, 3.8), xytext=(6.75, 6.4),
                arrowprops=dict(arrowstyle='->', color='#388e3c', lw=2,
                               connectionstyle='arc3,rad=-0.2'))

    plt.tight_layout()
    plt.savefig('graphrag_pipeline.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("Saved: graphrag_pipeline.png")
    plt.close()


def create_comparison_diagram():
    """Create Vector RAG vs Graph RAG comparison diagram."""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    for ax in [ax1, ax2]:
        ax.set_xlim(0, 8)
        ax.set_ylim(0, 10)
        ax.axis('off')

    # === VECTOR RAG ===
    ax1.set_title('Vector RAG', fontsize=16, fontweight='bold', color='#ef6c00', pad=20)

    # Draw flow
    boxes = [
        (1, 8, 'Documents', '#fff9c4'),
        (1, 6.5, 'Chunks', '#e3f2fd'),
        (1, 5, 'Embeddings', '#f3e5f5'),
        (1, 3.5, 'Vector DB', '#e8f5e9'),
        (5, 8, 'Query', '#e1f5fe'),
        (5, 6.5, 'Similarity\nSearch', '#fff3e0'),
        (5, 5, 'Top-K\nChunks', '#f5f5f5'),
        (5, 3.5, 'LLM', '#f3e5f5'),
        (5, 2, 'Answer', '#c8e6c9'),
    ]

    for x, y, text, color in boxes:
        box = FancyBboxPatch((x, y-0.4), 2, 0.8, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='#666', linewidth=1.5)
        ax1.add_patch(box)
        ax1.text(x+1, y, text, fontsize=10, ha='center', va='center')

    # Arrows
    arrows = [(2, 7.5, 2, 7.1), (2, 6, 2, 5.6), (2, 4.5, 2, 4.1),
              (6, 7.5, 6, 7.1), (6, 6, 6, 5.6), (6, 4.5, 6, 4.1), (6, 3, 6, 2.6)]
    for x1, y1, x2, y2 in arrows:
        ax1.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    ax1.annotate('', xy=(4.9, 6.5), xytext=(3.1, 3.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5,
                               connectionstyle='arc3,rad=0.3'))

    # Limitation text
    ax1.text(4, 0.8, '❌ Chunks are INDEPENDENT\n   No connections between facts!',
             fontsize=10, ha='center', color='#d32f2f', style='italic')

    # === GRAPH RAG ===
    ax2.set_title('Graph RAG', fontsize=16, fontweight='bold', color='#388e3c', pad=20)

    boxes = [
        (1, 8, 'Documents', '#fff9c4'),
        (1, 6.5, 'LLM\nExtraction', '#f3e5f5'),
        (1, 5, 'Knowledge\nGraph', '#e8f5e9'),
        (5, 8, 'Query', '#e1f5fe'),
        (5, 6.5, 'Entity\nMatch', '#fff3e0'),
        (5, 5, 'K-Hop\nTraversal', '#e0f7fa'),
        (5, 3.5, 'LLM', '#f3e5f5'),
        (5, 2, 'Answer', '#c8e6c9'),
    ]

    for x, y, text, color in boxes:
        box = FancyBboxPatch((x, y-0.4), 2, 0.8, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='#666', linewidth=1.5)
        ax2.add_patch(box)
        ax2.text(x+1, y, text, fontsize=10, ha='center', va='center')

    # Arrows
    arrows = [(2, 7.5, 2, 7.1), (2, 6, 2, 5.6),
              (6, 7.5, 6, 7.1), (6, 6, 6, 5.6), (6, 4.5, 6, 4.1), (6, 3, 6, 2.6)]
    for x1, y1, x2, y2 in arrows:
        ax2.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    ax2.annotate('', xy=(4.9, 5), xytext=(3.1, 5),
                arrowprops=dict(arrowstyle='->', color='#388e3c', lw=2))

    # Advantage text
    ax2.text(4, 0.8, '✅ Follows RELATIONSHIPS\n   Multi-hop reasoning works!',
             fontsize=10, ha='center', color='#2e7d32', style='italic')

    plt.tight_layout()
    plt.savefig('vector_vs_graph_rag.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("Saved: vector_vs_graph_rag.png")
    plt.close()


def create_khop_diagram():
    """Create K-hop expansion visualization."""

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax in axes:
        ax.set_xlim(-3, 3)
        ax.set_ylim(-2.5, 2.5)
        ax.axis('off')
        ax.set_aspect('equal')

    # K=0
    ax = axes[0]
    ax.set_title('K = 0 (Seed Only)', fontsize=12, fontweight='bold')
    circle = plt.Circle((0, 0), 0.5, color='#4caf50', ec='#2e7d32', lw=2)
    ax.add_patch(circle)
    ax.text(0, 0, 'OpenAI', fontsize=9, ha='center', va='center', color='white', fontweight='bold')

    # K=1
    ax = axes[1]
    ax.set_title('K = 1 (Direct Neighbors)', fontsize=12, fontweight='bold')

    # Center
    circle = plt.Circle((0, 0), 0.5, color='#4caf50', ec='#2e7d32', lw=2)
    ax.add_patch(circle)
    ax.text(0, 0, 'OpenAI', fontsize=8, ha='center', va='center', color='white', fontweight='bold')

    # Neighbors
    neighbors = [
        (1.5, 1, 'GPT-4', '#2196f3'),
        (1.5, -1, 'ChatGPT', '#2196f3'),
        (-1.5, 0, 'Sam\nAltman', '#ff9800'),
    ]
    for x, y, text, color in neighbors:
        circle = plt.Circle((x, y), 0.4, color=color, ec='#666', lw=1.5)
        ax.add_patch(circle)
        ax.text(x, y, text, fontsize=7, ha='center', va='center', color='white')
        ax.annotate('', xy=(x-0.35 if x > 0 else x+0.35, y),
                   xytext=(0.45 if x > 0 else -0.45, 0.2 if y > 0 else -0.2),
                   arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    # K=2
    ax = axes[2]
    ax.set_title('K = 2 (2-Hop Neighbors)', fontsize=12, fontweight='bold')

    # Center
    circle = plt.Circle((0, 0), 0.4, color='#4caf50', ec='#2e7d32', lw=2)
    ax.add_patch(circle)
    ax.text(0, 0, 'OpenAI', fontsize=7, ha='center', va='center', color='white', fontweight='bold')

    # 1-hop neighbors
    neighbors1 = [
        (1.2, 0.8, 'GPT-4', '#2196f3'),
        (1.2, -0.8, 'ChatGPT', '#2196f3'),
        (-1.2, 0, 'Sam', '#ff9800'),
    ]
    for x, y, text, color in neighbors1:
        circle = plt.Circle((x, y), 0.35, color=color, ec='#666', lw=1.5)
        ax.add_patch(circle)
        ax.text(x, y, text, fontsize=6, ha='center', va='center', color='white')

    # 2-hop neighbors
    circle = plt.Circle((2.2, 0), 0.35, color='#9c27b0', ec='#666', lw=1.5)
    ax.add_patch(circle)
    ax.text(2.2, 0, 'Trans-\nformer', fontsize=5, ha='center', va='center', color='white')

    # Edges
    edges = [
        (0.35, 0.2, 0.9, 0.6),
        (0.35, -0.2, 0.9, -0.6),
        (-0.35, 0, -0.9, 0),
        (1.5, 0.6, 1.9, 0.15),
        (1.5, -0.6, 1.9, -0.15),
    ]
    for x1, y1, x2, y2 in edges:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='#666', lw=1))

    plt.tight_layout()
    plt.savefig('khop_expansion.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("Saved: khop_expansion.png")
    plt.close()


def create_workflow_steps():
    """Create step-by-step workflow diagram."""

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    ax.text(7, 7.5, 'GraphRAG Workflow: From Question to Answer',
            fontsize=16, fontweight='bold', ha='center')

    steps = [
        (1, 5.5, '1️⃣', 'User Query', '"What did OpenAI develop?"', '#e1f5fe', '#0288d1'),
        (4, 5.5, '2️⃣', 'Entity Match', 'Find "OpenAI" in graph', '#fff3e0', '#ef6c00'),
        (7, 5.5, '3️⃣', 'K-Hop Expand', 'Get neighbors (k=2)', '#e0f7fa', '#00796b'),
        (10, 5.5, '4️⃣', 'Build Context', 'Subgraph → Text', '#f5f5f5', '#616161'),
        (13, 5.5, '5️⃣', 'LLM Answer', 'Generate response', '#f3e5f5', '#7b1fa2'),
    ]

    for x, y, num, title, desc, bg_color, border_color in steps:
        # Box
        box = FancyBboxPatch((x-1, y-1), 2, 2, boxstyle="round,pad=0.1",
                              facecolor=bg_color, edgecolor=border_color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y+0.5, num, fontsize=14, ha='center', va='center')
        ax.text(x, y, title, fontsize=9, ha='center', va='center', fontweight='bold')
        ax.text(x, y-0.5, desc, fontsize=7, ha='center', va='center', style='italic')

    # Arrows between steps
    for i in range(4):
        x = 2.1 + i * 3
        ax.annotate('', xy=(x+0.8, 5.5), xytext=(x, 5.5),
                   arrowprops=dict(arrowstyle='->', color='#666', lw=2))

    # Result box
    result_box = FancyBboxPatch((5, 1.5), 4, 1.5, boxstyle="round,pad=0.1",
                                 facecolor='#c8e6c9', edgecolor='#2e7d32', linewidth=2)
    ax.add_patch(result_box)
    ax.text(7, 2.5, '✅ Final Answer', fontsize=11, ha='center', va='center', fontweight='bold')
    ax.text(7, 1.9, '"OpenAI developed GPT-4 and ChatGPT"', fontsize=9, ha='center', va='center')

    ax.annotate('', xy=(7, 3.1), xytext=(12, 4.4),
               arrowprops=dict(arrowstyle='->', color='#2e7d32', lw=2,
                              connectionstyle='arc3,rad=0.3'))

    plt.tight_layout()
    plt.savefig('workflow_steps.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("Saved: workflow_steps.png")
    plt.close()


if __name__ == "__main__":
    print("Generating GraphRAG diagrams...")
    print("-" * 40)

    create_pipeline_diagram()
    create_comparison_diagram()
    create_khop_diagram()
    create_workflow_steps()

    print("-" * 40)
    print("All diagrams generated!")
    print("\nFiles created:")
    print("  - graphrag_pipeline.png")
    print("  - vector_vs_graph_rag.png")
    print("  - khop_expansion.png")
    print("  - workflow_steps.png")
