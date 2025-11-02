"""AI maze generation system with OpenAI-compatible interface."""

import json
import os
import random
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from uuid import UUID

from spherical_maze.maze_graph import MazeGraph, MazeNode


def _load_env_file(path: str = ".env") -> None:
    """Lightweight .env loader so environment configuration is automatic."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


class AIMapGenerator:
    """Generates maze structures using AI or procedural fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        api_endpoint: str | None = None,
        model: str | None = None,
        use_dummy: bool = True,
    ) -> None:
        """Initialize the maze generator."""
        env_api_key = os.getenv("OPEN_ROUTER_KEY") or os.getenv("OPENAI_API_KEY")
        env_endpoint = os.getenv("BASE_URL") or os.getenv("OPEN_ROUTER_BASE_URL")
        env_model = os.getenv("OPEN_ROUTER_MODEL") or os.getenv("OPENAI_MODEL")

        # Preserve explicit arguments, otherwise fall back to environment values.
        self.api_key = api_key if api_key is not None else (env_api_key or "dummy-key")
        self.api_endpoint = (
            api_endpoint if api_endpoint is not None else (env_endpoint or "https://api.openai.com/v1")
        )
        self.model = model if model is not None else (env_model or "gpt-4o-mini")
        self.use_dummy = use_dummy
        self.request_count = 0
        self.max_requests_per_minute = 60

    def generate_maze(
        self,
        prompt: str,
        start_position: tuple[float, float] = (0.0, 0.0),
        complexity: str = "medium",
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Generate a maze based on a text prompt."""
        if self.use_dummy:
            return self._generate_dummy_maze(start_position, complexity, prompt)

        if not self.can_make_request():
            msg = "AI request rate limit exceeded"
            raise RuntimeError(msg)

        if not self.api_key or self.api_key == "dummy-key":
            msg = "An API key is required when use_dummy is False"
            raise ValueError(msg)

        return self._generate_ai_maze(prompt, start_position, timeout, complexity)

    def _generate_dummy_maze(
        self,
        start_position: tuple[float, float],
        complexity: str,
        prompt: str,
    ) -> dict[str, Any]:
        """Generate a procedural maze for testing."""
        nodes = []
        edges = []

        complexity_map = {"simple": 5, "medium": 10, "complex": 20}
        num_nodes = complexity_map.get(complexity, 10)

        start_lat, start_lon = start_position
        nodes.append(
            {
                "latitude": start_lat,
                "longitude": start_lon,
                "generation_prompt": prompt,
            }
        )

        patterns = {
            "spiral": self._generate_spiral_pattern,
            "grid": self._generate_grid_pattern,
            "random": self._generate_random_pattern,
            "radial": self._generate_radial_pattern,
        }

        pattern = "random"
        for key in patterns:
            if key in prompt.lower():
                pattern = key
                break

        pattern_nodes = patterns[pattern](start_position, num_nodes)
        nodes.extend(pattern_nodes)

        for i in range(len(nodes) - 1):
            edges.append({"from_index": i, "to_index": i + 1, "cost": 1.0})

        if num_nodes > 5 and random.random() > 0.5:
            for _ in range(num_nodes // 5):
                idx_a = random.randint(0, len(nodes) - 1)
                idx_b = random.randint(0, len(nodes) - 1)
                if idx_a != idx_b and abs(idx_a - idx_b) > 2:
                    edges.append({"from_index": idx_a, "to_index": idx_b, "cost": 2.0})

        return {"nodes": nodes, "edges": edges, "pattern": pattern}

    def _generate_spiral_pattern(
        self, start: tuple[float, float], num_nodes: int
    ) -> list[dict[str, float]]:
        """Generate a spiral pattern of nodes."""
        nodes = []
        start_lat, start_lon = start

        for i in range(1, num_nodes):
            angle = i * 30
            radius = i * 5
            lat = start_lat + radius * 0.1 * (1 if i % 2 == 0 else -1)
            lon = start_lon + angle % 360 - 180
            nodes.append({"latitude": lat, "longitude": lon, "generation_prompt": "spiral"})

        return nodes

    def _generate_grid_pattern(
        self, start: tuple[float, float], num_nodes: int
    ) -> list[dict[str, float]]:
        """Generate a grid pattern of nodes."""
        nodes = []
        start_lat, start_lon = start
        grid_size = int(num_nodes**0.5)

        for i in range(1, num_nodes):
            row = i // grid_size
            col = i % grid_size
            lat = start_lat + row * 10
            lon = start_lon + col * 10
            if lon > 180:
                lon -= 360
            elif lon < -180:
                lon += 360
            nodes.append({"latitude": lat, "longitude": lon, "generation_prompt": "grid"})

        return nodes

    def _generate_random_pattern(
        self, start: tuple[float, float], num_nodes: int
    ) -> list[dict[str, float]]:
        """Generate a random pattern of nodes."""
        nodes = []
        start_lat, start_lon = start

        for _ in range(1, num_nodes):
            lat = start_lat + random.uniform(-30, 30)
            lon = start_lon + random.uniform(-30, 30)
            lat = max(-90, min(90, lat))
            if lon > 180:
                lon -= 360
            elif lon < -180:
                lon += 360
            nodes.append({"latitude": lat, "longitude": lon, "generation_prompt": "random"})

        return nodes

    def _generate_radial_pattern(
        self, start: tuple[float, float], num_nodes: int
    ) -> list[dict[str, float]]:
        """Generate a radial pattern of nodes."""
        nodes = []
        start_lat, start_lon = start
        num_rays = 4
        nodes_per_ray = num_nodes // num_rays

        for ray in range(num_rays):
            angle = ray * (360 / num_rays)
            for i in range(1, nodes_per_ray + 1):
                radius = i * 5
                lat = start_lat + radius * 0.1 * (1 if ray % 2 == 0 else -1)
                lon = start_lon + angle + i * 5
                if lon > 180:
                    lon -= 360
                elif lon < -180:
                    lon += 360
                lat = max(-90, min(90, lat))
                nodes.append({"latitude": lat, "longitude": lon, "generation_prompt": "radial"})

        return nodes[: num_nodes - 1]

    def _generate_ai_maze(
        self,
        prompt: str,
        start_position: tuple[float, float],
        timeout: float,
        complexity: str,
    ) -> dict[str, Any]:
        """Generate maze using an OpenAI-compatible API endpoint."""
        self.request_count += 1

        url = f"{self.api_endpoint.rstrip('/')}/chat/completions"
        system_prompt = (
            "You design mazes that live on a spherical surface. Respond using only coordinate "
            "pairs in the format (latitude, longitude) per line, ordered so edges connect "
            "sequentially. Keep latitude within [-90, 90] and longitude within [-180, 180]."
        )
        user_prompt = (
            f"{prompt}\n"
            f"Start node: ({start_position[0]}, {start_position[1]}).\n"
            f"Complexity: {complexity}.\n"
            "Output at least five coordinate pairs."
        )

        payload = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        request_data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError:
            return self._generate_dummy_maze(start_position, complexity, prompt)

        try:
            response_json = json.loads(body)
            choices = response_json.get("choices", [])
            content = choices[0]["message"]["content"] if choices else ""
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return self._generate_dummy_maze(start_position, complexity, prompt)

        parsed = self.parse_response(content)
        if not parsed["nodes"]:
            return self._generate_dummy_maze(start_position, complexity, prompt)

        for node in parsed["nodes"]:
            node.setdefault("generation_prompt", f"AI:{prompt[:100]}")
        parsed["pattern"] = "ai"
        return parsed

    def parse_response(self, response: str) -> dict[str, Any]:
        """Parse AI response text into structured maze data."""
        nodes = []
        edges = []

        coord_pattern = r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)"
        matches = re.findall(coord_pattern, response)

        for match in matches:
            lat, lon = float(match[0]), float(match[1])
            nodes.append({"latitude": lat, "longitude": lon, "generation_prompt": response[:100]})

        for i in range(len(nodes) - 1):
            edges.append({"from_index": i, "to_index": i + 1, "cost": 1.0})

        return {"nodes": nodes, "edges": edges}

    def create_prompt(
        self,
        start_node: tuple[float, float],
        complexity: str,
        style: str,
    ) -> str:
        """Create a formatted prompt for maze generation."""
        return (
            f"Create a {complexity} complexity maze with {style} paths "
            f"starting from node at ({start_node[0]}, {start_node[1]}) "
            f"on a spherical surface. Generate connected waypoints."
        )

    def can_make_request(self) -> bool:
        """Check if rate limit allows making a request."""
        return self.request_count < self.max_requests_per_minute

    def import_to_graph(self, maze_data: dict[str, Any], graph: MazeGraph) -> MazeNode:
        """Import generated maze data into a MazeGraph."""
        node_map: dict[int, UUID] = {}
        pattern = maze_data.get("pattern", "generated")

        for index, node_data in enumerate(maze_data["nodes"]):
            latitude = node_data["latitude"]
            longitude = node_data["longitude"]
            prompt_text = node_data.get("generation_prompt", "")

            existing = graph.get_node_by_position(latitude, longitude, threshold=0.25)
            if existing is not None:
                if prompt_text:
                    existing.generation_prompt = prompt_text
                node_map[index] = existing.id
                continue

            node = graph.add_node(
                latitude=latitude,
                longitude=longitude,
                generation_prompt=prompt_text,
            )
            node.metadata.setdefault("source", pattern)
            node_map[index] = node.id

        for edge_data in maze_data["edges"]:
            from_idx = edge_data["from_index"]
            to_idx = edge_data["to_index"]
            cost = edge_data.get("cost", 1.0)
            raw_path = edge_data.get("path_points")

            if from_idx in node_map and to_idx in node_map and node_map[from_idx] != node_map[to_idx]:
                path_points = None
                if raw_path:
                    path_points = [(float(lat), float(lon)) for lat, lon in raw_path]
                graph.add_edge(node_map[from_idx], node_map[to_idx], cost, path_points=path_points)

        return graph.nodes[node_map[0]] if node_map else None

    def expand_maze_from_node(
        self,
        graph: MazeGraph,
        node_id: UUID,
        prompt: str = "expand maze",
    ) -> list[UUID]:
        """Expand the maze from a specific node and return created node IDs."""
        if node_id not in graph.nodes:
            return []

        node = graph.nodes[node_id]

        if node.metadata.get("expanded"):
            return []

        existing_nodes = set(graph.nodes.keys())
        expansion_data = self.generate_maze(
            prompt=f"Expand {prompt}",
            start_position=(node.latitude, node.longitude),
            complexity="simple",
        )

        new_node_ids: list[UUID] = []
        if expansion_data["nodes"]:
            start_node = self.import_to_graph(expansion_data, graph)
            new_node_ids = [nid for nid in graph.nodes.keys() if nid not in existing_nodes]

            if start_node and start_node.id != node_id and start_node.id in new_node_ids:
                graph.add_edge(node_id, start_node.id)

        node.metadata.setdefault("expansion_attempts", 0)
        node.metadata["expansion_attempts"] += 1

        if new_node_ids:
            node.metadata["expanded"] = True
            node.metadata["expanded_prompt"] = prompt

        return new_node_ids
