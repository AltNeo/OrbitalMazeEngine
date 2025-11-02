"""Tests for the maze graph data structure."""

import json

import pytest

from spherical_maze.maze_graph import MazeEdge, MazeGraph, MazeNode


class TestMazeNode:
    """Test MazeNode functionality."""

    def test_node_creation(self) -> None:
        """Test creating a maze node."""
        from uuid import uuid4

        node_id = uuid4()
        node = MazeNode(
            id=node_id,
            latitude=10.0,
            longitude=20.0,
            generation_prompt="test",
        )

        assert node.id == node_id
        assert node.latitude == 10.0
        assert node.longitude == 20.0
        assert node.generation_prompt == "test"
        assert not node.visited
        assert len(node.connections) == 0

    def test_node_serialization(self) -> None:
        """Test node to_dict and from_dict."""
        from uuid import uuid4

        node = MazeNode(
            id=uuid4(),
            latitude=45.0,
            longitude=-90.0,
            generation_prompt="spiral",
            visited=True,
        )

        node_dict = node.to_dict()
        restored = MazeNode.from_dict(node_dict)

        assert restored.id == node.id
        assert restored.latitude == node.latitude
        assert restored.longitude == node.longitude
        assert restored.visited == node.visited


class TestMazeEdge:
    """Test MazeEdge functionality."""

    def test_edge_creation(self) -> None:
        """Test creating a maze edge."""
        from uuid import uuid4

        edge_id = uuid4()
        node_a = uuid4()
        node_b = uuid4()

        edge = MazeEdge(
            id=edge_id,
            node_a=node_a,
            node_b=node_b,
            traversal_cost=2.5,
        )

        assert edge.id == edge_id
        assert edge.node_a == node_a
        assert edge.node_b == node_b
        assert edge.traversal_cost == 2.5
        assert not edge.blocked

    def test_edge_serialization(self) -> None:
        """Test edge to_dict and from_dict."""
        from uuid import uuid4

        edge = MazeEdge(
            id=uuid4(),
            node_a=uuid4(),
            node_b=uuid4(),
            path_points=[(1.0, 2.0), (3.0, 4.0)],
            traversal_cost=1.5,
            blocked=True,
        )

        edge_dict = edge.to_dict()
        restored = MazeEdge.from_dict(edge_dict)

        assert restored.id == edge.id
        assert restored.node_a == edge.node_a
        assert restored.node_b == edge.node_b
        assert restored.traversal_cost == edge.traversal_cost
        assert restored.blocked == edge.blocked


class TestMazeGraph:
    """Test MazeGraph functionality."""

    def test_graph_initialization(self) -> None:
        """Test creating an empty graph."""
        graph = MazeGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self) -> None:
        """Test adding nodes to graph."""
        graph = MazeGraph()

        node1 = graph.add_node(0.0, 0.0, "start")
        node2 = graph.add_node(10.0, 10.0, "next")

        assert len(graph.nodes) == 2
        assert node1.id in graph.nodes
        assert node2.id in graph.nodes
        assert graph.nodes[node1.id].latitude == 0.0
        assert graph.nodes[node2.id].longitude == 10.0

    def test_add_edge(self) -> None:
        """Test adding edges between nodes."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)

        edge = graph.add_edge(node1.id, node2.id, cost=1.5)

        assert len(graph.edges) == 1
        assert edge.id in graph.edges
        assert node2.id in node1.connections
        assert node1.id in node2.connections
        assert edge.traversal_cost == 1.5
        assert len(edge.path_points) >= 2

    def test_add_edge_invalid_nodes(self) -> None:
        """Test adding edge with invalid node IDs."""
        from uuid import uuid4

        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)

        with pytest.raises(ValueError, match="Both nodes must exist"):
            graph.add_edge(node1.id, uuid4())

    def test_remove_node(self) -> None:
        """Test removing a node updates connections."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)
        node3 = graph.add_node(20.0, 20.0)

        graph.add_edge(node1.id, node2.id)
        graph.add_edge(node2.id, node3.id)

        graph.remove_node(node2.id)

        assert len(graph.nodes) == 2
        assert node2.id not in graph.nodes
        assert node2.id not in node1.connections
        assert node2.id not in node3.connections

    def test_has_cycle(self) -> None:
        """Test cycle detection in graph."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)
        node3 = graph.add_node(20.0, 20.0)

        assert not graph.has_cycle()

        graph.add_edge(node1.id, node2.id)
        graph.add_edge(node2.id, node3.id)
        assert not graph.has_cycle()

        graph.add_edge(node3.id, node1.id)
        assert graph.has_cycle()

    def test_shortest_path(self) -> None:
        """Test pathfinding algorithm."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)
        node3 = graph.add_node(20.0, 20.0)
        node4 = graph.add_node(30.0, 30.0)

        graph.add_edge(node1.id, node2.id, cost=1.0)
        graph.add_edge(node2.id, node3.id, cost=1.0)
        graph.add_edge(node3.id, node4.id, cost=1.0)
        graph.add_edge(node1.id, node4.id, cost=10.0)

        path = graph.shortest_path(node1.id, node4.id)

        assert path is not None
        assert len(path) == 4
        assert path[0] == node1.id
        assert path[-1] == node4.id

    def test_shortest_path_no_route(self) -> None:
        """Test pathfinding with no route."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)

        path = graph.shortest_path(node1.id, node2.id)

        assert path is None

    def test_find_nodes_in_radius(self) -> None:
        """Test spatial query for nearby nodes."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(5.0, 5.0)
        node3 = graph.add_node(50.0, 50.0)

        nearby = graph.find_nodes_in_radius(0.0, 0.0, radius=10.0)

        assert len(nearby) == 2
        assert node1 in nearby
        assert node2 in nearby
        assert node3 not in nearby

    def test_get_node_by_position(self) -> None:
        """Test finding node at specific position."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        graph.add_node(10.0, 10.0)

        found = graph.get_node_by_position(0.05, 0.05, threshold=0.1)
        assert found is not None
        assert found.id == node1.id

        not_found = graph.get_node_by_position(50.0, 50.0, threshold=0.1)
        assert not_found is None

    def test_serialize_deserialize(self) -> None:
        """Test graph serialization and deserialization."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0, "start")
        node2 = graph.add_node(10.0, 10.0, "end")
        graph.add_edge(node1.id, node2.id, cost=2.5)

        json_str = graph.to_json()
        assert isinstance(json_str, str)
        json.loads(json_str)

        restored = MazeGraph.from_json(json_str)

        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1

        original_nodes = list(graph.nodes.values())
        restored_nodes = list(restored.nodes.values())

        assert restored_nodes[0].latitude == original_nodes[0].latitude
        assert restored_nodes[1].longitude == original_nodes[1].longitude
        restored_edge = next(iter(restored.edges.values()))
        assert len(restored_edge.path_points) >= 2

    def test_add_edge_generates_geodesic_path(self) -> None:
        """Edges store an interpolated geodesic across the sphere."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(45.0, 90.0)

        edge = graph.add_edge(node1.id, node2.id, segments=12)

        assert len(edge.path_points) == 13
        start_lat, start_lon = edge.path_points[0]
        end_lat, end_lon = edge.path_points[-1]
        assert start_lat == pytest.approx(node1.latitude)
        assert start_lon == pytest.approx(node1.longitude)
        assert end_lat == pytest.approx(node2.latitude)
        assert end_lon == pytest.approx(node2.longitude)

    def test_great_circle_distance(self) -> None:
        """Test great circle distance calculation."""
        distance = MazeGraph._great_circle_distance(0.0, 0.0, 0.0, 90.0)
        assert 89.0 < distance < 91.0

        distance_same = MazeGraph._great_circle_distance(45.0, 45.0, 45.0, 45.0)
        assert distance_same == 0.0
