"""Tests for navigation system."""

from uuid import UUID

from spherical_maze.maze_graph import MazeGraph
from spherical_maze.navigation import DotEntity, PathFollower


class TestDotEntity:
    """Test DotEntity functionality."""

    def test_dot_initialization(self) -> None:
        """Test creating a dot entity."""
        dot = DotEntity(latitude=10.0, longitude=20.0, speed=2.0)

        assert dot.latitude == 10.0
        assert dot.longitude == 20.0
        assert dot.speed == 2.0
        assert dot.target_node is None
        assert len(dot.path_queue) == 0

    def test_dot_from_position(self) -> None:
        """Test creating dot from position."""
        dot = DotEntity.from_position(5.0, 15.0, speed=1.5)

        assert dot.latitude == 5.0
        assert dot.longitude == 15.0
        assert dot.speed == 1.5

    def test_set_path(self) -> None:
        """Test setting a path for the dot."""
        from uuid import uuid4

        dot = DotEntity(latitude=0.0, longitude=0.0)
        path = [uuid4(), uuid4(), uuid4()]

        dot.set_path(path)

        assert len(dot.path_queue) == 3
        assert dot.current_path_index == 0
        assert dot.target_node == path[0]

    def test_calculate_distance(self) -> None:
        """Test distance calculation."""
        distance = DotEntity._calculate_distance(0.0, 0.0, 0.0, 0.0)
        assert distance == 0.0

        distance = DotEntity._calculate_distance(0.0, 0.0, 1.0, 1.0)
        assert distance > 0.0

    def test_update_movement(self) -> None:
        """Test dot movement along path."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)
        graph.add_edge(node1.id, node2.id)

        dot = DotEntity(latitude=0.0, longitude=0.0, speed=50.0)
        dot.set_path([node1.id, node2.id])

        initial_pos = (dot.latitude, dot.longitude)
        dot.update(0.1, graph)

        reached = False
        for _ in range(50):
            reached = dot.update(0.1, graph)
            if reached or (dot.latitude, dot.longitude) != initial_pos:
                break

        assert (dot.latitude, dot.longitude) != initial_pos or reached

    def test_update_reaches_waypoint(self) -> None:
        """Test dot reaches waypoint."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(0.1, 0.1)
        graph.add_edge(node1.id, node2.id)

        dot = DotEntity(latitude=0.0, longitude=0.0, speed=1000.0)
        dot.set_path([node1.id, node2.id])

        for _ in range(100):
            if dot.update(0.1, graph):
                break

        assert dot.current_path_index == len(dot.path_queue)

    def test_empty_path(self) -> None:
        """Test update with empty path."""
        graph = MazeGraph()
        dot = DotEntity(latitude=0.0, longitude=0.0)

        reached = dot.update(0.1, graph)
        assert reached


class TestPathFollower:
    """Test PathFollower functionality."""

    def test_path_follower_initialization(self) -> None:
        """Test creating a path follower."""
        graph = MazeGraph()
        dot = DotEntity(latitude=0.0, longitude=0.0)
        follower = PathFollower(dot, graph)

        assert follower.dot == dot
        assert follower.graph == graph
        assert not follower.is_following
        assert not follower.completed

    def test_start_following(self) -> None:
        """Test starting path following."""
        from uuid import uuid4

        graph = MazeGraph()
        dot = DotEntity(latitude=0.0, longitude=0.0)
        follower = PathFollower(dot, graph)

        path = [uuid4(), uuid4()]
        follower.start_following(path)

        assert follower.is_following
        assert not follower.completed
        assert len(dot.path_queue) == 2

    def test_update_following(self) -> None:
        """Test updating path following."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(0.5, 0.5)
        graph.add_edge(node1.id, node2.id)

        dot = DotEntity(latitude=0.0, longitude=0.0, speed=100.0)
        follower = PathFollower(dot, graph)

        follower.start_following([node1.id, node2.id])

        for _ in range(100):
            follower.update(0.1)
            if follower.is_complete():
                break

        assert follower.is_complete()

    def test_stop_following(self) -> None:
        """Test stopping path following."""
        from uuid import uuid4

        graph = MazeGraph()
        dot = DotEntity(latitude=0.0, longitude=0.0)
        follower = PathFollower(dot, graph)

        follower.start_following([uuid4()])
        follower.stop()

        assert not follower.is_following
        assert len(dot.path_queue) == 0

    def test_is_complete(self) -> None:
        """Test checking if path following is complete."""
        graph = MazeGraph()
        dot = DotEntity(latitude=0.0, longitude=0.0)
        follower = PathFollower(dot, graph)

        assert not follower.is_complete()

        follower.completed = True
        assert follower.is_complete()

    def test_waypoint_callback_invoked(self) -> None:
        """Test waypoint callback runs when dot reaches nodes."""
        graph = MazeGraph()
        start = graph.add_node(0.0, 0.0)
        end = graph.add_node(0.2, 0.2)
        graph.add_edge(start.id, end.id)

        dot = DotEntity(latitude=0.0, longitude=0.0, speed=200.0)
        follower = PathFollower(dot, graph)

        reached_nodes: list[UUID] = []
        follower.set_waypoint_callback(lambda node_id: reached_nodes.append(node_id))
        follower.start_following([start.id, end.id])

        for _ in range(20):
            follower.update(0.1)
            if follower.is_complete():
                break

        assert end.id in reached_nodes
