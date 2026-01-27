"""
=============================================================================
GraphRAG Teaching Demo - Knowledge Extractor
=============================================================================

This module extracts entities and relationships from text using an LLM.

TEACHING NOTES:
---------------
1. We use Ollama for local LLM inference (no API keys needed)
2. The extraction quality depends heavily on prompt design
3. Error handling is important - LLMs don't always produce valid JSON

PIPELINE:
---------
Text Document → LLM (with extraction prompt) → JSON → Validated Entities/Relations
"""

import json
import re
import requests
from typing import Optional


# =============================================================================
# LLM Client (Ollama)
# =============================================================================

class OllamaClient:
    """
    Simple client for Ollama API.

    TEACHING NOTE:
    Ollama provides an OpenAI-compatible API at localhost:11434
    This makes it easy to swap between Ollama and other providers.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate text completion from Ollama.

        Args:
            prompt: The input prompt
            temperature: Controls randomness (0 = deterministic, 1 = creative)
                        For extraction, use 0 for consistency!

        Returns:
            Generated text string
        """
        # TEACHING NOTE: temperature=0 is important for consistent extraction
        # Higher temperature = more creative but less consistent

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            print("Make sure Ollama is running: ollama serve")
            raise


# =============================================================================
# JSON Extraction Helper
# =============================================================================

def extract_json_from_text(text: str) -> Optional[dict]:
    """
    Extract JSON object from LLM response.

    TEACHING NOTE:
    LLMs sometimes add extra text before/after JSON.
    This function tries multiple strategies to extract valid JSON.

    Common issues:
    - LLM adds "Here's the extraction:" before JSON
    - LLM adds explanation after JSON
    - JSON has trailing commas (invalid in strict JSON)
    """

    # Strategy 1: Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Find JSON between curly braces
    # TEACHING NOTE: This regex finds the outermost { } pair
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # Strategy 3: More aggressive extraction
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # TEACHING NOTE: If all strategies fail, return None
    # The caller should handle this gracefully
    return None


# =============================================================================
# Knowledge Extractor
# =============================================================================

class KnowledgeExtractor:
    """
    Extracts entities and relationships from text documents.

    TEACHING NOTE:
    This is the most critical component of GraphRAG.
    Garbage in → Garbage out: Bad extraction = Bad graph = Bad answers
    """

    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

        # Import the prompt from prompts.py
        try:
            from prompts import EXTRACTION_PROMPT
        except ImportError:
            from .prompts import EXTRACTION_PROMPT
        self.prompt_template = EXTRACTION_PROMPT

    def extract(self, text: str) -> dict:
        """
        Extract entities and relationships from a single text.

        Args:
            text: The document text to process

        Returns:
            Dictionary with 'entities' and 'relationships' lists
        """
        # Format the prompt with the input text
        prompt = self.prompt_template.format(text=text)

        # Call LLM
        # TEACHING NOTE: This is where the magic happens!
        # The LLM reads the text and identifies structured knowledge
        print(f"  Extracting from text ({len(text)} chars)...")
        response = self.llm.generate(prompt, temperature=0.0)

        # Parse JSON from response
        result = extract_json_from_text(response)

        if result is None:
            # TEACHING NOTE: Extraction failed - return empty result
            # In production, you might want to retry or log this
            print("  Warning: Failed to parse JSON from LLM response")
            return {"entities": [], "relationships": []}

        # Validate structure
        result = self._validate_extraction(result)

        print(f"  Extracted {len(result['entities'])} entities, {len(result['relationships'])} relationships")
        return result

    def _validate_extraction(self, result: dict) -> dict:
        """
        Validate and clean the extraction result.

        TEACHING NOTE:
        LLMs are not perfectly reliable. We need to validate:
        1. Required fields exist
        2. Types are correct
        3. References are consistent (relationship entities exist)
        """
        # Ensure required keys exist
        if "entities" not in result:
            result["entities"] = []
        if "relationships" not in result:
            result["relationships"] = []

        # Normalize entity names (lowercase for matching)
        entity_names = set()
        for entity in result["entities"]:
            if "name" in entity:
                entity_names.add(entity["name"].lower())

        # Filter relationships to only include valid entity references
        valid_relationships = []
        for rel in result["relationships"]:
            source = rel.get("source", "").lower()
            target = rel.get("target", "").lower()

            # TEACHING NOTE: Only keep relationships where both entities exist
            # This prevents dangling edges in the graph
            if source in entity_names and target in entity_names:
                valid_relationships.append(rel)
            else:
                print(f"  Warning: Skipping relationship with unknown entity: {rel}")

        result["relationships"] = valid_relationships
        return result

    def extract_from_documents(self, documents: list) -> dict:
        """
        Extract from multiple documents and merge results.

        TEACHING NOTE:
        When processing multiple documents:
        1. Same entity might appear in different docs
        2. Need to merge/deduplicate entities
        3. Relationships from different docs are combined
        """
        all_entities = []
        all_relationships = []

        for i, doc in enumerate(documents):
            print(f"\nProcessing document {i+1}/{len(documents)}: {doc.get('title', 'Untitled')}")

            text = doc.get("content", "")
            if not text:
                continue

            extraction = self.extract(text)

            # Add source document reference
            # TEACHING NOTE: Tracking provenance is important for debugging
            for entity in extraction["entities"]:
                entity["source_doc"] = doc.get("id", f"doc_{i}")
            for rel in extraction["relationships"]:
                rel["source_doc"] = doc.get("id", f"doc_{i}")

            all_entities.extend(extraction["entities"])
            all_relationships.extend(extraction["relationships"])

        # Deduplicate entities
        # TEACHING NOTE: Entity resolution is a complex problem!
        # Here we use simple name matching. Production systems use more sophisticated methods.
        unique_entities = self._deduplicate_entities(all_entities)

        return {
            "entities": unique_entities,
            "relationships": all_relationships
        }

    def _deduplicate_entities(self, entities: list) -> list:
        """
        Remove duplicate entities (by name).

        TEACHING NOTE:
        Simple deduplication by name. More sophisticated approaches:
        - Fuzzy matching ("OpenAI" vs "Open AI")
        - Embedding similarity
        - Coreference resolution

        STUDENT EXERCISE: Implement fuzzy matching!
        """
        seen = {}
        unique = []

        for entity in entities:
            name = entity.get("name", "").lower()
            if name and name not in seen:
                seen[name] = True
                unique.append(entity)

        return unique


# =============================================================================
# Demo / Test
# =============================================================================

if __name__ == "__main__":
    """
    Demo: Run extraction on sample text.

    To test:
    1. Make sure Ollama is running: ollama serve
    2. Run: python extractor.py
    """

    # Sample text for testing
    sample_text = """
    OpenAI is an artificial intelligence research company founded in 2015
    by Sam Altman and Elon Musk. Sam Altman serves as CEO of OpenAI.
    The company developed GPT-4, a large language model released in 2023.
    OpenAI is headquartered in San Francisco.
    """

    print("=" * 60)
    print("GraphRAG Knowledge Extractor Demo")
    print("=" * 60)

    # Initialize
    llm = OllamaClient(model="qwen2.5:7b")
    extractor = KnowledgeExtractor(llm)

    # Extract
    print("\nInput text:")
    print(sample_text)
    print("\nExtracting...")

    result = extractor.extract(sample_text)

    # Display results
    print("\n" + "=" * 60)
    print("Extraction Results")
    print("=" * 60)

    print("\nEntities:")
    for e in result["entities"]:
        print(f"  - {e['name']} ({e.get('type', 'UNKNOWN')})")

    print("\nRelationships:")
    for r in result["relationships"]:
        print(f"  - {r['source']} --[{r['relation']}]--> {r['target']}")

    print("\nRaw JSON:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
