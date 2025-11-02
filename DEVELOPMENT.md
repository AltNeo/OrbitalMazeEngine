# Development Guide

## Project Structure

```
spherical_maze/
├── spherical_maze/          # Main package
│   ├── __init__.py         # Package initialization
│   ├── maze_graph.py       # Cyclic tree data structure (MazeGraph, MazeNode, MazeEdge)
│   ├── renderer.py         # Spherical world rendering (SphereRenderer)
│   ├── navigation.py       # Pathfinding and movement (DotEntity, PathFollower)
│   ├── ai_generator.py     # Maze generation (AIMapGenerator)
│   ├── persistence.py      # Save/load system (SaveManager)
│   └── game.py            # Main game engine (SphericalMazeGame)
├── tests/                  # Test suite
│   ├── test_maze_graph.py
│   ├── test_renderer.py
│   ├── test_navigation.py
│   ├── test_ai_generator.py
│   └── test_persistence.py
├── main.py                 # Game entry point
├── demo.py                 # Headless demo
├── pyproject.toml         # Project configuration
└── README.md              # User documentation
```

## Key Components

### 1. MazeGraph (maze_graph.py)
- **MazeNode**: Represents a point on the sphere with lat/lon coordinates
- **MazeEdge**: Connects two nodes with optional path geometry
- **MazeGraph**: Cyclic graph allowing cycles and persistent storage
- Features: Dijkstra's shortest path, cycle detection, spatial queries, JSON serialization

### 2. SphereRenderer (renderer.py)
- Converts spherical coordinates (lat/lon) to 3D Cartesian
- Applies camera transformations (pitch/yaw rotation)
- Projects 3D points to 2D screen space
- Renders maze paths, nodes, and player dot using Pygame

### 3. Navigation (navigation.py)
- **DotEntity**: Player entity with position, speed, and path queue
- **PathFollower**: Manages automatic path following behavior
- Smooth interpolation between waypoints
- Great circle distance calculations

### 4. AIMapGenerator (ai_generator.py)
- Generates maze structures procedurally or via AI
- Supports multiple patterns: spiral, grid, radial, random
- OpenAI-compatible API integration (placeholder)
- Parses AI responses into graph structures

### 5. SaveManager (persistence.py)
- Compressed save files (gzip + JSON)
- Version tracking for compatibility
- Auto-save functionality
- Save/load game state including graph and player position

### 6. SphericalMazeGame (game.py)
- Main game loop with Pygame event handling
- Camera controls (WASD rotation, QE zoom)
- Maze generation (G key)
- Save/load (S/L keys)
- Pathfinding (P key)

## Development Workflow

### Setup
```bash
# Install in development mode
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_maze_graph.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix issues
ruff check . --fix
```

### Running the Game
```bash
# Run full GUI game
python main.py

# Run headless demo
python demo.py
```

## Architecture Decisions

### Spherical Coordinates
- Uses latitude (-90 to 90) and longitude (-180 to 180)
- Great circle distance for accurate spherical pathfinding
- Handles longitude wraparound at ±180°

### Cyclic Tree Structure
- Allows cycles (maze can loop back)
- Bidirectional edges (can traverse both directions)
- UUID-based node/edge identification for persistence
- Efficient spatial queries for nearby node finding

### Rendering Pipeline
```
Maze Graph → Spherical Coords → 3D Cartesian → 
Camera Transform → 2D Projection → Pygame Surface
```

### AI Integration
- Currently uses procedural generation (dummy mode)
- Designed for OpenAI-compatible API integration
- To enable AI: Set `use_dummy=False` and provide API key
- Fallback to procedural if API unavailable

## Testing Strategy

- **Unit Tests**: 75 tests covering all core components
- **Coverage**: 78% overall, >90% for core modules
- **Fixtures**: Pytest fixtures for common test objects
- **Isolation**: Each test is independent with cleanup

## Performance Considerations

- Spatial indexing for large graphs (>10k nodes)
- Visibility culling (only render front hemisphere)
- Efficient pathfinding with Dijkstra's algorithm
- Compressed save files to reduce disk usage

## Future Enhancements

1. **AI Integration**: Connect to real OpenAI API for creative maze generation
2. **Dynamic Expansion**: Generate new maze sections as player explores
3. **Multi-level Mazes**: Support vertical layers on the sphere
4. **Multiplayer**: Multiple dots navigating the same maze
5. **Visual Effects**: Particle systems, trails, smooth animations
6. **Mobile Support**: Touch controls for mobile devices

## Troubleshooting

### Pygame Issues
- If pygame doesn't initialize: Check SDL library installation
- Display issues: Try different display modes in pygame.display.set_mode()

### Test Failures
- Camera transform tests can be sensitive to floating-point precision
- Use appropriate tolerances for coordinate comparisons

### Performance
- Large mazes (>50k nodes) may require optimization
- Consider implementing LOD (Level of Detail) for distant nodes
- Use profiling tools (cProfile) to identify bottlenecks

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Docstrings for all public methods
- Ruff enforced formatting and linting
- Maximum line length: 100 characters

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `pytest`
4. Format code: `ruff format .`
5. Check linting: `ruff check .`
6. Submit PR with clear description
