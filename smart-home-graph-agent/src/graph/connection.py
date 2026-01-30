"""
Neo4j Connection Module
=======================

Provides connection management for Neo4j database.
Supports both local Docker instances and Neo4j Aura (cloud).

Teaching Points:
- Connection pooling (handled by driver)
- Environment-based configuration
- Health checks before operations
"""

import os
from contextlib import contextmanager
from typing import Any, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError


# Load environment variables
load_dotenv()


class Neo4jConnection:
    """
    Neo4j connection manager with health checking.

    Usage:
        # Option 1: Using context manager (recommended)
        with Neo4jConnection() as conn:
            result = conn.query("MATCH (n) RETURN count(n)")

        # Option 2: Manual management
        conn = Neo4jConnection()
        conn.connect()
        result = conn.query("MATCH (n) RETURN count(n)")
        conn.close()

    Teaching Notes:
        - The driver manages a connection pool internally
        - Each query opens a session, executes, and closes
        - Transactions ensure ACID properties
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j"
    ):
        """
        Initialize connection parameters.

        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            user: Database username
            password: Database password
            database: Database name (default: "neo4j")
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database
        self._driver: Optional[Driver] = None

    def connect(self) -> "Neo4jConnection":
        """
        Establish connection to Neo4j.

        Returns:
            Self for method chaining

        Raises:
            AuthError: If credentials are invalid
            ServiceUnavailable: If Neo4j is not reachable
        """
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        return self

    def close(self) -> None:
        """Close the database connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> "Neo4jConnection":
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    @property
    def driver(self) -> Driver:
        """Get the driver, connecting if necessary."""
        if self._driver is None:
            self.connect()
        return self._driver

    def verify_connectivity(self) -> bool:
        """
        Test if the database is reachable.

        Returns:
            True if connection is successful

        Teaching Point:
            Always verify connectivity before running queries
            in production applications.
        """
        try:
            self.driver.verify_connectivity()
            return True
        except (ServiceUnavailable, AuthError) as e:
            print(f"Connection failed: {e}")
            return False

    def health_check(self) -> dict[str, Any]:
        """
        Perform a comprehensive health check.

        Returns:
            Dictionary with health status and database info
        """
        try:
            with self.driver.session(database=self.database) as session:
                # Get basic database info
                result = session.run("""
                    CALL dbms.components() YIELD name, versions, edition
                    RETURN name, versions[0] AS version, edition
                """)
                record = result.single()

                # Count nodes and relationships
                counts = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH ()-[r]->()
                    RETURN count(DISTINCT n) AS nodes, count(DISTINCT r) AS relationships
                """).single()

                return {
                    "status": "healthy",
                    "database": self.database,
                    "name": record["name"] if record else "unknown",
                    "version": record["version"] if record else "unknown",
                    "edition": record["edition"] if record else "unknown",
                    "node_count": counts["nodes"] if counts else 0,
                    "relationship_count": counts["relationships"] if counts else 0,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def query(
        self,
        cypher: str,
        parameters: Optional[dict] = None,
        fetch_all: bool = True
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            cypher: Cypher query string
            parameters: Query parameters (for parameterized queries)
            fetch_all: If True, return all results; if False, return first only

        Returns:
            List of result dictionaries

        Teaching Point:
            ALWAYS use parameterized queries to prevent Cypher injection.
            Bad:  f"MATCH (n:Room {{name: '{user_input}'}})"
            Good: "MATCH (n:Room {name: $room_name})", {"room_name": user_input}
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, parameters or {})
            if fetch_all:
                return [dict(record) for record in result]
            else:
                record = result.single()
                return [dict(record)] if record else []

    def query_single(
        self,
        cypher: str,
        parameters: Optional[dict] = None
    ) -> Optional[dict[str, Any]]:
        """
        Execute a query and return a single result.

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            Single result dictionary or None
        """
        results = self.query(cypher, parameters, fetch_all=False)
        return results[0] if results else None

    @contextmanager
    def session(self):
        """
        Get a session for complex transactions.

        Usage:
            with conn.session() as session:
                with session.begin_transaction() as tx:
                    tx.run("CREATE (n:Node {name: $name})", name="test")
                    tx.run("CREATE (m:Node {name: $name})", name="test2")
                    # Commits automatically on exit, rolls back on exception

        Teaching Point:
            Use explicit transactions when you need multiple
            operations to succeed or fail together (atomicity).
        """
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()

    def run_cypher_file(self, file_path: str) -> dict[str, Any]:
        """
        Execute a Cypher script file.

        Args:
            file_path: Path to .cypher file

        Returns:
            Summary of execution results

        Note:
            This splits on semicolons and runs each statement.
            For production, consider using APOC or neo4j-admin.
        """
        with open(file_path, 'r') as f:
            content = f.read()

        # Remove comments and empty lines
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('//'):
                lines.append(line)

        # Split into statements
        statements = ''.join(lines).split(';')
        statements = [s.strip() for s in statements if s.strip()]

        executed = 0
        errors = []

        with self.session() as session:
            for stmt in statements:
                try:
                    session.run(stmt)
                    executed += 1
                except Exception as e:
                    errors.append({"statement": stmt[:100], "error": str(e)})

        return {
            "total_statements": len(statements),
            "executed": executed,
            "errors": errors
        }


# Singleton connection for simple usage
_default_connection: Optional[Neo4jConnection] = None


def get_connection() -> Neo4jConnection:
    """
    Get a shared connection instance.

    Usage:
        from src.graph import get_connection

        conn = get_connection()
        result = conn.query("MATCH (n) RETURN n LIMIT 5")

    Teaching Point:
        Singleton pattern avoids creating multiple driver instances,
        which is wasteful since the driver already pools connections.
    """
    global _default_connection
    if _default_connection is None:
        _default_connection = Neo4jConnection()
        _default_connection.connect()
    return _default_connection


def close_connection() -> None:
    """Close the shared connection."""
    global _default_connection
    if _default_connection is not None:
        _default_connection.close()
        _default_connection = None


# Example usage and testing
if __name__ == "__main__":
    print("Testing Neo4j Connection...")
    print("-" * 40)

    # Test connection
    with Neo4jConnection() as conn:
        # Health check
        health = conn.health_check()
        print(f"Health Check: {health['status']}")

        if health['status'] == 'healthy':
            print(f"  Database: {health['database']}")
            print(f"  Version: {health['version']}")
            print(f"  Edition: {health['edition']}")
            print(f"  Nodes: {health['node_count']}")
            print(f"  Relationships: {health['relationship_count']}")
        else:
            print(f"  Error: {health.get('error', 'Unknown error')}")
            print("\n⚠️  Make sure Neo4j is running!")
            print("   Docker: docker run -p 7474:7474 -p 7687:7687 neo4j")
