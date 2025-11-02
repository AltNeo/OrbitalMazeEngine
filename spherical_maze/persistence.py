"""Save/load system for maze persistence."""

import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from spherical_maze.maze_graph import MazeGraph


class SaveManager:
    """Manages saving and loading game state."""

    CURRENT_VERSION = "1.0.0"

    def __init__(self, save_dir: str | Path | None = None) -> None:
        """Initialize save manager."""
        if save_dir is None:
            save_dir = Path.home() / ".spherical_maze" / "saves"

        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save_enabled = False
        self.auto_save_interval = 60.0
        self.last_auto_save = 0.0

    def save_game(
        self,
        graph: MazeGraph,
        player_pos: tuple[float, float],
        metadata: dict[str, Any],
        filename: str | None = None,
    ) -> Path:
        """Save game state to a file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"save_{timestamp}.json.gz"

        save_path = self.save_dir / filename

        save_data = {
            "version": self.CURRENT_VERSION,
            "timestamp": datetime.now().isoformat(),
            "graph": json.loads(graph.to_json()),
            "player_position": {"latitude": player_pos[0], "longitude": player_pos[1]},
            "metadata": metadata,
        }

        with gzip.open(save_path, "wt", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2)

        return save_path

    def load_game(self, filename: str | Path) -> dict[str, Any]:
        """Load game state from a file."""
        load_path = Path(filename)
        if not load_path.is_absolute():
            load_path = self.save_dir / load_path

        if not load_path.exists():
            msg = f"Save file not found: {load_path}"
            raise FileNotFoundError(msg)

        try:
            with gzip.open(load_path, "rt", encoding="utf-8") as f:
                save_data = json.load(f)
        except gzip.BadGzipFile:
            with open(load_path, encoding="utf-8") as f:
                save_data = json.load(f)

        if save_data.get("version") != self.CURRENT_VERSION:
            print(
                f"Warning: Save file version {save_data.get('version')} != {self.CURRENT_VERSION}"
            )

        graph = MazeGraph.from_json(json.dumps(save_data["graph"]))

        player_pos_data = save_data["player_position"]
        player_pos = (player_pos_data["latitude"], player_pos_data["longitude"])

        return {
            "graph": graph,
            "player_pos": player_pos,
            "metadata": save_data.get("metadata", {}),
            "timestamp": save_data.get("timestamp"),
        }

    def list_saves(self) -> list[Path]:
        """List all save files in the save directory."""
        saves = list(self.save_dir.glob("*.json.gz"))
        saves.extend(self.save_dir.glob("*.json"))
        saves.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return saves

    def delete_save(self, filename: str | Path) -> None:
        """Delete a save file."""
        load_path = Path(filename)
        if not load_path.is_absolute():
            load_path = self.save_dir / load_path

        if load_path.exists():
            load_path.unlink()

    def enable_auto_save(self, interval: float = 60.0) -> None:
        """Enable auto-save functionality."""
        self.auto_save_enabled = True
        self.auto_save_interval = interval

    def disable_auto_save(self) -> None:
        """Disable auto-save functionality."""
        self.auto_save_enabled = False

    def update(
        self,
        graph: MazeGraph,
        player_pos: tuple[float, float],
        metadata: dict[str, Any],
        elapsed_time: float,
    ) -> bool:
        """Update auto-save system. Returns True if auto-save was performed."""
        if not self.auto_save_enabled:
            return False

        self.last_auto_save += elapsed_time

        if self.last_auto_save >= self.auto_save_interval:
            self.save_game(graph, player_pos, metadata, "autosave.json.gz")
            self.last_auto_save = 0.0
            return True

        return False

    def list_auto_saves(self) -> list[Path]:
        """List all auto-save files."""
        return list(self.save_dir.glob("autosave*.json.gz"))
