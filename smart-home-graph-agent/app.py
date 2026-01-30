#!/usr/bin/env python3
"""
Smart Home Graph Agent - CLI Application
=========================================

A command-line interface for the Smart Home Agent.

Usage:
    python app.py                    # Interactive mode
    python app.py "your request"     # Single request mode
    python app.py --debug "request"  # Debug mode with trace

Teaching Points:
- Simple CLI wrapping the agent
- Shows how to integrate agent into applications
"""

import sys
import os
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          🏠 Smart Home Graph Agent 🏠                     ║
║                                                           ║
║  A GraphRAG + LangGraph Teaching Demo                     ║
║  Type 'help' for commands, 'quit' to exit                 ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help message."""
    help_text = """
Available Commands:
  help     - Show this help message
  quit     - Exit the application
  debug    - Toggle debug mode (show reasoning trace)
  status   - Show system status (Neo4j connection, etc.)
  examples - Show example requests

Example Requests:
  "Make the living room cozy for movie night"
  "Turn on all the lights in the kitchen"
  "Set up the bedroom for sleep"
  "Dim the lights to 50%"
  "What devices are in the living room?"
"""
    print(help_text)


def print_examples():
    """Print example requests."""
    examples = """
📝 Example Requests to Try:

1. Room-specific:
   "Turn on the living room lights"
   "Make the bedroom cozy"

2. Scene-based:
   "Set up for movie night"
   "Prepare for bedtime"
   "Party mode!"

3. Action-based:
   "Dim all the lights"
   "Play some music"

4. Multi-room:
   "Turn off all the lights in the house"

5. Vague (tests clarification):
   "Make it comfortable"
   "I want to relax"
"""
    print(examples)


def check_status():
    """Check system status."""
    print("\n📊 System Status")
    print("-" * 40)

    # Check OpenAI key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✓ OpenAI API Key: {masked}")
    else:
        print("✗ OpenAI API Key: Not set")
        print("  Set OPENAI_API_KEY in .env file")

    # Check Neo4j connection
    try:
        from src.graph.connection import Neo4jConnection
        conn = Neo4jConnection()
        health = conn.health_check()
        conn.close()

        if health.get("status") == "healthy":
            print(f"✓ Neo4j: Connected")
            print(f"  - Nodes: {health.get('node_count', 0)}")
            print(f"  - Relationships: {health.get('relationship_count', 0)}")
        else:
            print(f"✗ Neo4j: {health.get('error', 'Connection failed')}")
    except Exception as e:
        print(f"✗ Neo4j: {str(e)[:50]}")

    print("-" * 40)


def run_interactive(debug: bool = False):
    """Run in interactive mode."""
    print_banner()

    # Check status first
    check_status()

    # Import agent (after status check to show errors)
    try:
        from src.agent import SmartHomeAgent
        agent = SmartHomeAgent(debug=debug)
        print("\n✓ Agent initialized successfully!")
    except Exception as e:
        print(f"\n✗ Failed to initialize agent: {e}")
        print("  Make sure Neo4j is running and OPENAI_API_KEY is set.")
        return

    print("\nReady for requests. Type 'help' for commands.\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == 'quit':
                print("\nGoodbye! 👋")
                break
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif user_input.lower() == 'debug':
                debug = not debug
                agent.debug = debug
                print(f"Debug mode: {'ON' if debug else 'OFF'}")
                continue
            elif user_input.lower() == 'status':
                check_status()
                continue
            elif user_input.lower() == 'examples':
                print_examples()
                continue

            # Process request
            print("\n🤔 Processing...\n")

            if debug:
                response, trace = agent.run_with_trace(user_input)
                print("📋 Reasoning Trace:")
                for i, step in enumerate(trace, 1):
                    print(f"   {i}. {step}")
                print()
            else:
                response = agent.run(user_input)

            print(f"🏠 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            if debug:
                import traceback
                traceback.print_exc()


def run_single(request: str, debug: bool = False):
    """Run a single request."""
    try:
        from src.agent import SmartHomeAgent
        agent = SmartHomeAgent(debug=debug)

        if debug:
            response, trace = agent.run_with_trace(request)
            print("Reasoning Trace:")
            if trace:
                for i, step in enumerate(trace, 1):
                    print(f"   {i}. {step}")
            else:
                print("   (No reasoning trace available)")
            print()
            print(f"Response: {response}")
        else:
            response = agent.run(request)
            print(response)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smart Home Graph Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                              # Interactive mode
  python app.py "Turn on living room lights" # Single request
  python app.py --debug "Make it cozy"       # Debug mode
  python app.py --status                     # Check system status
"""
    )

    parser.add_argument(
        "request",
        nargs="?",
        help="Request to process (if not provided, runs in interactive mode)"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode (show reasoning trace)"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Check system status and exit"
    )

    args = parser.parse_args()

    if args.status:
        check_status()
        return

    if args.request:
        run_single(args.request, debug=args.debug)
    else:
        run_interactive(debug=args.debug)


if __name__ == "__main__":
    main()
