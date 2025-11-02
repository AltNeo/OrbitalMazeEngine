# Spherical Maze

An AI-powered maze game on a spherical canvas with persistent cyclic tree structure.

## Features

- **Spherical World**: Navigate a maze projected onto a 3D sphere
- **AI Maze Generation**: Generate mazes using procedural algorithms (AI integration ready)
- **Cyclic Tree Structure**: Persistent maze storage allowing cycles and branches
- **Dynamic Pathfinding**: Dijkstra's algorithm for optimal path calculation
- **Save/Load System**: Compressed save files with versioning
- **Interactive Camera**: Rotate and zoom the spherical view

## Installation

```bash
# Install dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Run the game
python main.py
```

## Controls

- **G**: Generate new maze
- **R**: Reset maze
- **S**: Save game
- **L**: Load game
- **P**: Start pathfinding to end
- **WASD**: Rotate camera
- **Q/E**: Zoom in/out
- **ESC**: Quit

## Development

### Run Tests

```bash
pytest
```

### Format Code

```bash
ruff format .
```

### Lint Code

```bash
ruff check .
```

## Project Structure

```
spherical_maze/
├── maze_graph.py      # Cyclic tree data structure
├── renderer.py        # Spherical rendering system
├── navigation.py      # Pathfinding and movement
├── ai_generator.py    # Maze generation (AI-ready)
├── persistence.py     # Save/load system
└── game.py           # Main game engine

tests/
├── test_maze_graph.py
├── test_renderer.py
├── test_navigation.py
├── test_ai_generator.py
└── test_persistence.py
```

## AI Integration

To integrate with OpenAI-compatible API:

1. Set `use_dummy=False` in `AIMapGenerator`
2. Provide your API key and endpoint
3. The system will use AI for maze generation instead of procedural algorithms

```python
generator = AIMapGenerator(
    api_key="your-api-key",
    api_endpoint="https://api.openai.com/v1",
    use_dummy=False
)
```

## Architecture

The game uses a modular architecture:

- **MazeGraph**: Cyclic graph allowing cycles and persistent storage
- **SphereRenderer**: Projects 3D spherical coordinates to 2D screen
- **DotEntity**: Player entity with movement and pathfinding
- **AIMapGenerator**: Generates maze patterns (procedural or AI-based)
- **SaveManager**: Handles game state persistence with compression

## License

MIT License
