"""
FastAPI Application
===================

REST API for the Smart Home Graph Agent.

Teaching Points:
- Lifespan events manage startup/shutdown (init Agent, close DB)
- Depends() injects shared resources into endpoint functions
- CORS middleware allows cross-origin requests (for frontends)
- SSE (Server-Sent Events) enables streaming responses
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.api.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    GraphStatsResponse,
    ErrorResponse,
)
from src.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware

logger = logging.getLogger("smart_home_api")


# =========================================
# APPLICATION STATE (managed by lifespan)
# =========================================

class AppState:
    """Holds shared resources initialized at startup."""
    agent = None
    retriever = None
    connection = None


app_state = AppState()


# =========================================
# LIFESPAN: Startup / Shutdown
# =========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Teaching Point:
        The lifespan context manager replaces @app.on_event("startup")
        and @app.on_event("shutdown"). It's the modern FastAPI pattern.
    """
    # === STARTUP ===
    logger.info("Starting Smart Home API...")

    try:
        from src.agent.workflow import SmartHomeAgent
        app_state.agent = SmartHomeAgent()
        logger.info("Agent initialized")
    except Exception as e:
        logger.error("Failed to initialize agent: %s", e)

    try:
        from src.graph.retriever import SmartHomeRetriever
        app_state.retriever = SmartHomeRetriever()
        logger.info("Retriever initialized")
    except Exception as e:
        logger.error("Failed to initialize retriever: %s", e)

    try:
        from src.graph.connection import get_connection
        app_state.connection = get_connection()
        logger.info("Neo4j connection initialized")
    except Exception as e:
        logger.error("Failed to connect to Neo4j: %s", e)

    yield  # Application is running

    # === SHUTDOWN ===
    logger.info("Shutting down Smart Home API...")
    if app_state.connection:
        try:
            from src.graph.connection import close_connection
            close_connection()
            logger.info("Neo4j connection closed")
        except Exception:
            pass


# =========================================
# DEPENDENCY INJECTION
# =========================================

def get_agent():
    """
    Dependency: Get the shared Agent instance.

    Teaching Point:
        FastAPI's Depends() pattern is Dependency Injection (DI).
        It decouples endpoint logic from resource management.
    """
    if app_state.agent is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized. Check server logs.",
        )
    return app_state.agent


def get_retriever():
    """Dependency: Get the shared Retriever instance."""
    if app_state.retriever is None:
        raise HTTPException(
            status_code=503,
            detail="Retriever not initialized. Check Neo4j connection.",
        )
    return app_state.retriever


# =========================================
# CREATE APPLICATION
# =========================================

def create_app() -> FastAPI:
    """
    Factory function to create the FastAPI application.

    Teaching Point:
        Application factory pattern makes testing easier.
        You can create multiple app instances with different configs.
    """
    app = FastAPI(
        title="Smart Home Graph Agent API",
        description=(
            "REST API for the Smart Home Graph Agent.\n\n"
            "This API provides endpoints for:\n"
            "- Chat with the smart home agent\n"
            "- Stream agent responses via SSE\n"
            "- Query the knowledge graph\n"
            "- Health monitoring"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # --- Middleware (order: last added = outermost) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)
    app.add_middleware(RequestLoggingMiddleware)

    # --- Register routes ---
    _register_routes(app)

    return app


# =========================================
# ROUTES
# =========================================

def _register_routes(app: FastAPI) -> None:
    """Register all API endpoints."""

    # ----- Chat Endpoints -----

    @app.post(
        "/api/v1/chat",
        response_model=ChatResponse,
        tags=["Chat"],
        summary="Send a chat message",
        responses={503: {"model": ErrorResponse}},
    )
    async def chat(request: ChatRequest, agent=Depends(get_agent)):
        """
        Process a user message and return the agent's response.

        This endpoint runs the full LangGraph workflow:
        1. Parse intent
        2. Retrieve context from knowledge graph
        3. Generate action plan
        4. Validate plan
        5. Generate natural language response
        """
        try:
            start_time = datetime.now()

            if request.debug:
                response_text, trace = agent.run_with_trace(request.message)
            else:
                response_text = agent.run(request.message)
                trace = []

            duration = (datetime.now() - start_time).total_seconds()

            return ChatResponse(
                response=response_text,
                reasoning_trace=trace,
                session_id=request.session_id,
                metadata={"duration_seconds": round(duration, 3)},
            )
        except Exception as e:
            logger.error("Chat error: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post(
        "/api/v1/chat/stream",
        tags=["Chat"],
        summary="Stream a chat response via SSE",
    )
    async def chat_stream(request: ChatRequest, agent=Depends(get_agent)):
        """
        Stream agent responses using Server-Sent Events (SSE).

        Each event corresponds to a workflow node completing.
        The client receives real-time updates as the agent processes.

        Teaching Point:
            SSE is simpler than WebSocket for one-way streaming.
            The client opens a connection and receives events as they happen.
        """
        async def event_generator():
            try:
                for event in agent.run_streaming(request.message):
                    for node_name, node_data in event.items():
                        yield {
                            "event": "node_complete",
                            "data": json.dumps({
                                "node_name": node_name,
                                "data": _serialize_state(node_data),
                                "timestamp": datetime.now().isoformat(),
                            }, ensure_ascii=False),
                        }

                yield {
                    "event": "done",
                    "data": json.dumps({"status": "complete"}),
                }
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }

        return EventSourceResponse(event_generator())

    # ----- Health Endpoints -----

    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Health check",
    )
    async def health():
        """Check system health (Neo4j, LLM provider)."""
        neo4j_status = {"status": "unknown"}
        if app_state.connection:
            try:
                neo4j_status = app_state.connection.health_check()
            except Exception as e:
                neo4j_status = {"status": "unhealthy", "error": str(e)}
        else:
            neo4j_status = {"status": "not_connected"}

        llm_status = {"status": "unknown"}
        try:
            from src.llm import get_llm_info
            llm_status = get_llm_info()
        except Exception as e:
            llm_status = {"status": "error", "error": str(e)}

        overall = "healthy"
        if neo4j_status.get("status") != "healthy":
            overall = "degraded"
        if llm_status.get("status") != "ok":
            overall = "degraded"

        return HealthResponse(
            status=overall,
            neo4j=neo4j_status,
            llm=llm_status,
        )

    # ----- Graph Endpoints -----

    @app.get(
        "/api/v1/graph/stats",
        response_model=GraphStatsResponse,
        tags=["Graph"],
        summary="Knowledge graph statistics",
    )
    async def graph_stats(retriever=Depends(get_retriever)):
        """Get statistics about the knowledge graph (node/relationship counts)."""
        stats = retriever.get_graph_stats()
        return GraphStatsResponse(
            rooms=stats.get("rooms", 0),
            devices=stats.get("devices", 0),
            capabilities=stats.get("capabilities", 0),
            scenes=stats.get("scenes", 0),
            relationships=stats.get("total_relationships", 0),
        )

    @app.get(
        "/api/v1/graph/rooms",
        tags=["Graph"],
        summary="List all rooms",
    )
    async def list_rooms(retriever=Depends(get_retriever)):
        """Get a list of all rooms in the smart home."""
        return retriever.get_all_rooms()

    @app.get(
        "/api/v1/graph/rooms/{room_name}/devices",
        tags=["Graph"],
        summary="Get devices in a room",
    )
    async def room_devices(room_name: str, retriever=Depends(get_retriever)):
        """Get all devices in a specific room."""
        result = retriever.get_room_context(room_name)
        return {
            "room": room_name,
            "devices": result.raw_results,
            "device_count": result.metadata.get("device_count", 0),
        }

    @app.get(
        "/api/v1/graph/devices",
        tags=["Graph"],
        summary="List all devices",
    )
    async def list_devices(retriever=Depends(get_retriever)):
        """Get a list of all devices in the smart home."""
        return retriever.get_all_devices()

    @app.get(
        "/api/v1/graph/scenes",
        tags=["Graph"],
        summary="List all scenes",
    )
    async def list_scenes(retriever=Depends(get_retriever)):
        """Get a list of all available scenes."""
        return retriever.get_all_scenes()


# =========================================
# HELPERS
# =========================================

def _serialize_state(data: dict) -> dict:
    """Serialize agent state data for JSON response."""
    result = {}
    for key, value in data.items():
        try:
            json.dumps(value)
            result[key] = value
        except (TypeError, ValueError):
            result[key] = str(value)
    return result
