# Quick Start Guide

## Installation (30 seconds)

```bash
cd E:\Spherical_Maze
pip install -e ".[dev]"
```

## Run the Game (5 seconds)

```bash
python main.py
```

## Basic Controls

| Key | Action |
|-----|--------|
| **G** | Generate new maze |
| **P** | Start pathfinding to end |
| **WASD** | Rotate camera around sphere |
| **Q / E** | Zoom in / Zoom out |
| **S** | Save game |
| **L** | Load last save |
| **R** | Reset (clear maze) |
| **ESC** | Quit game |

## Quick Demo (No GUI)

```bash
python demo.py
```

This runs a headless simulation showing:
- Maze generation
- Pathfinding
- Dot navigation
- Save/load system

## Development Quick Start

```bash
# Run tests
pytest

# Format code
ruff format .

# Check code quality
ruff check .

# Run with coverage
pytest --cov
```

## Adding Your OpenAI API Key

Edit `spherical_maze/game.py` line 25:

```python
# Change from:
self.generator = AIMapGenerator(use_dummy=True)

# To:
self.generator = AIMapGenerator(
    api_key="your-api-key-here",
    api_endpoint="https://api.openai.com/v1",
    use_dummy=False
)
```

## Project Structure (5 seconds to understand)

```
spherical_maze/
├── maze_graph.py      # The maze data (cyclic tree)
├── renderer.py        # Draws sphere and maze
├── navigation.py      # Player movement
├── ai_generator.py    # Creates mazes (AI-ready)
├── persistence.py     # Save/load
└── game.py           # Main game loop

tests/                 # 75 tests, all passing
main.py               # Run this to play
demo.py               # Run this for headless demo
```

## Common Tasks

### Generate a Spiral Maze
Press **G** in game, or:
```python
from spherical_maze.ai_generator import AIMapGenerator
gen = AIMapGenerator(use_dummy=True)
maze = gen.generate_maze("Create a spiral maze")
```

### Find Shortest Path
Press **P** in game, or:
```python
from spherical_maze.maze_graph import MazeGraph
graph = MazeGraph()
# ... add nodes ...
path = graph.shortest_path(start_id, end_id)
```

### Save Game
Press **S** in game, or:
```python
from spherical_maze.persistence import SaveManager
manager = SaveManager()
manager.save_game(graph, player_pos, metadata)
```

## Troubleshooting

**Q: Game won't start**
- Ensure pygame is installed: `pip install pygame`

**Q: No maze appears**
- Press **G** to generate a maze

**Q: Can't see anything**
- Use **Q/E** to zoom
- Use **WASD** to rotate camera

**Q: Tests fail**
- Reinstall: `pip install -e ".[dev]"`
- Check Python version: `python --version` (needs 3.9+)

## Next Steps

1. ✅ Install and run (you're here!)
2. 📖 Read `README.md` for full features
3. 🔧 Read `DEVELOPMENT.md` for architecture
4. 🧪 Run `pytest` to see all tests pass
5. 🤖 Add your OpenAI key for AI generation

## That's It!

You now have a fully functional spherical maze game with:
- ✅ Working maze generation
- ✅ 3D spherical rendering
- ✅ Pathfinding and navigation
- ✅ Save/load system
- ✅ 75 passing tests
- ✅ Production-ready code

Enjoy! 🎮🌍
