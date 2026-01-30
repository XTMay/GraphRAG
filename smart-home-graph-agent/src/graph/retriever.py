"""
Smart Home GraphRAG Retriever
=============================

This module implements graph-based retrieval for the smart home agent.
It translates high-level retrieval intents into Cypher queries and
formats results for LLM consumption.

Teaching Points:
- GraphRAG retrieves structured subgraphs, not just text chunks
- Context is formatted specifically for LLM reasoning
- Multiple retrieval strategies for different query types
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum

from .connection import Neo4jConnection, get_connection
from .queries import SmartHomeQueries


class RetrievalStrategy(Enum):
    """
    Different strategies for retrieving context from the graph.

    Teaching Point:
        The retrieval strategy depends on what information
        the agent needs to accomplish its task.
    """
    ROOM_CONTEXT = "room_context"           # Get everything about a room
    CAPABILITY_SEARCH = "capability_search"  # Find devices by what they can do
    SCENE_LOOKUP = "scene_lookup"           # Get predefined scene configurations
    KEYWORD_SEARCH = "keyword_search"       # Fuzzy search across all entities
    MULTI_ROOM = "multi_room"               # Context for whole-house actions


@dataclass
class RetrievalResult:
    """
    Container for retrieval results.

    Attributes:
        strategy: Which retrieval strategy was used
        query_params: Parameters passed to the query
        raw_results: Raw data from Neo4j
        formatted_context: LLM-ready formatted string
        metadata: Additional info (timing, counts, etc.)
    """
    strategy: RetrievalStrategy
    query_params: dict
    raw_results: list[dict[str, Any]]
    formatted_context: str
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"RetrievalResult(strategy={self.strategy.value}, "
            f"results={len(self.raw_results)}, "
            f"context_length={len(self.formatted_context)})"
        )


class SmartHomeRetriever:
    """
    GraphRAG retriever for smart home knowledge graph.

    This class provides high-level retrieval methods that:
    1. Execute appropriate Cypher queries
    2. Process and validate results
    3. Format context for LLM consumption

    Usage:
        retriever = SmartHomeRetriever()

        # Get context for a room
        result = retriever.get_room_context("living room")
        print(result.formatted_context)

        # Find devices that can dim
        result = retriever.get_devices_by_capability(["dim"])
        print(result.formatted_context)

    Teaching Notes:
        - Each method corresponds to a retrieval strategy
        - formatted_context is what gets injected into LLM prompts
        - raw_results preserves structure for validation
    """

    def __init__(self, connection: Optional[Neo4jConnection] = None):
        """
        Initialize retriever with a Neo4j connection.

        Args:
            connection: Neo4j connection instance. If None, uses default.
        """
        self.conn = connection or get_connection()
        self.queries = SmartHomeQueries()

    # =========================================
    # CORE RETRIEVAL METHODS
    # =========================================

    def get_room_context(self, room_name: str) -> RetrievalResult:
        """
        Get comprehensive context for a specific room.

        This retrieves:
        - Room details
        - All devices in the room
        - Device capabilities
        - Applicable scenes
        - Adjacent rooms

        Args:
            room_name: Name of the room (partial match supported)

        Returns:
            RetrievalResult with formatted context for LLM

        Example:
            >>> result = retriever.get_room_context("living")
            >>> print(result.formatted_context)
            # Room: Living Room (entertainment, Ground Floor)
            # Devices:
            #   - Smart TV: power, volume, input_select
            #   - Ceiling Light: power, dim, color
            # ...
        """
        query = self.queries.get_context_for_room_action()
        results = self.conn.query(query, {"room_name": room_name})

        # Format for LLM
        formatted = self._format_room_context(results)

        return RetrievalResult(
            strategy=RetrievalStrategy.ROOM_CONTEXT,
            query_params={"room_name": room_name},
            raw_results=results,
            formatted_context=formatted,
            metadata={"device_count": self._count_devices(results)}
        )

    def get_devices_by_capability(
        self,
        capabilities: list[str],
        room_filter: Optional[str] = None
    ) -> RetrievalResult:
        """
        Find all devices that have specific capabilities.

        Args:
            capabilities: List of capability names (e.g., ["dim", "color"])
            room_filter: Optional room name to filter results

        Returns:
            RetrievalResult with devices grouped by room

        Example:
            >>> result = retriever.get_devices_by_capability(["dim"])
            >>> # Returns all dimmable devices in the home
        """
        query = self.queries.get_context_for_capability_action()
        results = self.conn.query(query, {"capabilities": capabilities})

        # Apply room filter if specified
        if room_filter:
            results = [
                r for r in results
                if room_filter.lower() in r.get("device_context", {}).get("room", "").lower()
            ]

        formatted = self._format_capability_context(results, capabilities)

        return RetrievalResult(
            strategy=RetrievalStrategy.CAPABILITY_SEARCH,
            query_params={"capabilities": capabilities, "room_filter": room_filter},
            raw_results=results,
            formatted_context=formatted,
            metadata={"device_count": len(results)}
        )

    def get_scene_context(self, scene_name: str) -> RetrievalResult:
        """
        Get details about a predefined scene.

        Args:
            scene_name: Name of the scene (partial match supported)

        Returns:
            RetrievalResult with scene configuration

        Example:
            >>> result = retriever.get_scene_context("movie")
            >>> # Returns Movie Night scene with all device actions
        """
        query = self.queries.get_scene_details()
        results = self.conn.query(query, {"scene_name": scene_name})

        formatted = self._format_scene_context(results)

        return RetrievalResult(
            strategy=RetrievalStrategy.SCENE_LOOKUP,
            query_params={"scene_name": scene_name},
            raw_results=results,
            formatted_context=formatted,
            metadata={"scenes_found": len(results)}
        )

    def search_by_keywords(self, keywords: list[str]) -> RetrievalResult:
        """
        Perform fuzzy search across all entity types.

        Useful for disambiguating vague user requests.

        Args:
            keywords: List of search terms

        Returns:
            RetrievalResult with matched entities by type

        Example:
            >>> result = retriever.search_by_keywords(["cozy", "relax"])
            >>> # Finds scenes, rooms, devices matching these terms
        """
        query = self.queries.search_by_keywords()
        results = self.conn.query(query, {"keywords": keywords})

        formatted = self._format_search_results(results, keywords)

        return RetrievalResult(
            strategy=RetrievalStrategy.KEYWORD_SEARCH,
            query_params={"keywords": keywords},
            raw_results=results,
            formatted_context=formatted,
            metadata={"search_terms": keywords}
        )

    def get_multi_room_context(self, room_names: list[str]) -> RetrievalResult:
        """
        Get context spanning multiple rooms.

        Args:
            room_names: List of room names to include

        Returns:
            RetrievalResult with combined room contexts

        Example:
            >>> result = retriever.get_multi_room_context(["living", "kitchen"])
            >>> # Returns devices and capabilities for both rooms
        """
        query = self.queries.get_context_for_multi_room()
        results = self.conn.query(query, {"room_names": room_names})

        formatted = self._format_multi_room_context(results)

        return RetrievalResult(
            strategy=RetrievalStrategy.MULTI_ROOM,
            query_params={"room_names": room_names},
            raw_results=results,
            formatted_context=formatted,
            metadata={"rooms_found": len(results)}
        )

    # =========================================
    # CONVENIENCE METHODS
    # =========================================

    def get_all_rooms(self) -> list[dict]:
        """Get a simple list of all rooms."""
        query = self.queries.get_all_rooms()
        return self.conn.query(query)

    def get_all_devices(self) -> list[dict]:
        """Get a simple list of all devices."""
        query = self.queries.get_all_devices()
        return self.conn.query(query)

    def get_all_capabilities(self) -> list[dict]:
        """Get a simple list of all capabilities."""
        query = self.queries.get_all_capabilities()
        return self.conn.query(query)

    def get_all_scenes(self) -> list[dict]:
        """Get a simple list of all scenes."""
        query = self.queries.get_all_scenes()
        return self.conn.query(query)

    def get_graph_stats(self) -> dict:
        """Get statistics about the knowledge graph."""
        query = self.queries.get_graph_stats()
        result = self.conn.query_single(query)
        return result.get("stats", {}) if result else {}

    # =========================================
    # FORMATTING METHODS
    # =========================================

    def _format_room_context(self, results: list[dict]) -> str:
        """
        Format room context for LLM consumption.

        Teaching Point:
            The formatting matters! LLMs understand structured
            text better than raw JSON for reasoning tasks.
        """
        if not results:
            return "No matching room found."

        lines = ["# Smart Home Context\n"]

        for row in results:
            ctx = row.get("context", row)

            # Room info
            room = ctx.get("room", {})
            lines.append(f"## Room: {room.get('name', 'Unknown')}")
            lines.append(f"- Type: {room.get('type', 'N/A')}")
            lines.append(f"- Floor: {room.get('floor', 'N/A')}")

            # Adjacent rooms
            adjacent = ctx.get("adjacent_rooms", [])
            if adjacent and adjacent[0]:  # Filter out None
                lines.append(f"- Adjacent to: {', '.join(filter(None, adjacent))}")

            # Devices
            devices = ctx.get("devices", [])
            if devices:
                lines.append(f"\n### Devices ({len(devices)} total)")
                for device in devices:
                    caps = device.get("capabilities", [])
                    cap_names = [c.get("name", c) if isinstance(c, dict) else c for c in caps]
                    status_emoji = "✓" if device.get("status") == "online" else "✗"
                    lines.append(
                        f"- **{device.get('name')}** ({device.get('type')}) {status_emoji}"
                    )
                    if cap_names:
                        lines.append(f"  - Capabilities: {', '.join(cap_names)}")

            # Scenes
            scenes = ctx.get("scenes", [])
            if scenes:
                lines.append(f"\n### Available Scenes")
                for scene in scenes:
                    if scene.get("name"):
                        lines.append(f"- **{scene.get('name')}**: {scene.get('description', 'N/A')}")
                        actions = scene.get("actions", [])
                        if actions:
                            action_strs = [
                                f"{a.get('device')}: {a.get('action')}"
                                for a in actions if a.get('device')
                            ]
                            if action_strs:
                                lines.append(f"  - Actions: {'; '.join(action_strs)}")

        return "\n".join(lines)

    def _format_capability_context(
        self,
        results: list[dict],
        capabilities: list[str]
    ) -> str:
        """Format capability search results."""
        if not results:
            return f"No devices found with capabilities: {', '.join(capabilities)}"

        lines = [f"# Devices with capabilities: {', '.join(capabilities)}\n"]

        # Group by room
        by_room: dict[str, list] = {}
        for row in results:
            ctx = row.get("device_context", row)
            room = ctx.get("room", "Unknown")
            if room not in by_room:
                by_room[room] = []
            by_room[room].append(ctx)

        for room, devices in by_room.items():
            lines.append(f"\n## {room}")
            for device in devices:
                lines.append(f"- **{device.get('device_name')}** ({device.get('device_type')})")
                caps = device.get("capabilities", [])
                for cap in caps:
                    if isinstance(cap, dict):
                        lines.append(f"  - {cap.get('name')}: {cap.get('description', '')}")
                        params = cap.get("parameters", [])
                        if params:
                            lines.append(f"    Parameters: {', '.join(params)}")

        return "\n".join(lines)

    def _format_scene_context(self, results: list[dict]) -> str:
        """Format scene details."""
        if not results:
            return "No matching scene found."

        lines = ["# Scene Details\n"]

        for scene in results:
            lines.append(f"## {scene.get('scene_name', 'Unknown Scene')}")
            lines.append(f"- Description: {scene.get('description', 'N/A')}")
            lines.append(f"- Mood: {scene.get('mood', 'N/A')}")

            rooms = scene.get("applicable_rooms", [])
            if rooms:
                lines.append(f"- Applies to: {', '.join(filter(None, rooms))}")

            typical = scene.get("typical_actions", [])
            if typical:
                lines.append(f"- Typical actions: {', '.join(typical)}")

            device_actions = scene.get("device_actions", [])
            if device_actions:
                lines.append("\n### Device Actions:")
                for action in device_actions:
                    if action.get("device"):
                        lines.append(f"- {action['device']}: {action.get('action', 'N/A')}")

        return "\n".join(lines)

    def _format_search_results(self, results: list[dict], keywords: list[str]) -> str:
        """Format keyword search results."""
        if not results:
            return f"No matches found for: {', '.join(keywords)}"

        lines = [f"# Search Results for: {', '.join(keywords)}\n"]

        for row in results:
            search = row.get("search_results", row)

            # Rooms
            rooms = search.get("rooms", [])
            if rooms:
                lines.append("## Matching Rooms")
                for r in rooms:
                    lines.append(f"- {r.get('name', 'Unknown')}")

            # Devices
            devices = search.get("devices", [])
            if devices:
                lines.append("\n## Matching Devices")
                for d in devices:
                    lines.append(f"- {d.get('name', 'Unknown')} ({d.get('device_type', 'N/A')})")

            # Scenes
            scenes = search.get("scenes", [])
            if scenes:
                lines.append("\n## Matching Scenes")
                for s in scenes:
                    lines.append(f"- {s.get('name', 'Unknown')} (mood: {s.get('mood', 'N/A')})")

            # Capabilities
            caps = search.get("capabilities", [])
            if caps:
                lines.append("\n## Matching Capabilities")
                for c in caps:
                    if c.get("name"):
                        lines.append(f"- {c.get('name')}")

        return "\n".join(lines)

    def _format_multi_room_context(self, results: list[dict]) -> str:
        """Format multi-room context."""
        if not results:
            return "No matching rooms found."

        lines = ["# Multi-Room Context\n"]

        for row in results:
            ctx = row.get("room_context", row)
            lines.append(f"\n## {ctx.get('room', 'Unknown')} ({ctx.get('floor', 'N/A')})")

            devices = ctx.get("devices", [])
            if devices:
                for device in devices:
                    caps = device.get("capabilities", [])
                    lines.append(f"- **{device.get('name')}** ({device.get('type')})")
                    if caps:
                        lines.append(f"  - Capabilities: {', '.join(caps)}")

        return "\n".join(lines)

    def _count_devices(self, results: list[dict]) -> int:
        """Count total devices in results."""
        count = 0
        for row in results:
            ctx = row.get("context", row)
            devices = ctx.get("devices", [])
            count += len(devices)
        return count


# Example usage and testing
if __name__ == "__main__":
    print("Testing Smart Home Retriever")
    print("=" * 50)

    try:
        retriever = SmartHomeRetriever()

        # Test graph stats
        print("\n📊 Graph Statistics:")
        stats = retriever.get_graph_stats()
        if stats:
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("  No data in graph. Run seed_graph.cypher first!")

        # Test room context retrieval
        print("\n🏠 Testing Room Context Retrieval:")
        result = retriever.get_room_context("living")
        print(f"  Strategy: {result.strategy.value}")
        print(f"  Devices found: {result.metadata.get('device_count', 0)}")
        print("\n--- Formatted Context ---")
        print(result.formatted_context[:500] + "..." if len(result.formatted_context) > 500 else result.formatted_context)

        # Test capability search
        print("\n\n💡 Testing Capability Search (dim):")
        result = retriever.get_devices_by_capability(["dim"])
        print(f"  Devices with 'dim': {result.metadata.get('device_count', 0)}")

        # Test scene lookup
        print("\n🎬 Testing Scene Lookup (movie):")
        result = retriever.get_scene_context("movie")
        print(f"  Scenes found: {result.metadata.get('scenes_found', 0)}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Neo4j is running and seed data is loaded!")
        print("  1. Start Neo4j: docker run -p 7474:7474 -p 7687:7687 neo4j")
        print("  2. Load data: Run seed_graph.cypher in Neo4j Browser")
