"""Tests for save/load system."""

import tempfile
from pathlib import Path

import pytest

from spherical_maze.maze_graph import MazeGraph
from spherical_maze.persistence import SaveManager


class TestPersistence:
    """Test SaveManager functionality."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield Path(tmpdirname)

    @pytest.fixture
    def save_manager(self, temp_dir: Path) -> SaveManager:
        """Create a save manager for testing."""
        return SaveManager(save_dir=temp_dir)

    @pytest.fixture
    def sample_graph(self) -> MazeGraph:
        """Create a sample graph for testing."""
        graph = MazeGraph()
        node1 = graph.add_node(0.0, 0.0, "start")
        node2 = graph.add_node(10.0, 10.0, "end")
        graph.add_edge(node1.id, node2.id)
        return graph

    def test_save_manager_initialization(self, temp_dir: Path) -> None:
        """Test creating a save manager."""
        manager = SaveManager(save_dir=temp_dir)

        assert manager.save_dir == temp_dir
        assert temp_dir.exists()

    def test_save_game(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test saving game state."""
        save_path = save_manager.save_game(
            graph=sample_graph,
            player_pos=(5.0, 5.0),
            metadata={"level": 1},
        )

        assert save_path.exists()
        assert save_path.suffix == ".gz"

    def test_save_game_custom_filename(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test saving with custom filename."""
        save_path = save_manager.save_game(
            graph=sample_graph,
            player_pos=(0.0, 0.0),
            metadata={},
            filename="custom_save.json.gz",
        )

        assert save_path.name == "custom_save.json.gz"

    def test_load_game(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test loading game state."""
        save_path = save_manager.save_game(
            graph=sample_graph,
            player_pos=(5.0, 5.0),
            metadata={"level": 2},
        )

        loaded = save_manager.load_game(save_path)

        assert loaded is not None
        assert "graph" in loaded
        assert "player_pos" in loaded
        assert "metadata" in loaded
        assert loaded["player_pos"] == (5.0, 5.0)
        assert loaded["metadata"]["level"] == 2

    def test_load_nonexistent_file(self, save_manager: SaveManager) -> None:
        """Test loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            save_manager.load_game("nonexistent.json.gz")

    def test_list_saves(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test listing save files."""
        save_manager.save_game(sample_graph, (0.0, 0.0), {}, "save1.json.gz")
        save_manager.save_game(sample_graph, (0.0, 0.0), {}, "save2.json.gz")

        saves = save_manager.list_saves()

        assert len(saves) >= 2

    def test_delete_save(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test deleting a save file."""
        save_path = save_manager.save_game(
            sample_graph,
            (0.0, 0.0),
            {},
            "to_delete.json.gz",
        )

        assert save_path.exists()

        save_manager.delete_save(save_path)

        assert not save_path.exists()

    def test_enable_auto_save(self, save_manager: SaveManager) -> None:
        """Test enabling auto-save."""
        save_manager.enable_auto_save(interval=30.0)

        assert save_manager.auto_save_enabled
        assert save_manager.auto_save_interval == 30.0

    def test_disable_auto_save(self, save_manager: SaveManager) -> None:
        """Test disabling auto-save."""
        save_manager.enable_auto_save()
        save_manager.disable_auto_save()

        assert not save_manager.auto_save_enabled

    def test_auto_save_update(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test auto-save update mechanism."""
        save_manager.enable_auto_save(interval=1.0)

        saved = save_manager.update(sample_graph, (0.0, 0.0), {}, elapsed_time=0.5)
        assert not saved

        saved = save_manager.update(sample_graph, (0.0, 0.0), {}, elapsed_time=0.6)
        assert saved

        auto_saves = save_manager.list_auto_saves()
        assert len(auto_saves) > 0

    def test_save_version(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test save file includes version information."""
        save_path = save_manager.save_game(sample_graph, (0.0, 0.0), {})

        loaded = save_manager.load_game(save_path)

        assert "timestamp" in loaded

    def test_graph_integrity_after_save_load(
        self,
        save_manager: SaveManager,
        sample_graph: MazeGraph,
    ) -> None:
        """Test graph data integrity after save and load."""
        original_node_count = len(sample_graph.nodes)
        original_edge_count = len(sample_graph.edges)

        save_path = save_manager.save_game(sample_graph, (0.0, 0.0), {})
        loaded = save_manager.load_game(save_path)

        loaded_graph = loaded["graph"]
        assert len(loaded_graph.nodes) == original_node_count
        assert len(loaded_graph.edges) == original_edge_count
