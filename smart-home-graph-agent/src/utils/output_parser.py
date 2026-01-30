"""
Output Parsers
==============

Parse LLM outputs into structured Python objects.

Teaching Points:
- LLMs output text, but we need structured data
- Pydantic models define expected schema
- Parsers handle JSON extraction and validation
"""

import json
import re
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


# =========================================
# DATA MODELS
# =========================================

class ParsedIntent(BaseModel):
    """Structured representation of user intent."""

    goal: str = Field(description="What the user wants to achieve")
    rooms: list[str] = Field(default_factory=list, description="Rooms mentioned")
    actions: list[str] = Field(default_factory=list, description="Specific actions mentioned")
    mood: Optional[str] = Field(default=None, description="Desired mood/atmosphere")
    scene_hint: Optional[str] = Field(default=None, description="Referenced scene name")
    constraints: list[str] = Field(default_factory=list, description="Any constraints")

    @field_validator('rooms', 'actions', 'constraints', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        return v


class DeviceAction(BaseModel):
    """A single device command."""

    device_id: str = Field(description="Device identifier")
    device_name: str = Field(description="Human-readable device name")
    capability: str = Field(description="Capability to invoke")
    value: Any = Field(description="Value to set")
    reason: Optional[str] = Field(default=None, description="Why this action")


class ActionPlan(BaseModel):
    """Complete action plan with reasoning."""

    reasoning: str = Field(description="Explanation of the plan")
    actions: list[DeviceAction] = Field(default_factory=list, description="Device commands")

    def to_display_string(self) -> str:
        """Format for user display."""
        lines = [f"**Reasoning:** {self.reasoning}", "", "**Actions:**"]
        for i, action in enumerate(self.actions, 1):
            lines.append(f"  {i}. {action.device_name}: {action.capability} → {action.value}")
            if action.reason:
                lines.append(f"     ({action.reason})")
        return "\n".join(lines)


class ValidationResult(BaseModel):
    """Result of action plan validation."""

    is_valid: bool = Field(description="Whether the plan is valid")
    issues: list[str] = Field(default_factory=list, description="Problems found")
    suggestions: list[str] = Field(default_factory=list, description="Improvements")


class ClarificationRequest(BaseModel):
    """Request for user clarification."""

    needs_clarification: bool = Field(default=True)
    question: str = Field(description="Question to ask user")
    options: list[str] = Field(default_factory=list, description="Multiple choice options")


# =========================================
# PARSING FUNCTIONS
# =========================================

def extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response text.

    Handles cases where JSON is wrapped in markdown code blocks
    or mixed with other text.

    Args:
        text: Raw LLM output

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If no valid JSON found
    """
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_block_pattern, text)

    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Try to find JSON object pattern
    json_pattern = r'\{[\s\S]*\}'
    matches = re.findall(json_pattern, text)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Could not extract valid JSON from: {text[:200]}...")


def parse_intent(llm_output: str) -> ParsedIntent:
    """
    Parse LLM output into ParsedIntent.

    Args:
        llm_output: Raw LLM response

    Returns:
        ParsedIntent object
    """
    data = extract_json(llm_output)
    return ParsedIntent(**data)


def parse_action_plan(llm_output: str) -> ActionPlan:
    """
    Parse LLM output into ActionPlan.

    Args:
        llm_output: Raw LLM response

    Returns:
        ActionPlan object
    """
    data = extract_json(llm_output)
    return ActionPlan(**data)


def parse_validation(llm_output: str) -> ValidationResult:
    """
    Parse LLM output into ValidationResult.

    Args:
        llm_output: Raw LLM response

    Returns:
        ValidationResult object
    """
    data = extract_json(llm_output)
    return ValidationResult(**data)


def parse_clarification(llm_output: str) -> ClarificationRequest:
    """
    Parse LLM output into ClarificationRequest.

    Args:
        llm_output: Raw LLM response

    Returns:
        ClarificationRequest object
    """
    data = extract_json(llm_output)
    return ClarificationRequest(**data)


# =========================================
# CONVENIENCE CLASSES
# =========================================

class SmartHomeOutputParser:
    """
    Unified parser for all smart home agent outputs.

    Usage:
        parser = SmartHomeOutputParser()
        intent = parser.parse_intent(llm_output)
        plan = parser.parse_action_plan(llm_output)
    """

    @staticmethod
    def parse_intent(text: str) -> ParsedIntent:
        return parse_intent(text)

    @staticmethod
    def parse_action_plan(text: str) -> ActionPlan:
        return parse_action_plan(text)

    @staticmethod
    def parse_validation(text: str) -> ValidationResult:
        return parse_validation(text)

    @staticmethod
    def parse_clarification(text: str) -> ClarificationRequest:
        return parse_clarification(text)

    @staticmethod
    def extract_json(text: str) -> dict:
        return extract_json(text)


# =========================================
# TESTING
# =========================================

if __name__ == "__main__":
    print("Testing Output Parsers")
    print("=" * 50)

    # Test intent parsing
    intent_json = '''
    {
        "goal": "prepare for movie",
        "rooms": ["living room"],
        "actions": ["dim lights"],
        "mood": "cozy",
        "scene_hint": "movie night",
        "constraints": []
    }
    '''

    intent = parse_intent(intent_json)
    print("\n✓ Intent Parsing:")
    print(f"  Goal: {intent.goal}")
    print(f"  Rooms: {intent.rooms}")
    print(f"  Mood: {intent.mood}")

    # Test action plan parsing
    plan_json = '''
    ```json
    {
        "reasoning": "Dimming lights for movie atmosphere",
        "actions": [
            {
                "device_id": "living_ceiling_01",
                "device_name": "Ceiling Light",
                "capability": "dim",
                "value": 20,
                "reason": "Low light for movies"
            }
        ]
    }
    ```
    '''

    plan = parse_action_plan(plan_json)
    print("\n✓ Action Plan Parsing:")
    print(f"  Reasoning: {plan.reasoning}")
    print(f"  Actions: {len(plan.actions)}")
    print(f"\n{plan.to_display_string()}")

    # Test with malformed input
    print("\n✓ Error Handling:")
    try:
        parse_intent("This is not JSON")
    except ValueError as e:
        print(f"  Correctly caught error: {str(e)[:50]}...")
