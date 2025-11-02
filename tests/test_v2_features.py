"""Tests for V2 first-person features."""

import math

from spherical_maze.navigation import DotEntity


class TestV2DotEntity:
    """Test V2-specific DotEntity features."""

    def test_dot_has_v2_properties(self) -> None:
        """Test that DotEntity has V2 first-person properties."""
        dot = DotEntity(latitude=0.0, longitude=0.0)

        assert hasattr(dot, "yaw")
        assert hasattr(dot, "pitch")
        assert hasattr(dot, "height")
        assert dot.yaw == 0.0
        assert dot.pitch == 0.0
        assert dot.height == 5.0

    def test_rotate_view(self) -> None:
        """Test view rotation updates yaw and pitch."""
        dot = DotEntity(latitude=0.0, longitude=0.0)

        dot.rotate_view(10.0, 5.0)

        assert dot.yaw == 10.0
        assert dot.pitch == 5.0

    def test_rotate_view_wraps_yaw(self) -> None:
        """Test yaw wraps around 360 degrees."""
        dot = DotEntity(latitude=0.0, longitude=0.0)

        dot.rotate_view(370.0, 0.0)

        assert 0.0 <= dot.yaw < 360.0
        assert abs(dot.yaw - 10.0) < 0.1

    def test_rotate_view_clamps_pitch(self) -> None:
        """Test pitch is clamped to prevent over-rotation."""
        dot = DotEntity(latitude=0.0, longitude=0.0)

        dot.rotate_view(0.0, 100.0)
        assert dot.pitch == 89.0

        dot.pitch = 0.0
        dot.rotate_view(0.0, -100.0)
        assert dot.pitch == -89.0

    def test_move_by_forward(self) -> None:
        """Test moving forward changes position."""
        dot = DotEntity(latitude=0.0, longitude=0.0, speed=10.0)
        initial_lat = dot.latitude
        initial_lon = dot.longitude

        dot.move_by(forward=1.0, strafe=0.0, delta_time=0.1)

        # Should have moved
        assert (dot.latitude, dot.longitude) != (initial_lat, initial_lon)

    def test_move_by_backward(self) -> None:
        """Test moving backward changes position."""
        dot = DotEntity(latitude=0.0, longitude=0.0, speed=10.0)
        initial_lat = dot.latitude
        initial_lon = dot.longitude

        dot.move_by(forward=-1.0, strafe=0.0, delta_time=0.1)

        # Should have moved
        assert (dot.latitude, dot.longitude) != (initial_lat, initial_lon)

    def test_move_by_strafe(self) -> None:
        """Test strafing changes position."""
        dot = DotEntity(latitude=0.0, longitude=0.0, speed=10.0)
        initial_lat = dot.latitude
        initial_lon = dot.longitude

        dot.move_by(forward=0.0, strafe=1.0, delta_time=0.1)

        # Should have moved
        assert (dot.latitude, dot.longitude) != (initial_lat, initial_lon)

    def test_move_by_respects_yaw(self) -> None:
        """Test movement direction is based on yaw."""
        dot1 = DotEntity(latitude=0.0, longitude=0.0, speed=10.0, yaw=0.0)
        dot2 = DotEntity(latitude=0.0, longitude=0.0, speed=10.0, yaw=90.0)

        dot1.move_by(forward=1.0, strafe=0.0, delta_time=0.1)
        dot2.move_by(forward=1.0, strafe=0.0, delta_time=0.1)

        # Different yaw should result in different positions
        assert (dot1.latitude, dot1.longitude) != (dot2.latitude, dot2.longitude)

    def test_move_by_no_movement(self) -> None:
        """Test no input results in no movement."""
        dot = DotEntity(latitude=5.0, longitude=10.0)
        initial_lat = dot.latitude
        initial_lon = dot.longitude

        dot.move_by(forward=0.0, strafe=0.0, delta_time=0.1)

        assert dot.latitude == initial_lat
        assert dot.longitude == initial_lon

    def test_move_by_clamps_latitude(self) -> None:
        """Test latitude is clamped to valid range."""
        dot = DotEntity(latitude=85.0, longitude=0.0, speed=100.0, yaw=0.0)

        # Try to move way past north pole
        for _ in range(20):
            dot.move_by(forward=1.0, strafe=0.0, delta_time=0.1)

        assert -90.0 <= dot.latitude <= 90.0

    def test_move_by_wraps_longitude(self) -> None:
        """Test longitude wraps correctly."""
        dot = DotEntity(latitude=0.0, longitude=170.0, speed=100.0, yaw=90.0)

        # Move to wrap longitude
        for _ in range(5):
            dot.move_by(forward=1.0, strafe=0.0, delta_time=0.1)

        assert -180.0 <= dot.longitude <= 180.0

    def test_collision_detection_with_graph(self) -> None:
        """Test collision detection prevents walking through walls."""
        from spherical_maze.maze_graph import MazeGraph

        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(5.0, 0.0)
        graph.add_edge(node1.id, node2.id)

        # Dot on the path
        dot = DotEntity(latitude=2.5, longitude=0.0, speed=10.0, yaw=90.0)

        # Try to move perpendicular to path (off path)
        initial_pos = (dot.latitude, dot.longitude)
        dot.move_by(forward=0.0, strafe=1.0, delta_time=0.5, graph=graph)

        # Should be blocked by collision detection (or close to initial)
        dist_moved = math.sqrt(
            (dot.latitude - initial_pos[0]) ** 2 + (dot.longitude - initial_pos[1]) ** 2
        )
        # Movement should be limited by collision
        assert dist_moved < 5.0  # Would be larger without collision

    def test_distance_to_segment(self) -> None:
        """Test distance calculation to line segment."""
        # Point on the segment
        dist = DotEntity._distance_to_segment(2.0, 0.0, 0.0, 0.0, 4.0, 0.0)
        assert abs(dist) < 0.1

        # Point off the segment
        dist = DotEntity._distance_to_segment(2.0, 5.0, 0.0, 0.0, 4.0, 0.0)
        assert abs(dist - 5.0) < 0.1

        # Point before segment start
        dist = DotEntity._distance_to_segment(-1.0, 0.0, 0.0, 0.0, 4.0, 0.0)
        assert abs(dist - 1.0) < 0.1

        # Point after segment end
        dist = DotEntity._distance_to_segment(5.0, 0.0, 0.0, 0.0, 4.0, 0.0)
        assert abs(dist - 1.0) < 0.1

    def test_valid_position_check(self) -> None:
        """Test position validity checking."""
        from spherical_maze.maze_graph import MazeGraph

        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 0.0)
        graph.add_edge(node1.id, node2.id)

        dot = DotEntity(latitude=0.0, longitude=0.0)

        # Position on path should be valid
        assert dot._check_valid_position(5.0, 0.0, graph)

        # Position near path should be valid
        assert dot._check_valid_position(5.0, 1.0, graph)

        # Position far from path should be invalid
        assert not dot._check_valid_position(50.0, 50.0, graph)


class TestV2Integration:
    """Test V2 renderer and game integration."""

    def test_renderer_v2_imports(self) -> None:
        """Test V2 renderer can be imported."""
        from spherical_maze.renderer_v2 import FirstPersonRenderer

        renderer = FirstPersonRenderer(radius=100.0, screen_size=(800, 600))
        assert renderer.fov > 0
        assert renderer.wall_height > 0
        assert renderer.path_width > 0
        renderer.cleanup()

    def test_game_v2_imports(self) -> None:
        """Test V2 game can be imported."""
        from spherical_maze.game_v2 import FirstPersonMazeGame

        # Just test import and basic properties
        assert FirstPersonMazeGame is not None

    def test_v2_renderer_camera_position(self) -> None:
        """Test camera position calculation."""
        from spherical_maze.renderer_v2 import FirstPersonRenderer

        renderer = FirstPersonRenderer(radius=100.0, screen_size=(800, 600))
        dot = DotEntity(latitude=0.0, longitude=0.0, height=5.0)

        cam_x, cam_y, cam_z = renderer.get_camera_position(dot)

        # Camera should be at radius + height
        cam_distance = math.sqrt(cam_x**2 + cam_y**2 + cam_z**2)
        expected_distance = 100.0 + 5.0

        assert abs(cam_distance - expected_distance) < 0.1

        renderer.cleanup()

    def test_v2_renderer_spherical_conversion(self) -> None:
        """Test spherical to Cartesian conversion."""
        from spherical_maze.renderer_v2 import FirstPersonRenderer

        renderer = FirstPersonRenderer(radius=100.0, screen_size=(800, 600))

        # Test north pole
        x, y, z = renderer.spherical_to_cartesian(90.0, 0.0)
        assert abs(x) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z - 100.0) < 1e-10

        # Test equator
        x, y, z = renderer.spherical_to_cartesian(0.0, 0.0)
        assert abs(x - 100.0) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z) < 1e-10

        renderer.cleanup()
