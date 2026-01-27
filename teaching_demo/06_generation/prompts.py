"""
=============================================================================
GraphRAG Teaching Demo - Generation Prompts
=============================================================================

This module contains prompts for generating answers based on graph context.

TEACHING NOTES:
---------------
1. The generation prompt is WHERE the magic happens
2. Good prompts guide the LLM to use the graph context effectively
3. Prompts should encourage the LLM to:
   - Use ONLY information from the context
   - Follow reasoning paths in the graph
   - Admit when information is not available

KEY INSIGHT:
------------
The quality of generation depends on:
1. Quality of the retrieved subgraph (from retrieval)
2. How well the subgraph is formatted as text
3. How well the prompt guides the LLM to use that context
"""

# =============================================================================
# Main Answer Generation Prompt
# =============================================================================

ANSWER_GENERATION_PROMPT = '''You are a helpful assistant that answers questions using ONLY the provided knowledge graph context.

## Knowledge Graph Context:
{context}

## Rules:
1. Answer ONLY using information from the context above
2. If the answer is not in the context, say "I don't have enough information to answer this question"
3. When referencing entities, use their exact names from the context
4. If the question requires connecting multiple facts, explain the reasoning path

## Question:
{question}

## Your Answer:
'''

# =============================================================================
# Chain-of-Thought Reasoning Prompt
# =============================================================================

REASONING_PROMPT = '''You are a knowledge graph reasoning assistant. Answer questions by following relationships in the provided graph.

## Knowledge Graph Context:
{context}

## Question:
{question}

## Instructions:
Think step-by-step by following the relationships in the graph:

1. First, identify the key entities mentioned in the question
2. Find those entities in the context
3. Follow the relationships to find connected information
4. Use only the relationships present to form your answer

## Reasoning Steps:
(Show your reasoning path through the graph)

## Final Answer:
(Based on your reasoning above)
'''

# =============================================================================
# Strict Factual Prompt (Prevents Hallucination)
# =============================================================================

STRICT_FACTUAL_PROMPT = '''You must answer the question using ONLY the facts provided below.

FACTS FROM KNOWLEDGE GRAPH:
{context}

QUESTION: {question}

INSTRUCTIONS:
- If the facts contain the answer, provide it
- If the facts do NOT contain enough information, respond: "INSUFFICIENT INFORMATION"
- Do NOT add any information not explicitly stated in the facts
- Do NOT use your own knowledge

ANSWER:
'''

# =============================================================================
# Conversational Prompt
# =============================================================================

CONVERSATIONAL_PROMPT = '''You are a friendly assistant with access to a knowledge graph about {topic}.

Based on what I know from the knowledge graph:
{context}

User asks: {question}

Please answer naturally and conversationally, but only using the information provided above. If you're not sure about something, say so.