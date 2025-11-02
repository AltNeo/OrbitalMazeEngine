"""Tests for AI maze generation."""

import pytest

from spherical_maze.ai_generator import AIMapGenerator
from spherical_maze.maze_graph import MazeGraph


class TestAIMapGenerator:
    """Test AI maze generator functionality."""

    def test_generator_initialization(self) -> None:
        """Test creating a generator."""
        gen = AIMapGenerator(api_key="test-key", use_dummy=True)

        assert gen.api_key == "test-key"
        assert gen.use_dummy

    def test_generate_dummy_maze_simple(self) -> None:
        """Test generating a simple dummy maze."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a simple maze", complexity="simple")

        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) > 0
        assert len(result["edges"]) > 0

    def test_generate_dummy_maze_medium(self) -> None:
        """Test generating a medium complexity maze."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a medium maze", complexity="medium")

        assert len(result["nodes"]) >= 10

    def test_generate_dummy_maze_complex(self) -> None:
        """Test generating a complex maze."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a complex maze", complexity="complex")

        assert len(result["nodes"]) >= 20

    def test_generate_spiral_pattern(self) -> None:
        """Test spiral pattern generation."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a spiral maze", start_position=(0.0, 0.0))

        assert "pattern" in result
        assert result["pattern"] == "spiral"

    def test_generate_grid_pattern(self) -> None:
        """Test grid pattern generation."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a grid maze", start_position=(0.0, 0.0))

        assert result["pattern"] == "grid"

    def test_generate_radial_pattern(self) -> None:
        """Test radial pattern generation."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a radial maze", start_position=(0.0, 0.0))

        assert result["pattern"] == "radial"

    def test_generate_random_pattern(self) -> None:
        """Test random pattern generation."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Create a random maze", start_position=(0.0, 0.0))

        assert result["pattern"] == "random"

    def test_parse_response_valid(self) -> None:
        """Test parsing valid AI response."""
        gen = AIMapGenerator(use_dummy=True)
        response = "Node at (10.5, 20.3) connects to (15.0, 25.5) and (20.0, 30.0)"

        parsed = gen.parse_response(response)

        assert len(parsed["nodes"]) == 3
        assert parsed["nodes"][0]["latitude"] == 10.5
        assert parsed["nodes"][0]["longitude"] == 20.3

    def test_parse_response_invalid(self) -> None:
        """Test parsing invalid AI response."""
        gen = AIMapGenerator(use_dummy=True)
        response = "No coordinates here"

        parsed = gen.parse_response(response)

        assert len(parsed["nodes"]) == 0

    def test_create_prompt(self) -> None:
        """Test prompt template formatting."""
        gen = AIMapGenerator(use_dummy=True)
        prompt = gen.create_prompt(
            start_node=(0.0, 0.0),
            complexity="medium",
            style="winding",
        )

        assert "medium" in prompt
        assert "winding" in prompt
        assert "0.0, 0.0" in prompt

    def test_can_make_request(self) -> None:
        """Test rate limiting."""
        gen = AIMapGenerator(use_dummy=True)
        assert gen.can_make_request()

        gen.request_count = 65
        assert not gen.can_make_request()

    def test_import_to_graph(self) -> None:
        """Test importing maze data to graph."""
        gen = AIMapGenerator(use_dummy=True)
        graph = MazeGraph()

        maze_data = gen.generate_maze("Test maze", complexity="simple")
        start_node = gen.import_to_graph(maze_data, graph)

        assert start_node is not None
        assert len(graph.nodes) == len(maze_data["nodes"])
        assert len(graph.edges) == len(maze_data["edges"])
        for edge in graph.edges.values():
            assert len(edge.path_points) >= 2

    def test_import_reuses_existing_start_node(self) -> None:
        """Test importing respects existing nodes at same position."""
        gen = AIMapGenerator(use_dummy=True)
        graph = MazeGraph()

        existing = graph.add_node(0.0, 0.0, "origin")
        maze_data = {
            "nodes": [
                {"latitude": 0.0, "longitude": 0.0, "generation_prompt": "origin"},
                {"latitude": 5.0, "longitude": 5.0, "generation_prompt": "new"},
            ],
            "edges": [{"from_index": 0, "to_index": 1, "cost": 1.0}],
            "pattern": "test",
        }

        start_node = gen.import_to_graph(maze_data, graph)

        assert start_node.id == existing.id
        assert len(graph.nodes) == 2

    def test_expand_maze_from_node(self) -> None:
        """Test expanding maze from existing node."""
        gen = AIMapGenerator(use_dummy=True)
        graph = MazeGraph()

        node1 = graph.add_node(0.0, 0.0)
        initial_node_count = len(graph.nodes)

        new_nodes = gen.expand_maze_from_node(graph, node1.id, "expand with simple paths")

        assert len(graph.nodes) > initial_node_count
        assert isinstance(new_nodes, list)
        if new_nodes:
            assert graph.nodes[node1.id].metadata.get("expanded")
            for edge in graph.edges.values():
                assert len(edge.path_points) >= 2

    def test_generate_maze_requires_api_key_when_not_dummy(self) -> None:
        """Test that real generation mode validates API key presence."""
        gen = AIMapGenerator(use_dummy=False, api_key="")

        with pytest.raises(ValueError):
            gen.generate_maze("Should fail", start_position=(0.0, 0.0))

    def test_maze_data_structure(self) -> None:
        """Test generated maze has correct structure."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Test", start_position=(5.0, 10.0))

        assert isinstance(result["nodes"], list)
        assert isinstance(result["edges"], list)

        if result["nodes"]:
            node = result["nodes"][0]
            assert "latitude" in node
            assert "longitude" in node

        if result["edges"]:
            edge = result["edges"][0]
            assert "from_index" in edge
            assert "to_index" in edge

    def test_coordinate_bounds(self) -> None:
        """Test generated coordinates are within valid bounds."""
        gen = AIMapGenerator(use_dummy=True)
        result = gen.generate_maze("Large maze", complexity="complex", start_position=(0.0, 0.0))

        for node in result["nodes"]:
            assert -90.0 <= node["latitude"] <= 90.0
            assert -180.0 <= node["longitude"] <= 180.0
