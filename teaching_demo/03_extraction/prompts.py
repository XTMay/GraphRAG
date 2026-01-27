"""
=============================================================================
GraphRAG Teaching Demo - Extraction Prompts
=============================================================================

This module contains prompts for extracting entities and relationships from text.

TEACHING NOTES:
---------------
1. Prompt design is CRITICAL for extraction quality
2. Clear output format specification helps LLM produce parseable JSON
3. Few-shot examples dramatically improve consistency
4. Entity type constraints prevent explosion of node types

COMMON MISTAKES:
----------------
- Not specifying JSON format clearly → unparseable output
- Too many entity types → noisy, inconsistent extraction
- No examples → inconsistent output format
- Asking for too much in one prompt → LLM confusion
"""

# =============================================================================
# Entity and Relationship Extraction Prompt
# =============================================================================

EXTRACTION_PROMPT = '''You are an expert at extracting structured knowledge from text.

Your task is to extract ENTITIES and RELATIONSHIPS from the given text.

## Entity Types (ONLY use these types):
- PERSON: Individual humans (e.g., Sam Altman, Geoffrey Hinton)
- ORGANIZATION: Companies, institutions, research labs (e.g., OpenAI, Google, Stanford University)
- TECHNOLOGY: AI models, architectures, systems (e.g., GPT-4, Transformer, BERT)
- LOCATION: Places (e.g., San Francisco, China)
- DATE: Time references (e.g., 2023, November 2022)

## Relationship Types (ONLY use these types):
- FOUNDED: Person founded an organization
- CEO_OF: Person is CEO of organization
- WORKS_AT: Person works at organization
- DEVELOPED: Organization/Person developed a technology
- BASED_ON: Technology is based on another technology
- LOCATED_IN: Organization is located in a place
- RELEASED_IN: Technology was released on a date
- ACQUIRED: Organization acquired another organization
- AFFILIATED_WITH: General association between entities

## Output Format:
Return a valid JSON object with this EXACT structure:
{
  "entities": [
    {"name": "Entity Name", "type": "ENTITY_TYPE", "description": "Brief description"}
  ],
  "relationships": [
    {"source": "Source Entity", "relation": "RELATION_TYPE", "target": "Target Entity", "description": "Brief description"}
  ]
}

## Example:

Text: "Apple Inc., founded by Steve Jobs in 1976, is headquartered in Cupertino."

Output:
{
  "entities": [
    {"name": "Apple Inc.", "type": "ORGANIZATION", "description": "Technology company"},
    {"name": "Steve Jobs", "type": "PERSON", "description": "Founder of Apple"},
    {"name": "1976", "type": "DATE", "description": "Year Apple was founded"},
    {"name": "Cupertino", "type": "LOCATION", "description": "City in California"}
  ],
  "relationships": [
    {"source": "Steve Jobs", "relation": "FOUNDED", "target": "Apple Inc.", "description": "Steve Jobs founded Apple"},
    {"source": "Apple Inc.", "relation": "LOCATED_IN", "target": "Cupertino", "description": "Apple is headquartered in Cupertino"}
  ]
}

## Important Rules:
1. Extract ONLY entities that are explicitly mentioned in the text
2. Do NOT infer or hallucinate entities not in the text
3. Use consistent entity names (e.g., always "OpenAI" not "Open AI")
4. Each relationship must connect two extracted entities
5. Return valid JSON only, no additional text

## Text to Process:
{text}

## Your Extraction (JSON only):
'''

# =============================================================================
# Alternative: Simplified Prompt (for weaker models)
# =============================================================================

SIMPLE_EXTRACTION_PROMPT = '''Extract entities and relationships from this text.

Entities to find: PERSON, ORGANIZATION, TECHNOLOGY
Relationships to find: FOUNDED, DEVELOPED, WORKS_AT, CEO_OF

Text: {text}

Return JSON format:
{
  "entities": [{"name": "...", "type": "..."}],
  "relationships": [{"source": "...", "relation": "...", "target": "..."}]
}

JSON:
'''

# =============================================================================
# Chinese Extraction Prompt (for Chinese text or bilingual models)
# =============================================================================

EXTRACTION_PROMPT_ZH = '''你是一个知识提取专家。请从给定文本中提取实体和关系。

## 实体类型:
- PERSON: 人物
- ORGANIZATION: 组织/公司
- TECHNOLOGY: 技术/模型
- LOCATION: 地点
- DATE: 日期

## 关系类型:
- FOUNDED: 创立
- CEO_OF: 担任CEO
- DEVELOPED: 开发
- LOCATED_IN: 位于
- WORKS_AT: 就职于

## 输出格式 (必须是有效的JSON):
{
  "entities": [{"name": "实体名", "type": "类型", "description": "描述"}],
  "relationships": [{"source": "源实体", "relation": "关系", "target": "目标实体"}]
}

## 待处理文本:
{text}

## 提取结果 (仅输出JSON):
'''

# =============================================================================
# Teaching Notes: Why These Design Choices?
# =============================================================================
"""
PROMPT DESIGN RATIONALE:

1. LIMITED ENTITY TYPES (5 types)
   - Why: Too many types → inconsistent classification
   - Why: Forces model to focus on most important entities
   - Alternative: Let model choose types (less consistent but more flexible)

2. LIMITED RELATIONSHIP TYPES (9 types)
   - Why: Standardized edges make graph querying easier
   - Why: Prevents edge explosion in the graph
   - Alternative: Free-form relations (more expressive but harder to query)

3. JSON OUTPUT FORMAT
   - Why: Machine-parseable, easy to validate
   - Why: Python's json.loads() can directly parse
   - Risk: LLM might produce invalid JSON → need error handling

4. FEW-SHOT EXAMPLE
   - Why: Shows exact format expected
   - Why: Reduces ambiguity in instructions
   - Best practice: Include 1-2 examples, more for complex tasks

5. EXPLICIT RULES
   - Why: LLMs tend to over-extract or hallucinate
   - Rule "ONLY entities in text" prevents hallucination
   - Rule "consistent names" helps with entity resolution

STUDENT EXERCISE:
-----------------
Try modifying the prompt:
1. Add a new entity type (e.g., PRODUCT, EVENT)
2. Add a new relationship type
3. Remove the example - does extraction quality drop?
4. Try with different LLMs - which handles the prompt best?
"""

# =============================================================================
# Prompt for Entity Matching (used in retrieval)
# =============================================================================

ENTITY_MATCHING_PROMPT = '''Given a question and a list of entities from a knowledge graph,
identify which entities are most relevant to answering the question.

Question: {question}

Available Entities:
{entities}

Return a JSON list of the most relevant entity names (maximum 3):
["entity1", "entity2", "entity3"]

Relevant Entities:
'''
