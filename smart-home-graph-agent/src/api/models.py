"""
API Data Models
===============

Pydantic models for request validation and response serialization.

Teaching Points:
- Pydantic enforces types at runtime (not just hints)
- Optional fields have default values
- Field(...) adds validation constraints
- Models auto-generate JSON Schema → Swagger UI
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# =========================================
# REQUEST MODELS
# =========================================

class ChatRequest(BaseModel):
    """
    Chat request payload.

    Example:
        {
            "message": "打开客厅的灯",
            "debug": false,
            "session_id": "user-123"
        }
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's natural language request",
        examples=["打开客厅的灯", "Make the living room cozy for movie night"],
    )
    debug: bool = Field(
        default=False,
        description="If true, include reasoning trace in response",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation memory (optional)",
    )


# =========================================
# RESPONSE MODELS
# =========================================

class ChatResponse(BaseModel):
    """
    Chat response payload.

    Teaching Point:
        Structured responses make it easy for frontends to render.
        The reasoning_trace is only populated when debug=True.
    """
    response: str = Field(
        description="Agent's natural language response",
    )
    reasoning_trace: list[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning (only when debug=True)",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (timing, retrieval info, etc.)",
    )


class StreamEvent(BaseModel):
    """
    Server-Sent Event payload for streaming responses.

    Teaching Point:
        SSE sends events one at a time as the agent processes.
        Each event corresponds to a workflow node completing.
    """
    node_name: str = Field(description="Name of the workflow node that produced this event")
    data: dict = Field(default_factory=dict, description="Event payload data")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of the event",
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Overall status: healthy / degraded / unhealthy")
    neo4j: dict = Field(default_factory=dict, description="Neo4j connection status")
    llm: dict = Field(default_factory=dict, description="LLM provider status")
    version: str = Field(default="1.0.0", description="API version")


class GraphStatsResponse(BaseModel):
    """Knowledge graph statistics."""
    rooms: int = Field(default=0)
    devices: int = Field(default=0)
    capabilities: int = Field(default=0)
    scenes: int = Field(default=0)
    relationships: int = Field(default=0)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(description="Error type")
    detail: str = Field(description="Human-readable error message")
    request_id: Optional[str] = Field(default=None)
