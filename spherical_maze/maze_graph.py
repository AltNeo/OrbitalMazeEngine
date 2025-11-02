"""Cyclic tree data structure for maze representation."""

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class MazeNode:
    """Represents a node in the maze graph with spherical coordinates."""

    id: UUID
    latitude: float
    longitude: float
    connections: list[UUID] = field(default_factory=list)
    generation_prompt: str = ""
    visited: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            "id": str(self.id),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "connections": [str(c) for c in self.connections],
            "generation_prompt": self.generation_prompt,
            "visited": self.visited,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MazeNode":
        """Deserialize node from dictionary."""
        return cls(
            id=UUID(data["id"]),
            latitude=data["latitude"],
            longitude=data["longitude"],
            connections=[UUID(c) for c in data["connections"]],
            generation_prompt=data.get("generation_prompt", ""),
            visited=data.get("visited", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MazeEdge:
    """Represents an edge between two nodes in the maze."""

    id: UUID
    node_a: UUID
    node_b: UUID
    path_points: list[tuple[float, float]] = field(default_factory=list)
    traversal_cost: float = 1.0
    blocked: bool = False
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize edge to dictionary."""
        return {
            "id": str(self.id),
            "node_a": str(self.node_a),
            "node_b": str(self.node_b),
            "path_points": self.path_points,
            "traversal_cost": self.traversal_cost,
            "blocked": self.blocked,
            "generation_timestamp": self.generation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MazeEdge":
        """Deserialize edge from dictionary."""
        return cls(
            id=UUID(data["id"]),
            node_a=UUID(data["node_a"]),
            node_b=UUID(data["node_b"]),
            path_points=[tuple(p) for p in data.get("path_points", [])],
            traversal_cost=data.get("traversal_cost", 1.0),
            blocked=data.get("blocked", False),
            generation_timestamp=data.get("generation_timestamp", datetime.now().isoformat()),
        )


class MazeGraph:
    """Cyclic graph structure for representing the maze."""

    def __init__(self) -> None:
        """Initialize an empty maze graph."""
        self.nodes: dict[UUID, MazeNode] = {}
        self.edges: dict[UUID, MazeEdge] = {}

    def add_node(
        self,
        latitude: float,
        longitude: float,
        generation_prompt: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> MazeNode:
        """Add a node to the graph."""
        node = MazeNode(
            id=uuid4(),
            latitude=latitude,
            longitude=longitude,
            generation_prompt=generation_prompt,
            metadata=metadata or {},
        )
        self.nodes[node.id] = node
        return node

    def add_edge(
        self,
        node_a_id: UUID,
        node_b_id: UUID,
        cost: float = 1.0,
        path_points: list[tuple[float, float]] | None = None,
        segments: int = 24,
    ) -> MazeEdge:
        """Add an edge between two nodes."""
        if node_a_id not in self.nodes or node_b_id not in self.nodes:
            msg = "Both nodes must exist in the graph"
            raise ValueError(msg)

        if path_points is None:
            node_a = self.nodes[node_a_id]
            node_b = self.nodes[node_b_id]
            path_points = self._compute_geodesic_path(node_a, node_b, segments=segments)

        edge = MazeEdge(
            id=uuid4(),
            node_a=node_a_id,
            node_b=node_b_id,
            traversal_cost=cost,
            path_points=path_points,
        )
        self.edges[edge.id] = edge

        self.nodes[node_a_id].connections.append(node_b_id)
        self.nodes[node_b_id].connections.append(node_a_id)

        return edge

    def remove_node(self, node_id: UUID) -> None:
        """Remove a node and all its connections from the graph."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        for connected_id in node.connections:
            if connected_id in self.nodes:
                self.nodes[connected_id].connections = [
                    c for c in self.nodes[connected_id].connections if c != node_id
                ]

        edges_to_remove = [
            edge_id
            for edge_id, edge in self.edges.items()
            if edge.node_a == node_id or edge.node_b == node_id
        ]
        for edge_id in edges_to_remove:
            del self.edges[edge_id]

        del self.nodes[node_id]

    def has_cycle(self) -> bool:
        """Detect if the graph contains any cycles using DFS."""
        visited = set()
        rec_stack = set()

        def dfs(node_id: UUID, parent: UUID | None) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor_id in self.nodes[node_id].connections:
                if neighbor_id not in visited:
                    if dfs(neighbor_id, node_id):
                        return True
                elif neighbor_id != parent and neighbor_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id, None):
                    return True

        return False

    def shortest_path(self, start_id: UUID, end_id: UUID) -> list[UUID] | None:
        """Find shortest path between two nodes using Dijkstra's algorithm."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        distances = {node_id: float("inf") for node_id in self.nodes}
        distances[start_id] = 0
        previous = dict.fromkeys(self.nodes)
        unvisited = set(self.nodes.keys())

        while unvisited:
            current = min(unvisited, key=lambda node_id: distances[node_id])
            if distances[current] == float("inf"):
                break

            unvisited.remove(current)

            if current == end_id:
                break

            for neighbor_id in self.nodes[current].connections:
                if neighbor_id in unvisited:
                    edge_cost = self._get_edge_cost(current, neighbor_id)
                    alt = distances[current] + edge_cost
                    if alt < distances[neighbor_id]:
                        distances[neighbor_id] = alt
                        previous[neighbor_id] = current

        if distances[end_id] == float("inf"):
            return None

        path = []
        current = end_id
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()

        return path

    def _get_edge_cost(self, node_a_id: UUID, node_b_id: UUID) -> float:
        """Get the cost of an edge between two nodes."""
        for edge in self.edges.values():
            if (edge.node_a == node_a_id and edge.node_b == node_b_id) or (
                edge.node_a == node_b_id and edge.node_b == node_a_id
            ):
                return edge.traversal_cost if not edge.blocked else float("inf")
        return 1.0

    def find_nodes_in_radius(
        self, latitude: float, longitude: float, radius: float
    ) -> list[MazeNode]:
        """Find all nodes within a given radius (in degrees) of a position."""
        nearby = []
        for node in self.nodes.values():
            distance = self._great_circle_distance(
                latitude, longitude, node.latitude, node.longitude
            )
            if distance <= radius:
                nearby.append(node)
        return nearby

    @staticmethod
    def _great_circle_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance between two points on a sphere (in degrees)."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)

        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return math.degrees(c)

    def _compute_geodesic_path(
        self,
        node_a: MazeNode,
        node_b: MazeNode,
        segments: int = 24,
    ) -> list[tuple[float, float]]:
        """Generate intermediate points along the geodesic between two nodes."""
        if segments < 2:
            segments = 2

        vec_a = self._latlon_to_vector(node_a.latitude, node_a.longitude)
        vec_b = self._latlon_to_vector(node_b.latitude, node_b.longitude)

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        dot = max(-1.0, min(1.0, dot))

        if abs(dot - 1.0) < 1e-8:
            return [
                (node_a.latitude, node_a.longitude),
                (node_b.latitude, node_b.longitude),
            ]

        omega = math.acos(dot)
        sin_omega = math.sin(omega)
        path: list[tuple[float, float]] = []

        for i in range(segments + 1):
            t = i / segments
            factor_a = math.sin((1 - t) * omega) / sin_omega
            factor_b = math.sin(t * omega) / sin_omega
            x = factor_a * vec_a[0] + factor_b * vec_b[0]
            y = factor_a * vec_a[1] + factor_b * vec_b[1]
            z = factor_a * vec_a[2] + factor_b * vec_b[2]
            lat, lon = self._vector_to_latlon((x, y, z))
            path.append((lat, lon))

        return path

    @staticmethod
    def _latlon_to_vector(latitude: float, longitude: float) -> tuple[float, float, float]:
        """Convert latitude/longitude to a unit vector."""
        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)
        x = math.cos(lat_rad) * math.cos(lon_rad)
        y = math.cos(lat_rad) * math.sin(lon_rad)
        z = math.sin(lat_rad)
        return (x, y, z)

    @staticmethod
    def _vector_to_latlon(vector: tuple[float, float, float]) -> tuple[float, float]:
        """Convert a unit vector back to latitude/longitude."""
        x, y, z = vector
        lat = math.degrees(math.asin(max(-1.0, min(1.0, z))))
        lon = math.degrees(math.atan2(y, x))
        if lon > 180:
            lon -= 360
        elif lon < -180:
            lon += 360
        return lat, lon

    def to_json(self) -> str:
        """Serialize graph to JSON string."""
        data = {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "MazeGraph":
        """Deserialize graph from JSON string."""
        data = json.loads(json_str)
        graph = cls()

        for node_data in data["nodes"]:
            node = MazeNode.from_dict(node_data)
            graph.nodes[node.id] = node

        for edge_data in data["edges"]:
            edge = MazeEdge.from_dict(edge_data)
            if not edge.path_points:
                node_a = graph.nodes.get(edge.node_a)
                node_b = graph.nodes.get(edge.node_b)
                if node_a is not None and node_b is not None:
                    edge.path_points = graph._compute_geodesic_path(node_a, node_b)
            graph.edges[edge.id] = edge

        return graph

    def get_node_by_position(
        self, latitude: float, longitude: float, threshold: float = 0.1
    ) -> MazeNode | None:
        """Get a node at or near a specific position."""
        for node in self.nodes.values():
            distance = self._great_circle_distance(
                latitude, longitude, node.latitude, node.longitude
            )
            if distance <= threshold:
                return node
        return None
