"""PathFinder - SQL recursive CTE-based graph traversal for relationship networks.

Finds paths between people in the network using PostgreSQL/SQLite recursive CTEs.
Calculates path strength based on relationship types and hop decay.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .mock_data import RELATIONSHIP_WEIGHTS, RelationshipType

logger = logging.getLogger(__name__)

# Path strength decays with each hop
HOP_DECAY_FACTOR = 0.7


@dataclass
class PathNode:
    """A node (person) in a connection path."""

    person_id: str
    name: str
    title: str
    company: str
    email: Optional[str] = None


@dataclass
class PathEdge:
    """An edge (relationship) in a connection path."""

    from_person_id: str
    to_person_id: str
    relationship_type: str
    strength: float
    context: Optional[str] = None


@dataclass
class ConnectionPath:
    """A complete path from source to target person."""

    path_id: str
    source_person: PathNode
    target_person: PathNode
    nodes: list[PathNode]
    edges: list[PathEdge]
    total_hops: int
    path_strength: float
    introduction_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "path_id": self.path_id,
            "source": {
                "id": self.source_person.person_id,
                "name": self.source_person.name,
                "title": self.source_person.title,
                "company": self.source_person.company,
            },
            "target": {
                "id": self.target_person.person_id,
                "name": self.target_person.name,
                "title": self.target_person.title,
                "company": self.target_person.company,
            },
            "nodes": [
                {
                    "id": n.person_id,
                    "name": n.name,
                    "title": n.title,
                    "company": n.company,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "from": e.from_person_id,
                    "to": e.to_person_id,
                    "type": e.relationship_type,
                    "strength": e.strength,
                    "context": e.context,
                }
                for e in self.edges
            ],
            "total_hops": self.total_hops,
            "path_strength": round(self.path_strength, 3),
            "introduction_chain": self.introduction_chain,
        }


@dataclass
class NetworkGraph:
    """A subgraph of the network around a person."""

    center_person: PathNode
    nodes: list[PathNode]
    edges: list[PathEdge]
    depth: int

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "center": {
                "id": self.center_person.person_id,
                "name": self.center_person.name,
                "title": self.center_person.title,
                "company": self.center_person.company,
            },
            "nodes": [
                {
                    "id": n.person_id,
                    "name": n.name,
                    "title": n.title,
                    "company": n.company,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.from_person_id,
                    "target": e.to_person_id,
                    "type": e.relationship_type,
                    "strength": e.strength,
                }
                for e in self.edges
            ],
            "depth": self.depth,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }


class PathFinder:
    """
    Finds connection paths between people using SQL recursive CTEs.

    Supports both SQLite and PostgreSQL databases with appropriate syntax.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize the PathFinder.

        Args:
            db_session: Optional database session. If None, uses mock data.
        """
        self.db_session = db_session
        self._use_mock = db_session is None

    async def find_paths(
        self,
        from_person_id: str,
        to_person_id: str,
        max_hops: int = 3,
    ) -> list[ConnectionPath]:
        """
        Find all paths between two people up to max_hops.

        Args:
            from_person_id: Starting person UUID
            to_person_id: Target person UUID
            max_hops: Maximum number of hops to search (default 3)

        Returns:
            List of ConnectionPath objects sorted by path_strength descending
        """
        if self._use_mock:
            return await self._find_paths_mock(from_person_id, to_person_id, max_hops)

        return await self._find_paths_sql(from_person_id, to_person_id, max_hops)

    async def _find_paths_sql(
        self,
        from_person_id: str,
        to_person_id: str,
        max_hops: int,
    ) -> list[ConnectionPath]:
        """Find paths using SQL recursive CTE."""
        # SQLite-compatible recursive CTE for path finding
        # Note: This finds all paths up to max_hops between two nodes
        query = text("""
            WITH RECURSIVE paths AS (
                -- Base case: start from the source person
                SELECT
                    r.person_a_id AS current_id,
                    r.person_b_id AS next_id,
                    r.relationship_type,
                    r.strength,
                    r.context,
                    r.person_a_id || ',' || r.person_b_id AS path,
                    1 AS depth,
                    r.strength AS path_strength
                FROM relationships r
                WHERE r.person_a_id = :from_id

                UNION ALL

                SELECT
                    r.person_a_id AS current_id,
                    r.person_b_id AS next_id,
                    r.relationship_type,
                    r.strength,
                    r.context,
                    r.person_b_id || ',' || r.person_a_id AS path,
                    1 AS depth,
                    r.strength AS path_strength
                FROM relationships r
                WHERE r.person_b_id = :from_id

                UNION ALL

                -- Recursive case: extend paths
                SELECT
                    p.next_id AS current_id,
                    CASE
                        WHEN r.person_a_id = p.next_id THEN r.person_b_id
                        ELSE r.person_a_id
                    END AS next_id,
                    r.relationship_type,
                    r.strength,
                    r.context,
                    p.path || ',' || CASE
                        WHEN r.person_a_id = p.next_id THEN r.person_b_id
                        ELSE r.person_a_id
                    END AS path,
                    p.depth + 1 AS depth,
                    p.path_strength * :decay * r.strength AS path_strength
                FROM paths p
                JOIN relationships r ON (r.person_a_id = p.next_id OR r.person_b_id = p.next_id)
                WHERE p.depth < :max_hops
                  AND p.path NOT LIKE '%' || CASE
                      WHEN r.person_a_id = p.next_id THEN r.person_b_id
                      ELSE r.person_a_id
                  END || '%'
            )
            SELECT DISTINCT path, depth, path_strength
            FROM paths
            WHERE next_id = :to_id
            ORDER BY path_strength DESC
            LIMIT 10
        """)

        result = await self.db_session.execute(
            query,
            {
                "from_id": from_person_id,
                "to_id": to_person_id,
                "max_hops": max_hops,
                "decay": HOP_DECAY_FACTOR,
            },
        )

        rows = result.fetchall()
        paths = []

        for row in rows:
            path_str, depth, strength = row
            node_ids = path_str.split(",")

            # Build the path object
            path = await self._build_path_from_ids(
                node_ids=node_ids,
                path_strength=strength,
            )
            if path:
                paths.append(path)

        return sorted(paths, key=lambda p: p.path_strength, reverse=True)

    async def _find_paths_mock(
        self,
        from_person_id: str,
        to_person_id: str,
        max_hops: int,
    ) -> list[ConnectionPath]:
        """Find paths using mock data with BFS."""
        from .mock_data import MOCK_PEOPLE, MOCK_RELATIONSHIPS, get_mock_person_by_id

        # Build adjacency list from mock relationships
        adjacency: dict[str, list[tuple[str, str, float, str]]] = {}
        for rel in MOCK_RELATIONSHIPS:
            # Add both directions (undirected graph)
            if rel.person_a_id not in adjacency:
                adjacency[rel.person_a_id] = []
            if rel.person_b_id not in adjacency:
                adjacency[rel.person_b_id] = []

            adjacency[rel.person_a_id].append(
                (rel.person_b_id, rel.relationship_type.value, rel.strength, rel.context)
            )
            adjacency[rel.person_b_id].append(
                (rel.person_a_id, rel.relationship_type.value, rel.strength, rel.context)
            )

        # BFS to find all paths
        all_paths: list[tuple[list[str], list[tuple[str, float, str]], float]] = []
        queue: list[tuple[str, list[str], list[tuple[str, float, str]], float]] = [
            (from_person_id, [from_person_id], [], 1.0)
        ]

        while queue:
            current, path, edges, strength = queue.pop(0)

            if current == to_person_id:
                all_paths.append((path, edges, strength))
                continue

            if len(path) > max_hops + 1:
                continue

            for neighbor, rel_type, rel_strength, context in adjacency.get(current, []):
                if neighbor not in path:  # Avoid cycles
                    new_strength = strength * rel_strength * HOP_DECAY_FACTOR
                    new_edges = edges + [(rel_type, rel_strength, context or "")]
                    queue.append((neighbor, path + [neighbor], new_edges, new_strength))

        # Convert to ConnectionPath objects
        paths = []
        for idx, (node_ids, edge_data, path_strength) in enumerate(all_paths):
            source = get_mock_person_by_id(node_ids[0])
            target = get_mock_person_by_id(node_ids[-1])

            if not source or not target:
                continue

            nodes = []
            for nid in node_ids:
                person = get_mock_person_by_id(nid)
                if person:
                    nodes.append(
                        PathNode(
                            person_id=person.id,
                            name=person.name,
                            title=person.title,
                            company=person.company,
                            email=person.email,
                        )
                    )

            edges = []
            for i, (rel_type, rel_strength, context) in enumerate(edge_data):
                edges.append(
                    PathEdge(
                        from_person_id=node_ids[i],
                        to_person_id=node_ids[i + 1],
                        relationship_type=rel_type,
                        strength=rel_strength,
                        context=context,
                    )
                )

            # Build introduction chain description
            intro_chain = self._build_introduction_chain(nodes, edges)

            paths.append(
                ConnectionPath(
                    path_id=f"path_{idx + 1}",
                    source_person=PathNode(
                        person_id=source.id,
                        name=source.name,
                        title=source.title,
                        company=source.company,
                        email=source.email,
                    ),
                    target_person=PathNode(
                        person_id=target.id,
                        name=target.name,
                        title=target.title,
                        company=target.company,
                        email=target.email,
                    ),
                    nodes=nodes,
                    edges=edges,
                    total_hops=len(edges),
                    path_strength=path_strength,
                    introduction_chain=intro_chain,
                )
            )

        return sorted(paths, key=lambda p: p.path_strength, reverse=True)[:10]

    async def _build_path_from_ids(
        self,
        node_ids: list[str],
        path_strength: float,
    ) -> Optional[ConnectionPath]:
        """Build a ConnectionPath from a list of node IDs."""
        if len(node_ids) < 2:
            return None

        # Fetch person details
        persons_query = text("""
            SELECT id, name, title, company, email
            FROM persons
            WHERE id IN :ids
        """)

        result = await self.db_session.execute(
            persons_query, {"ids": tuple(node_ids)}
        )
        persons_map = {row.id: row for row in result.fetchall()}

        nodes = []
        for nid in node_ids:
            if nid in persons_map:
                p = persons_map[nid]
                nodes.append(
                    PathNode(
                        person_id=p.id,
                        name=p.name,
                        title=p.title,
                        company=p.company,
                        email=p.email,
                    )
                )

        # Fetch relationship details for edges
        edges = []
        for i in range(len(node_ids) - 1):
            rel_query = text("""
                SELECT relationship_type, strength, context
                FROM relationships
                WHERE (person_a_id = :a AND person_b_id = :b)
                   OR (person_a_id = :b AND person_b_id = :a)
                LIMIT 1
            """)

            rel_result = await self.db_session.execute(
                rel_query, {"a": node_ids[i], "b": node_ids[i + 1]}
            )
            rel = rel_result.fetchone()

            if rel:
                edges.append(
                    PathEdge(
                        from_person_id=node_ids[i],
                        to_person_id=node_ids[i + 1],
                        relationship_type=rel.relationship_type,
                        strength=rel.strength,
                        context=rel.context,
                    )
                )

        if not nodes or len(nodes) < 2:
            return None

        intro_chain = self._build_introduction_chain(nodes, edges)

        return ConnectionPath(
            path_id=f"path_{hash(tuple(node_ids)) % 10000}",
            source_person=nodes[0],
            target_person=nodes[-1],
            nodes=nodes,
            edges=edges,
            total_hops=len(edges),
            path_strength=path_strength,
            introduction_chain=intro_chain,
        )

    def _build_introduction_chain(
        self, nodes: list[PathNode], edges: list[PathEdge]
    ) -> list[str]:
        """Build human-readable introduction chain."""
        chain = []

        for i, edge in enumerate(edges):
            from_node = nodes[i]
            to_node = nodes[i + 1]

            rel_desc = self._relationship_description(edge.relationship_type)
            chain.append(
                f"{from_node.name} ({from_node.title}) {rel_desc} {to_node.name} ({to_node.title})"
            )

        return chain

    def _relationship_description(self, rel_type: str) -> str:
        """Get human-readable relationship description."""
        descriptions = {
            "worked_together": "worked with",
            "board_together": "serves on board with",
            "investor_founder": "invested in",
            "alumni": "went to school with",
            "met_at_conference": "met at conference",
            "mutual_friend": "knows through mutual contacts",
            "advisor": "advises",
            "deal_counterparty": "did deals with",
        }
        return descriptions.get(rel_type, "knows")

    async def get_network_map(
        self,
        person_id: str,
        depth: int = 2,
    ) -> NetworkGraph:
        """
        Get the network graph around a person.

        Args:
            person_id: Center person UUID
            depth: How many hops to include (default 2)

        Returns:
            NetworkGraph with all nodes and edges within depth
        """
        if self._use_mock:
            return await self._get_network_map_mock(person_id, depth)

        return await self._get_network_map_sql(person_id, depth)

    async def _get_network_map_mock(
        self, person_id: str, depth: int
    ) -> NetworkGraph:
        """Get network map using mock data."""
        from .mock_data import MOCK_RELATIONSHIPS, get_mock_person_by_id

        center = get_mock_person_by_id(person_id)
        if not center:
            return NetworkGraph(
                center_person=PathNode(
                    person_id=person_id,
                    name="Unknown",
                    title="",
                    company="",
                ),
                nodes=[],
                edges=[],
                depth=depth,
            )

        # BFS to find all nodes within depth
        visited: set[str] = {person_id}
        queue: list[tuple[str, int]] = [(person_id, 0)]
        all_edges: list[PathEdge] = []

        while queue:
            current, current_depth = queue.pop(0)

            if current_depth >= depth:
                continue

            for rel in MOCK_RELATIONSHIPS:
                neighbor = None
                if rel.person_a_id == current:
                    neighbor = rel.person_b_id
                elif rel.person_b_id == current:
                    neighbor = rel.person_a_id

                if neighbor:
                    # Always add the edge if it connects to a visited node or we're exploring
                    edge = PathEdge(
                        from_person_id=rel.person_a_id,
                        to_person_id=rel.person_b_id,
                        relationship_type=rel.relationship_type.value,
                        strength=rel.strength,
                        context=rel.context,
                    )

                    # Avoid duplicate edges
                    edge_key = (
                        min(rel.person_a_id, rel.person_b_id),
                        max(rel.person_a_id, rel.person_b_id),
                    )
                    existing_keys = {
                        (min(e.from_person_id, e.to_person_id), max(e.from_person_id, e.to_person_id))
                        for e in all_edges
                    }

                    if edge_key not in existing_keys:
                        if neighbor in visited or current_depth + 1 <= depth:
                            all_edges.append(edge)

                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_depth + 1))

        # Build node list
        nodes = []
        for nid in visited:
            person = get_mock_person_by_id(nid)
            if person:
                nodes.append(
                    PathNode(
                        person_id=person.id,
                        name=person.name,
                        title=person.title,
                        company=person.company,
                        email=person.email,
                    )
                )

        return NetworkGraph(
            center_person=PathNode(
                person_id=center.id,
                name=center.name,
                title=center.title,
                company=center.company,
                email=center.email,
            ),
            nodes=nodes,
            edges=all_edges,
            depth=depth,
        )

    async def _get_network_map_sql(
        self, person_id: str, depth: int
    ) -> NetworkGraph:
        """Get network map using SQL recursive CTE."""
        # This query finds all nodes within N hops of the center person
        query = text("""
            WITH RECURSIVE network AS (
                -- Base case: the center person
                SELECT
                    :person_id AS person_id,
                    0 AS depth

                UNION

                -- Recursive case: neighbors
                SELECT
                    CASE
                        WHEN r.person_a_id = n.person_id THEN r.person_b_id
                        ELSE r.person_a_id
                    END AS person_id,
                    n.depth + 1 AS depth
                FROM network n
                JOIN relationships r ON (r.person_a_id = n.person_id OR r.person_b_id = n.person_id)
                WHERE n.depth < :depth
            )
            SELECT DISTINCT person_id FROM network
        """)

        result = await self.db_session.execute(
            query, {"person_id": person_id, "depth": depth}
        )
        node_ids = [row.person_id for row in result.fetchall()]

        # Fetch person details
        persons_query = text("""
            SELECT id, name, title, company, email
            FROM persons
            WHERE id IN :ids
        """)
        persons_result = await self.db_session.execute(
            persons_query, {"ids": tuple(node_ids)}
        )

        nodes = []
        center_person = None
        for row in persons_result.fetchall():
            node = PathNode(
                person_id=row.id,
                name=row.name,
                title=row.title,
                company=row.company,
                email=row.email,
            )
            nodes.append(node)
            if row.id == person_id:
                center_person = node

        # Fetch all relationships between these nodes
        edges_query = text("""
            SELECT person_a_id, person_b_id, relationship_type, strength, context
            FROM relationships
            WHERE person_a_id IN :ids AND person_b_id IN :ids
        """)
        edges_result = await self.db_session.execute(
            edges_query, {"ids": tuple(node_ids)}
        )

        edges = []
        for row in edges_result.fetchall():
            edges.append(
                PathEdge(
                    from_person_id=row.person_a_id,
                    to_person_id=row.person_b_id,
                    relationship_type=row.relationship_type,
                    strength=row.strength,
                    context=row.context,
                )
            )

        if not center_person:
            center_person = PathNode(
                person_id=person_id,
                name="Unknown",
                title="",
                company="",
            )

        return NetworkGraph(
            center_person=center_person,
            nodes=nodes,
            edges=edges,
            depth=depth,
        )

    def calculate_path_strength(self, edges: list[PathEdge]) -> float:
        """
        Calculate overall path strength from edges.

        Strength decays with each hop: base_strength * decay^hop
        """
        if not edges:
            return 0.0

        strength = 1.0
        for i, edge in enumerate(edges):
            # Apply hop decay
            hop_factor = HOP_DECAY_FACTOR ** i
            strength *= edge.strength * hop_factor

        return strength
