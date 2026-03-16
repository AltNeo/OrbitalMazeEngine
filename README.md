# Orbital Maze Engine

A spherical maze project with legacy Python prototypes and a browser-first Three.js build.

The current recommended entry point is the web prototype in [`web/`](web/), which
renders a first-person maze on the inner surface of a hollow sphere and pairs it with a spherical
radar view of the active graph.

## Current Status

- Recommended mode: browser prototype in `web/`
- Legacy modes: Python/Pygame prototypes in `main.py` and related `spherical_maze/` modules
- Maze structure: cyclic node graph embedded onto a sphere
- Goal: walk corridor arcs, navigate junctions, and reach the beacon target

## Run The Web Prototype

From the repository root:

```bash
cd web
python -m http.server 8080
```

Open:

```text
http://127.0.0.1:8080
```

No build step is required.

## Controls

- `W`: move forward
- `S`: move backward
- `A`: bias branch choice left and lean left
- `D`: bias branch choice right and lean right
- `M`: hide/show the radar panel
- `R`: generate a new sphere

## How Junction Choice Works

Junction selection is currently bias-based, not menu-based:

- hold `A` to prefer the left branch
- hold `D` to prefer the right branch
- hold neither to prefer the branch closest to straight ahead

This means a three-way node is navigable, but branch choice is still driven by left/forward/right
bias rather than explicit per-exit selection.

## Web Prototype Notes

- The browser app uses an import map and loads Three.js from the official CDN.
- Google Fonts are loaded from the web at runtime.
- If those remote assets are blocked, the page will not render correctly without local replacements.
- The right-hand radar shows your in-progress position along the active corridor, not just the
  destination node.
- The first-person scene uses shared junction chambers so multi-way nodes do not collapse into a
  single overlapping pile of corridor walls.

## Repository Layout

- [`web/index.html`](web/index.html): entry page
- [`web/app.js`](web/app.js): main loop and input
- [`web/maze.js`](web/maze.js): graph, navigation, and branch selection
- [`web/render.js`](web/render.js): radar and HUD rendering
- [`web/three-view.js`](web/three-view.js): Three.js corridor and junction scene
- [`spherical_maze/`](spherical_maze/): older Python gameplay/rendering modules

## Legacy Python Prototype

The older Python stack is still present for reference and experiments:

```bash
pip install -e ".[dev]"
python main.py
```

That path is no longer the recommended way to experience the project.

## Development Checks

For the browser files:

```bash
node --check web/app.js
node --check web/maze.js
node --check web/render.js
node --check web/three-view.js
```

For the Python codebase:

```bash
ruff check .
pytest
```

## License

MIT License
