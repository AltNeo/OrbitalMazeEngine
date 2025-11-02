# Repository Guidelines

## Project Structure & Module Organization
Core gameplay logic lives in `spherical_maze/`, with modules such as `maze_graph.py` (graph storage and pathfinding), `renderer.py` (Pygame rendering), `navigation.py` (player movement), `ai_generator.py` (procedural and AI-ready maze creation), and `persistence.py` (save/load). `main.py` boots the interactive game, while `demo.py` provides a headless walk-through for quick validation. Tests mirror the package layout under `tests/`, and `pyproject.toml` centralizes build, dependency, lint, and coverage settings.

## Build, Test, and Development Commands
- `pip install -e ".[dev]"` installs runtime and dev tooling (pytest, coverage, ruff) in editable mode.
- `python main.py` launches the full Pygame experience; use `python demo.py` for a headless systems check.
- `pytest` (or `pytest -v --cov=spherical_maze`) runs the suite with coverage, matching the default `pyproject` addopts.
- `ruff format .` and `ruff check .` format and lint; add `--fix` to auto-apply safe lint corrections.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and the project-wide 100-character line limit enforced by Ruff. Use type hints on public APIs, PascalCase for classes, snake_case for functions and variables, and prefix tests with `test_`. Maintain focused docstrings for modules, classes, and complex routines. Prefer module-level constants in ALL_CAPS and keep demo or CLI entry points in `main.py`/`demo.py`.

## Testing Guidelines
Pytest locates files via `tests/test_*.py`; mirror production module names to keep fixtures discoverable. Add targeted unit tests for new behaviors and ensure coverage for core paths remains at or above the current ~78% baseline. Use `pytest tests/test_navigation.py -k scenario` for focused runs, and verify that temporary assets created in tests are cleaned up.

## Commit & Pull Request Guidelines
Author small, logically grouped commits with imperative subjects (e.g., `Add spiral maze preset`); include short bodies when context aids reviewers. Before opening a PR, run `pytest` and `ruff check .` and report results in the description. Reference related tickets, describe gameplay or UX changes, and attach screenshots or logs when altering rendering or AI output. Highlight any new configuration flags or assets so reviewers can validate them quickly.

## Configuration & Security Notes
AI-powered maze generation stays in dummy mode by default; never commit real API keys. Use environment variables or local config files ignored by Git when toggling `AIMapGenerator` to live API mode. Persisted saves from `persistence.py` store gzip-compressed JSON—treat them as opaque test fixtures and avoid editing by hand.
