"""Tests for rendering system."""

import pytest

from spherical_maze.maze_graph import MazeGraph
from spherical_maze.navigation import DotEntity
from spherical_maze.renderer import SphereRenderer


class TestSphereRenderer:
    """Test SphereRenderer functionality."""

    @pytest.fixture
    def renderer(self) -> SphereRenderer:
        """Create a renderer for testing."""
        return SphereRenderer(radius=100.0, screen_size=(800, 600))

    @pytest.fixture(autouse=True)
    def cleanup_pygame(self, renderer: SphereRenderer) -> None:
        """Clean up pygame after each test."""
        yield
        renderer.cleanup()

    def test_renderer_initialization(self, renderer: SphereRenderer) -> None:
        """Test creating a renderer."""
        assert renderer.radius == 100.0
        assert renderer.screen_width == 800
        assert renderer.screen_height == 600
        assert renderer.zoom == 1.0

    def test_spherical_to_cartesian_north_pole(self, renderer: SphereRenderer) -> None:
        """Test conversion at north pole."""
        x, y, z = renderer.spherical_to_cartesian(90.0, 0.0)

        assert abs(x) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z - 100.0) < 1e-10

    def test_spherical_to_cartesian_south_pole(self, renderer: SphereRenderer) -> None:
        """Test conversion at south pole."""
        x, y, z = renderer.spherical_to_cartesian(-90.0, 0.0)

        assert abs(x) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z + 100.0) < 1e-10

    def test_spherical_to_cartesian_equator(self, renderer: SphereRenderer) -> None:
        """Test conversion at equator."""
        x, y, z = renderer.spherical_to_cartesian(0.0, 0.0)

        assert abs(x - 100.0) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z) < 1e-10

    def test_project_to_screen(self, renderer: SphereRenderer) -> None:
        """Test projection to screen coordinates."""
        result = renderer.project_to_screen(0.0, 0.0)

        assert result is not None
        screen_x, screen_y = result
        assert isinstance(screen_x, int)
        assert isinstance(screen_y, int)

    def test_project_to_screen_back_face(self, renderer: SphereRenderer) -> None:
        """Test projection of point on sphere."""
        renderer.camera_pitch = 0.0
        renderer.camera_yaw = 0.0

        result = renderer.project_to_screen(0.0, 0.0)

        assert result is not None

    def test_is_visible_front(self, renderer: SphereRenderer) -> None:
        """Test visibility check for front-facing point."""
        renderer.camera_pitch = 0.0
        renderer.camera_yaw = 0.0

        visible = renderer.is_visible(0.0, 0.0)
        assert visible

    def test_is_visible_back(self, renderer: SphereRenderer) -> None:
        """Test visibility check for far side point."""
        renderer.camera_pitch = 0.0
        renderer.camera_yaw = 180.0

        visible = renderer.is_visible(0.0, 180.0)
        assert visible

    def test_rotate_camera(self, renderer: SphereRenderer) -> None:
        """Test camera rotation."""
        initial_pitch = renderer.camera_pitch
        initial_yaw = renderer.camera_yaw

        renderer.rotate_camera(pitch=10.0, yaw=20.0)

        assert renderer.camera_pitch == initial_pitch + 10.0
        assert renderer.camera_yaw == initial_yaw + 20.0

    def test_rotate_camera_pitch_limits(self, renderer: SphereRenderer) -> None:
        """Test camera pitch is clamped to valid range."""
        renderer.rotate_camera(pitch=200.0, yaw=0.0)
        assert renderer.camera_pitch == 90.0

        renderer.camera_pitch = 0.0
        renderer.rotate_camera(pitch=-200.0, yaw=0.0)
        assert renderer.camera_pitch == -90.0

    def test_set_zoom(self, renderer: SphereRenderer) -> None:
        """Test setting zoom level."""
        renderer.set_zoom(2.5)
        assert renderer.zoom == 2.5

    def test_set_zoom_max_clamp(self, renderer: SphereRenderer) -> None:
        """Test zoom is clamped to maximum."""
        renderer.set_zoom(10.0)
        assert renderer.zoom == renderer.max_zoom

    def test_set_zoom_min_clamp(self, renderer: SphereRenderer) -> None:
        """Test zoom is clamped to minimum."""
        renderer.set_zoom(0.1)
        assert renderer.zoom == renderer.min_zoom

    def test_render_empty_graph(self, renderer: SphereRenderer) -> None:
        """Test rendering an empty graph."""
        graph = MazeGraph()

        try:
            renderer.render(graph)
        except Exception as e:
            pytest.fail(f"Rendering empty graph raised exception: {e}")

    def test_render_with_nodes(self, renderer: SphereRenderer) -> None:
        """Test rendering graph with nodes."""
        graph = MazeGraph()
        graph.add_node(0.0, 0.0)
        graph.add_node(10.0, 10.0)

        try:
            renderer.render(graph)
        except Exception as e:
            pytest.fail(f"Rendering graph with nodes raised exception: {e}")

    def test_render_with_edges(self, renderer: SphereRenderer) -> None:
        """Test rendering graph with edges."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0)
        node2 = graph.add_node(10.0, 10.0)
        graph.add_edge(node1.id, node2.id)

        try:
            renderer.render(graph)
        except Exception as e:
            pytest.fail(f"Rendering graph with edges raised exception: {e}")

    def test_render_with_dot(self, renderer: SphereRenderer) -> None:
        """Test rendering with dot entity."""
        graph = MazeGraph()
        dot = DotEntity(latitude=0.0, longitude=0.0)

        try:
            renderer.render(graph, dot=dot)
        except Exception as e:
            pytest.fail(f"Rendering with dot raised exception: {e}")

    def test_get_view_matrix(self, renderer: SphereRenderer) -> None:
        """Test getting view transformation matrix."""
        matrix = renderer.get_view_matrix()

        assert matrix.shape == (3, 3)

    def test_camera_transform(self, renderer: SphereRenderer) -> None:
        """Test camera transformation."""
        x, y, z = 100.0, 0.0, 0.0

        x_t, y_t, z_t = renderer.apply_camera_transform(x, y, z)

        assert isinstance(x_t, float)
        assert isinstance(y_t, float)
        assert isinstance(z_t, float)
