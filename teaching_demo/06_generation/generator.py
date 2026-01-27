"""
=============================================================================
GraphRAG Teaching Demo - Answer Generator
=============================================================================

This module generates answers using LLM + retrieved graph context.

TEACHING NOTES:
---------------
1. This is the FINAL step in GraphRAG
2. The LLM reasons over the graph context to answer the question
3. Quality depends on: retrieval quality + prompt quality + LLM capability

COMPARISON WITH VECTOR RAG:
---------------------------
Vector RAG: LLM sees retrieved text chunks
GraphRAG:   LLM sees structured entity-relationship facts

The structured format can help the LLM:
- See clear relationships
- Follow reasoning paths
- Distinguish entities clearly
"""

import requests
from typing import Optional

# Import prompts
try:
    from prompts import (
        ANSWER_GENERATION_PROMPT,
        REASONING_PROMPT,
        STRICT_FACTUAL_PROMPT
    )
except ImportError:
    from .prompts import (
        ANSWER_GENERATION_PROMPT,
        REASONING_PROMPT,
        STRICT_FACTUAL_PROMPT
    )


class AnswerGenerator:
    """
    Generates answers using LLM and graph context.

    TEACHING NOTE:
    The generator is relatively simple - most of the work is in:
    1. Extraction (getting good entities/relations)
    2. Retrieval (getting the right subgraph)

    The generator just formats the prompt and calls the LLM.
    """

    def __init__(
        self,
        llm_base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b"
    ):
        self.llm_base_url = llm_base_url
        self.model = model

    def generate(
        self,
        question: str,
        context: str,
        mode: str = "standard",
        temperature: float = 0.3
    ) -> dict:
        """
        Generate an answer based on graph context.

        Args:
            question: The user's question
            context: Graph context as text (from retriever.subgraph_to_text())
            mode: Generation mode:
                  - "standard": Basic Q&A
                  - "reasoning": Chain-of-thought reasoning
                  - "strict": Only use context, no external knowledge
            temperature: LLM temperature (0 = deterministic, 1 = creative)

        Returns:
            Dict with 'answer' and 'mode' keys

        TEACHING NOTE:
        Temperature setting matters:
        - 0.0: Very deterministic, good for factual Q&A
        - 0.3: Slight variation, good for natural-sounding answers
        - 0.7+: More creative, NOT recommended for factual RAG
        """

        # Select prompt based on mode
        if mode == "reasoning":
            prompt_template = REASONING_PROMPT
        elif mode == "strict":
            prompt_template = STRICT_FACTUAL_PROMPT
        else:
            prompt_template = ANSWER_GENERATION_PROMPT

        # Format prompt
        prompt = prompt_template.format(
            context=context,
            question=question
        )

        # Call LLM
        print(f"[Generator] Generating answer (mode={mode})...")
        answer = self._call_llm(prompt, temperature)

        return {
            "question": question,
            "answer": answer,
            "mode": mode,
            "context_length": len(context)
        }

    def _call_llm(self, prompt: str, temperature: float) -> str:
        """
        Call Ollama API to generate text.

        TEACHING NOTE:
        We use Ollama for local inference. This can be swapped for:
        - vLLM
        - Text Generation Inference (TGI)
        - Any OpenAI-compatible API
        """

        try:
            response = requests.post(
                f"{self.llm_base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["response"]

        except requests.exceptions.RequestException as e:
            print(f"[Generator] Error calling LLM: {e}")
            return "Error: Could not generate answer. Please check if Ollama is running."

    def generate_with_reasoning_path(
        self,
        question: str,
        context: str,
        subgraph  # NetworkX graph
    ) -> dict:
        """
        Generate answer with explicit reasoning path visualization.

        TEACHING NOTE:
        This is an advanced feature that shows HOW the answer was derived
        by highlighting the path through the graph.

        STUDENT EXERCISE: Implement this function!
        """

        # First generate the answer
        result = self.generate(question, context, mode="reasoning")

        # TODO: Extract reasoning path from answer
        # TODO: Map path back to graph edges
        # TODO: Return highlighted path

        result["reasoning_path"] = "TODO: Extract and visualize reasoning path"

        return result


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    """Demo answer generation."""

    print("=" * 60)
    print("Answer Generator Demo")
    print("=" * 60)

    # Sample context (as if retrieved from graph)
    context = """
=== Knowledge Graph Context ===

Entities:
- OpenAI (ORGANIZATION): AI research company founded in 2015
- Sam Altman (PERSON): CEO of OpenAI
- GPT-4 (TECHNOLOGY): Large language model developed by OpenAI
- ChatGPT (TECHNOLOGY): Conversational AI based on GPT models
- Transformer (TECHNOLOGY): Neural network architecture

Relationships:
- Sam Altman --[CEO_OF]--> OpenAI
- OpenAI --[DEVELOPED]--> GPT-4
- OpenAI --[DEVELOPED]--> ChatGPT
- ChatGPT --[BASED_ON]--> GPT-4
- GPT-4 --[BASED_ON]--> Transformer
"""

    # Initialize generator
    generator = AnswerGenerator(model="qwen2.5:7b")

    # Test questions
    questions = [
        "Who is the CEO of OpenAI?",
        "What did OpenAI develop?",
        "What is ChatGPT based on?",
    ]

    for question in questions:
        print(f"\n{'=' * 60}")
        print(f"Question: {question}")
        print("-" * 40)

        result = generator.generate(
            question=question,
            context=context,
            mode="standard"
        )

        print(f"Answer: {result['answer']}")
