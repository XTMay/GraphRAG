"""
API Server Entry Point
======================

Start the FastAPI web service for the Smart Home Graph Agent.

Usage:
    python api_server.py                    # Default: localhost:8000
    python api_server.py --port 8080        # Custom port
    python api_server.py --host 0.0.0.0     # Listen on all interfaces
    python api_server.py --reload           # Auto-reload on code changes (dev mode)

After starting, open http://localhost:8000/docs for Swagger UI.

Teaching Point:
    This file is analogous to app.py (CLI) and streamlit_app.py (Web UI).
    It's a third interface to the same agent — the REST API interface.
"""

import argparse
import logging
import sys

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Smart Home Graph Agent - API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python api_server.py                  Start with defaults (localhost:8000)
  python api_server.py --port 8080      Use port 8080
  python api_server.py --reload         Enable auto-reload for development
  python api_server.py --host 0.0.0.0   Listen on all network interfaces
        """,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("  Smart Home Graph Agent - API Server")
    print("=" * 60)
    print(f"  Host:    {args.host}")
    print(f"  Port:    {args.port}")
    print(f"  Reload:  {args.reload}")
    print(f"  Docs:    http://{args.host}:{args.port}/docs")
    print("=" * 60)

    uvicorn.run(
        "src.api.server:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
