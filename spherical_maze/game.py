"""Main game engine and loop."""

import sys
from uuid import UUID

import pygame

from spherical_maze.ai_generator import AIMapGenerator
from spherical_maze.maze_graph import MazeGraph, MazeNode
from spherical_maze.navigation import DotEntity, PathFollower
from spherical_maze.persistence import SaveManager
from spherical_maze.renderer import SphereRenderer


class SphericalMazeGame:
    """Main game controller."""

    def __init__(
        self,
        screen_size: tuple[int, int] = (1024, 768),
        sphere_radius: float = 150.0,
    ) -> None:
        """Initialize the game."""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60

        self.renderer = SphereRenderer(radius=sphere_radius, screen_size=screen_size)
        self.graph = MazeGraph()
        self.generator = AIMapGenerator(use_dummy=True)
        self.save_manager = SaveManager()

        self.dot: DotEntity | None = None
        self.path_follower: PathFollower | None = None
        self.origin_node_id: UUID | None = None
        self._last_waypoint: UUID | None = None
        self.last_prompt = "Create a spiral maze"

        self.camera_rotation_speed = 2.0
        self.zoom_speed = 0.1

        self.font = pygame.font.Font(None, 24)
        self.status_text = "Press G to generate maze, WASD to rotate camera, Q/E to zoom"

    def generate_initial_maze(self, prompt: str = "Create a spiral maze") -> None:
        """Generate the initial maze."""
        self.last_prompt = prompt
        self.graph = MazeGraph()
        self._last_waypoint = None

        maze_data = self.generator.generate_maze(
            prompt, start_position=(0.0, 0.0), complexity="medium"
        )

        start_node = self.generator.import_to_graph(maze_data, self.graph)

        if not start_node:
            self.status_text = "Maze generation failed"
            return

        self.origin_node_id = start_node.id
        self.dot = DotEntity(
            latitude=start_node.latitude,
            longitude=start_node.longitude,
            speed=20.0,
        )
        self._create_path_follower()

        loop_path: list[UUID] = []
        nodes_list = list(self.graph.nodes.values())
        if len(nodes_list) > 1:
            end_node = nodes_list[-1]
            base_path = self.graph.shortest_path(start_node.id, end_node.id)
            loop_path = self._build_loop_path(base_path, start_node.id)

        if self.path_follower and loop_path:
            self.path_follower.start_following(loop_path)

        self.status_text = f"Maze generated with {len(self.graph.nodes)} nodes"

    def _create_path_follower(self) -> None:
        """Create a path follower for the current dot and graph."""
        if not self.dot:
            self.path_follower = None
            return

        self.path_follower = PathFollower(self.dot, self.graph)
        self.path_follower.set_waypoint_callback(self._on_waypoint_reached)

    def _build_loop_path(self, path: list[UUID] | None, origin_id: UUID) -> list[UUID]:
        """Ensure the path returns to the origin node."""
        if not path:
            return []

        loop_path = list(path)
        if loop_path[0] != origin_id:
            loop_path.insert(0, origin_id)

        if loop_path[-1] != origin_id:
            back_path = self.graph.shortest_path(loop_path[-1], origin_id)
            if back_path and len(back_path) > 1:
                loop_path.extend(back_path[1:])

        return loop_path

    def _select_next_target(self) -> MazeNode | None:
        """Choose the next node to visit based on exploration state."""
        if self.origin_node_id is None or self.origin_node_id not in self.graph.nodes:
            return None

        origin = self.graph.nodes[self.origin_node_id]

        def distance(node: MazeNode) -> float:
            return MazeGraph._great_circle_distance(
                origin.latitude,
                origin.longitude,
                node.latitude,
                node.longitude,
            )

        candidates = [
            node
            for node in self.graph.nodes.values()
            if node.id != self.origin_node_id
        ]

        if not candidates:
            return None

        unvisited = [node for node in candidates if not node.visited]
        if unvisited:
            return max(unvisited, key=distance)

        unexpanded = [node for node in candidates if not node.metadata.get("expanded")]
        if unexpanded:
            return max(unexpanded, key=distance)

        return max(candidates, key=distance)

    def _schedule_next_route(self) -> bool:
        """Schedule the next exploration loop."""
        if not self.path_follower or self.origin_node_id is None:
            return False

        target = self._select_next_target()
        if target is None:
            self.status_text = "Exploration complete — no new nodes available"
            return False

        path = self.graph.shortest_path(self.origin_node_id, target.id)
        loop_path = self._build_loop_path(path, self.origin_node_id)

        if len(loop_path) < 2:
            self.status_text = "Unable to build path to next target"
            return False

        self.path_follower.start_following(loop_path)
        self.status_text = f"Exploring toward node {str(target.id)[:8]}"
        return True

    def _on_waypoint_reached(self, node_id: UUID) -> None:
        """Callback when the dot reaches a waypoint."""
        self._last_waypoint = node_id

        node = self.graph.nodes.get(node_id)
        if node is None or node_id == self.origin_node_id:
            return

        if node.metadata.get("expanded"):
            return

        new_nodes = self.generator.expand_maze_from_node(
            self.graph,
            node_id,
            prompt=f"{self.last_prompt} - continuation",
        )

        if new_nodes:
            self.status_text = f"Expanded maze near node {str(node_id)[:8]}"

    def _handle_path_completion(self) -> None:
        """Handle logic once the current path loop finishes."""
        if not self.path_follower or not self.dot or self.origin_node_id is None:
            return

        current = self.graph.get_node_by_position(
            self.dot.latitude, self.dot.longitude, threshold=1.0
        )
        if current is None:
            return

        origin_node = self.graph.nodes.get(self.origin_node_id)
        if origin_node and not origin_node.metadata.get("expanded"):
            new_nodes = self.generator.expand_maze_from_node(
                self.graph,
                origin_node.id,
                prompt=f"{self.last_prompt} - hub expansion",
            )
            if new_nodes:
                self.status_text = (
                    f"Expanded hub with {len(new_nodes)} new nodes — continuing exploration"
                )

        if not self._schedule_next_route():
            self.status_text = (
                f"Reached hub at ({self.dot.latitude:.1f}, {self.dot.longitude:.1f})"
            )

    def handle_events(self) -> None:
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_g:
                    self.generate_initial_maze("Create a random complex maze")

                elif event.key == pygame.K_r:
                    self.graph = MazeGraph()
                    self.dot = None
                    self.path_follower = None
                    self.origin_node_id = None
                    self._last_waypoint = None
                    self.status_text = "Maze reset. Press G to generate new maze."

                elif event.key == pygame.K_s:
                    if self.dot:
                        save_path = self.save_manager.save_game(
                            self.graph,
                            (self.dot.latitude, self.dot.longitude),
                            {"timestamp": pygame.time.get_ticks()},
                        )
                        self.status_text = f"Game saved to {save_path.name}"

                elif event.key == pygame.K_l:
                    saves = self.save_manager.list_saves()
                    if saves:
                        loaded = self.save_manager.load_game(saves[0])
                        self.graph = loaded["graph"]
                        lat, lon = loaded["player_pos"]
                        self.dot = DotEntity(latitude=lat, longitude=lon, speed=20.0)
                        self._create_path_follower()
                        origin_node = self.graph.get_node_by_position(lat, lon, threshold=2.0)
                        if origin_node:
                            self.origin_node_id = origin_node.id
                        elif self.graph.nodes:
                            self.origin_node_id = next(iter(self.graph.nodes))
                        else:
                            self.origin_node_id = None
                        self.status_text = "Game loaded successfully"
                    else:
                        self.status_text = "No save files found"

                elif event.key == pygame.K_p:
                    if self.path_follower and not self.path_follower.is_following:
                        self._schedule_next_route()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.renderer.rotate_camera(pitch=self.camera_rotation_speed, yaw=0)
        if keys[pygame.K_s]:
            self.renderer.rotate_camera(pitch=-self.camera_rotation_speed, yaw=0)
        if keys[pygame.K_a]:
            self.renderer.rotate_camera(pitch=0, yaw=-self.camera_rotation_speed)
        if keys[pygame.K_d]:
            self.renderer.rotate_camera(pitch=0, yaw=self.camera_rotation_speed)

        if keys[pygame.K_q]:
            self.renderer.set_zoom(self.renderer.zoom - self.zoom_speed)
        if keys[pygame.K_e]:
            self.renderer.set_zoom(self.renderer.zoom + self.zoom_speed)

    def update(self, delta_time: float) -> None:
        """Update game state."""
        if self.path_follower:
            was_complete = self.path_follower.is_complete()
            self.path_follower.update(delta_time)

            if self.path_follower.is_complete() and not was_complete:
                if self.dot:
                    self.status_text = (
                        f"Reached destination at ({self.dot.latitude:.1f}, {self.dot.longitude:.1f})"
                    )
                self._handle_path_completion()

    def render(self) -> None:
        """Render the game."""
        self.renderer.render(self.graph, self.dot, show_all_nodes=True)

        text_surface = self.font.render(self.status_text, True, (255, 255, 255))
        self.renderer.screen.blit(text_surface, (10, 10))

        info_text = f"Nodes: {len(self.graph.nodes)} | Edges: {len(self.graph.edges)} | FPS: {int(self.clock.get_fps())}"
        info_surface = self.font.render(info_text, True, (200, 200, 200))
        self.renderer.screen.blit(info_surface, (10, 40))

        if self.dot:
            nearest = self.graph.get_node_by_position(
                self.dot.latitude, self.dot.longitude, threshold=2.0
            )
            node_label = str(nearest.id)[:8] if nearest else "none"
            remaining = max(0, len(self.dot.path_queue) - self.dot.current_path_index)
            position_text = (
                f"Dot lat {self.dot.latitude:.1f}°, lon {self.dot.longitude:.1f}° | "
                f"Node {node_label} | Waypoints left {remaining}"
            )
            pos_surface = self.font.render(position_text, True, (220, 220, 220))
            self.renderer.screen.blit(pos_surface, (10, 70))

        camera_text = (
            f"View pitch {self.renderer.camera_pitch:.0f}° "
            f"yaw {self.renderer.camera_yaw:.0f}° "
            f"zoom {self.renderer.zoom:.2f}x"
        )
        camera_surface = self.font.render(camera_text, True, (160, 160, 170))
        self.renderer.screen.blit(camera_surface, (10, 96))

        controls = "G:Generate R:Reset S:Save L:Load P:Path WASD:Rotate QE:Zoom ESC:Quit"
        control_surface = self.font.render(controls, True, (180, 180, 180))
        self.renderer.screen.blit(control_surface, (10, self.renderer.screen_height - 30))

        pygame.display.flip()

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        self.generate_initial_maze()

        while self.running:
            delta_time = self.clock.tick(self.fps) / 1000.0

            self.handle_events()
            self.update(delta_time)
            self.render()

        self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources."""
        self.renderer.cleanup()
        pygame.quit()


def main() -> int:
    """Entry point for the game."""
    game = SphericalMazeGame(screen_size=(1024, 768))
    game.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
