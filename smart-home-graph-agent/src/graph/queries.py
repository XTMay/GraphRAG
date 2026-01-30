"""
Cypher Query Templates
======================

Centralized query templates for the Smart Home Knowledge Graph.
These queries demonstrate various graph retrieval patterns.

Teaching Points:
- Parameterized queries prevent injection
- MATCH patterns follow relationships
- OPTIONAL MATCH handles missing data gracefully
- COLLECT aggregates related nodes
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SmartHomeQueries:
    """
    Collection of Cypher query templates for smart home graph.

    All queries use parameterized inputs for safety and performance.

    Usage:
        queries = SmartHomeQueries()
        cypher = queries.get_room_with_devices()
        results = conn.query(cypher, {"room_name": "Living Room"})

    Teaching Notes:
        - $variable syntax is for Neo4j parameters
        - Parameters are passed separately from query string
        - This prevents Cypher injection attacks
    """

    # =========================================
    # BASIC QUERIES - Single Entity Retrieval
    # =========================================

    @staticmethod
    def get_all_rooms() -> str:
        """Get all rooms with basic info."""
        return """
            MATCH (r:Room)
            RETURN r.name AS name,
                   r.floor AS floor,
                   r.type AS type,
                   r.description AS description
            ORDER BY r.floor, r.name
        """

    @staticmethod
    def get_all_devices() -> str:
        """Get all devices with their rooms."""
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)
            RETURN d.device_id AS device_id,
                   d.name AS name,
                   d.device_type AS type,
                   d.brand AS brand,
                   d.status AS status,
                   r.name AS room
            ORDER BY r.name, d.name
        """

    @staticmethod
    def get_all_capabilities() -> str:
        """Get all available capabilities."""
        return """
            MATCH (c:Capability)
            RETURN c.name AS name,
                   c.description AS description,
                   c.parameters AS parameters,
                   c.example AS example
            ORDER BY c.name
        """

    @staticmethod
    def get_all_scenes() -> str:
        """Get all available scenes."""
        return """
            MATCH (s:Scene)
            OPTIONAL MATCH (s)-[:APPLIES_TO]->(r:Room)
            RETURN s.name AS name,
                   s.description AS description,
                   s.mood AS mood,
                   s.typical_actions AS typical_actions,
                   collect(DISTINCT r.name) AS rooms
            ORDER BY s.name
        """

    # =========================================
    # ROOM-CENTRIC QUERIES
    # =========================================

    @staticmethod
    def get_room_with_devices() -> str:
        """
        Get a room and all its devices with capabilities.

        Parameters:
            $room_name: Name of the room (case-insensitive partial match)

        Teaching Point:
            This query demonstrates a 2-hop traversal:
            Room -> Device -> Capability
        """
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)
            WHERE toLower(r.name) CONTAINS toLower($room_name)
            OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)
            WITH r, d, collect(c.name) AS capabilities
            RETURN r.name AS room_name,
                   r.type AS room_type,
                   r.floor AS floor,
                   collect({
                       device_id: d.device_id,
                       name: d.name,
                       type: d.device_type,
                       brand: d.brand,
                       status: d.status,
                       capabilities: capabilities
                   }) AS devices
        """

    @staticmethod
    def get_room_topology() -> str:
        """
        Get room and its adjacent rooms.

        Parameters:
            $room_name: Name of the room

        Teaching Point:
            ADJACENT_TO relationship shows spatial relationships.
        """
        return """
            MATCH (r:Room)
            WHERE toLower(r.name) CONTAINS toLower($room_name)
            OPTIONAL MATCH (r)-[:ADJACENT_TO]->(adjacent:Room)
            RETURN r.name AS room,
                   r.floor AS floor,
                   collect(adjacent.name) AS adjacent_rooms
        """

    # =========================================
    # DEVICE-CENTRIC QUERIES
    # =========================================

    @staticmethod
    def get_device_details() -> str:
        """
        Get full details of a specific device.

        Parameters:
            $device_name: Name of the device (partial match)
        """
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)
            WHERE toLower(d.name) CONTAINS toLower($device_name)
            OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)
            RETURN d.device_id AS device_id,
                   d.name AS name,
                   d.device_type AS type,
                   d.brand AS brand,
                   d.model AS model,
                   d.status AS status,
                   r.name AS room,
                   collect({
                       name: c.name,
                       description: c.description,
                       parameters: c.parameters
                   }) AS capabilities
        """

    @staticmethod
    def get_devices_by_type() -> str:
        """
        Get all devices of a specific type.

        Parameters:
            $device_type: Type of device (e.g., "light", "speaker")
        """
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)
            WHERE toLower(d.device_type) = toLower($device_type)
            OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)
            RETURN d.device_id AS device_id,
                   d.name AS name,
                   d.brand AS brand,
                   d.status AS status,
                   r.name AS room,
                   collect(c.name) AS capabilities
            ORDER BY r.name
        """

    @staticmethod
    def get_devices_with_capability() -> str:
        """
        Find all devices that have a specific capability.

        Parameters:
            $capability_name: Name of capability (e.g., "dim", "play_music")

        Teaching Point:
            This query finds devices by their capabilities,
            which is useful for intent-based retrieval.
        """
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)-[:HAS_CAPABILITY]->(c:Capability)
            WHERE toLower(c.name) = toLower($capability_name)
            RETURN d.device_id AS device_id,
                   d.name AS name,
                   d.device_type AS type,
                   r.name AS room,
                   c.description AS capability_description,
                   c.parameters AS parameters
            ORDER BY r.name
        """

    # =========================================
    # SCENE-RELATED QUERIES
    # =========================================

    @staticmethod
    def get_scene_details() -> str:
        """
        Get full details of a scene including devices it controls.

        Parameters:
            $scene_name: Name of scene (partial match)

        Teaching Point:
            Scenes are pre-defined configurations that span multiple devices.
            The USES_DEVICE relationship includes action metadata.
        """
        return """
            MATCH (s:Scene)
            WHERE toLower(s.name) CONTAINS toLower($scene_name)
            OPTIONAL MATCH (s)-[:APPLIES_TO]->(r:Room)
            OPTIONAL MATCH (s)-[uses:USES_DEVICE]->(d:Device)
            RETURN s.name AS scene_name,
                   s.description AS description,
                   s.mood AS mood,
                   s.typical_actions AS typical_actions,
                   collect(DISTINCT r.name) AS applicable_rooms,
                   collect(DISTINCT {
                       device: d.name,
                       device_type: d.device_type,
                       action: uses.action
                   }) AS device_actions
        """

    @staticmethod
    def get_scenes_for_room() -> str:
        """
        Get all scenes applicable to a specific room.

        Parameters:
            $room_name: Name of room
        """
        return """
            MATCH (s:Scene)-[:APPLIES_TO]->(r:Room)
            WHERE toLower(r.name) CONTAINS toLower($room_name)
            OPTIONAL MATCH (s)-[uses:USES_DEVICE]->(d:Device)
            RETURN s.name AS scene_name,
                   s.description AS description,
                   s.mood AS mood,
                   collect({device: d.name, action: uses.action}) AS actions
        """

    @staticmethod
    def get_scenes_by_mood() -> str:
        """
        Find scenes by mood/atmosphere.

        Parameters:
            $mood: Mood keyword (e.g., "relaxed", "energetic")
        """
        return """
            MATCH (s:Scene)
            WHERE toLower(s.mood) CONTAINS toLower($mood)
                  OR toLower(s.description) CONTAINS toLower($mood)
            OPTIONAL MATCH (s)-[:APPLIES_TO]->(r:Room)
            RETURN s.name AS scene_name,
                   s.description AS description,
                   s.mood AS mood,
                   s.typical_actions AS typical_actions,
                   collect(r.name) AS rooms
        """

    # =========================================
    # COMPLEX RETRIEVAL QUERIES (GraphRAG)
    # =========================================

    @staticmethod
    def get_context_for_room_action() -> str:
        """
        Comprehensive context retrieval for room-based actions.
        Returns room, all devices, their capabilities, and relevant scenes.

        Parameters:
            $room_name: Target room name

        Teaching Point:
            This is a "context gathering" query that retrieves
            everything needed for an LLM to reason about actions.
            It combines multiple patterns in one query.
        """
        return """
            // Get room and devices with capabilities
            MATCH (r:Room)-[:CONTAINS]->(d:Device)
            WHERE toLower(r.name) CONTAINS toLower($room_name)
            OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)

            // Collect device info
            WITH r, d, collect({
                name: c.name,
                description: c.description,
                parameters: c.parameters
            }) AS caps

            WITH r, collect({
                device_id: d.device_id,
                name: d.name,
                type: d.device_type,
                brand: d.brand,
                status: d.status,
                capabilities: caps
            }) AS devices

            // Get relevant scenes for this room
            OPTIONAL MATCH (scene:Scene)-[:APPLIES_TO]->(r)
            OPTIONAL MATCH (scene)-[uses:USES_DEVICE]->(sd:Device)

            WITH r, devices, scene, collect({
                device: sd.name,
                action: uses.action
            }) AS scene_actions

            WITH r, devices, collect({
                name: scene.name,
                description: scene.description,
                mood: scene.mood,
                actions: scene_actions
            }) AS scenes

            // Get adjacent rooms
            OPTIONAL MATCH (r)-[:ADJACENT_TO]->(adj:Room)

            WITH r, devices, scenes, collect(adj.name) AS adjacent_rooms

            RETURN {
                room: {
                    name: r.name,
                    type: r.type,
                    floor: r.floor
                },
                devices: devices,
                scenes: [s IN scenes WHERE s.name IS NOT NULL],
                adjacent_rooms: adjacent_rooms
            } AS context
        """

    @staticmethod
    def get_context_for_capability_action() -> str:
        """
        Context retrieval based on capability requirements.
        Finds all devices with specific capabilities.

        Parameters:
            $capabilities: List of required capability names

        Teaching Point:
            When user says "dim the lights", we need to find
            all devices with "dim" capability across the home.
        """
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)-[:HAS_CAPABILITY]->(c:Capability)
            WHERE c.name IN $capabilities

            WITH r, d, collect({
                name: c.name,
                description: c.description,
                parameters: c.parameters
            }) AS matching_caps

            RETURN {
                room: r.name,
                device_id: d.device_id,
                device_name: d.name,
                device_type: d.device_type,
                status: d.status,
                capabilities: matching_caps
            } AS device_context
            ORDER BY r.name
        """

    @staticmethod
    def get_context_for_multi_room() -> str:
        """
        Context for actions spanning multiple rooms.

        Parameters:
            $room_names: List of room names

        Teaching Point:
            Commands like "prepare the house for a party"
            may affect multiple rooms simultaneously.
        """
        return """
            MATCH (r:Room)-[:CONTAINS]->(d:Device)
            WHERE any(name IN $room_names WHERE toLower(r.name) CONTAINS toLower(name))
            OPTIONAL MATCH (d)-[:HAS_CAPABILITY]->(c:Capability)

            WITH r, d, collect(c.name) AS capabilities

            WITH r, collect({
                device_id: d.device_id,
                name: d.name,
                type: d.device_type,
                status: d.status,
                capabilities: capabilities
            }) AS devices

            RETURN {
                room: r.name,
                floor: r.floor,
                devices: devices
            } AS room_context
            ORDER BY r.floor, r.name
        """

    @staticmethod
    def search_by_keywords() -> str:
        """
        Fuzzy search across rooms, devices, and scenes.

        Parameters:
            $keywords: Search terms (will match against names/descriptions)

        Teaching Point:
            Natural language often contains vague references.
            This query provides broad matching for disambiguation.
        """
        return """
            // Search rooms
            OPTIONAL MATCH (r:Room)
            WHERE any(kw IN $keywords WHERE
                toLower(r.name) CONTAINS toLower(kw) OR
                toLower(r.type) CONTAINS toLower(kw) OR
                toLower(r.description) CONTAINS toLower(kw)
            )

            WITH collect(DISTINCT {type: 'room', name: r.name, match_type: 'room'}) AS room_matches

            // Search devices
            OPTIONAL MATCH (d:Device)
            WHERE any(kw IN $keywords WHERE
                toLower(d.name) CONTAINS toLower(kw) OR
                toLower(d.device_type) CONTAINS toLower(kw)
            )

            WITH room_matches, collect(DISTINCT {type: 'device', name: d.name, device_type: d.device_type}) AS device_matches

            // Search scenes
            OPTIONAL MATCH (s:Scene)
            WHERE any(kw IN $keywords WHERE
                toLower(s.name) CONTAINS toLower(kw) OR
                toLower(s.mood) CONTAINS toLower(kw) OR
                toLower(s.description) CONTAINS toLower(kw)
            )

            WITH room_matches, device_matches, collect(DISTINCT {type: 'scene', name: s.name, mood: s.mood}) AS scene_matches

            // Search capabilities
            OPTIONAL MATCH (c:Capability)
            WHERE any(kw IN $keywords WHERE
                toLower(c.name) CONTAINS toLower(kw) OR
                toLower(c.description) CONTAINS toLower(kw)
            )

            RETURN {
                rooms: [r IN room_matches WHERE r.name IS NOT NULL],
                devices: [d IN device_matches WHERE d.name IS NOT NULL],
                scenes: [s IN scene_matches WHERE s.name IS NOT NULL],
                capabilities: collect(DISTINCT {type: 'capability', name: c.name})
            } AS search_results
        """

    # =========================================
    # UTILITY QUERIES
    # =========================================

    @staticmethod
    def get_graph_stats() -> str:
        """Get statistics about the knowledge graph."""
        return """
            MATCH (r:Room) WITH count(r) AS rooms
            MATCH (d:Device) WITH rooms, count(d) AS devices
            MATCH (c:Capability) WITH rooms, devices, count(c) AS capabilities
            MATCH (s:Scene) WITH rooms, devices, capabilities, count(s) AS scenes
            MATCH ()-[rel]->() WITH rooms, devices, capabilities, scenes, count(rel) AS relationships
            RETURN {
                rooms: rooms,
                devices: devices,
                capabilities: capabilities,
                scenes: scenes,
                total_relationships: relationships
            } AS stats
        """

    @staticmethod
    def clear_all_data() -> str:
        """
        Delete all nodes and relationships.
        USE WITH CAUTION!
        """
        return """
            MATCH (n)
            DETACH DELETE n
        """


# Convenience instance
queries = SmartHomeQueries()


if __name__ == "__main__":
    # Print all available queries for reference
    print("Available Smart Home Queries")
    print("=" * 50)

    q = SmartHomeQueries()
    methods = [m for m in dir(q) if not m.startswith('_')]

    for method in methods:
        func = getattr(q, method)
        if callable(func):
            doc = func.__doc__ or "No description"
            first_line = doc.strip().split('\n')[0]
            print(f"\n{method}()")
            print(f"  {first_line}")
