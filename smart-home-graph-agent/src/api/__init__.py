"""
API Module
==========

FastAPI web service layer for the Smart Home Graph Agent.

Main Components:
- FastAPI application with REST endpoints
- Pydantic request/response models
- Middleware for logging, rate limiting, error handling
- SSE streaming support

Teaching Points:
- REST API design patterns
- Request validation with Pydantic
- Middleware pipeline concept
- Server-Sent Events for streaming
"""

from .models import ChatRequest, ChatResponse, StreamEvent, HealthResponse, GraphStatsResponse
from .server import create_app

__all__ = [
    "create_app",
    "ChatRequest",
    "ChatResponse",
    "StreamEvent",
    "HealthResponse",
    "GraphStatsResponse",
]
