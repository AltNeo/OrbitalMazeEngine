"""V2: First-person game engine with mouse look and WASD movement."""

import sys

import pygame

from spherical_maze.ai_generator import AIMapGenerator
from spherical_maze.maze_graph import MazeGraph
from spherical_maze.navigation import DotEntity
from spherical_maze.persistence import SaveManager
from spherical_maze.renderer_v2 import FirstPersonRenderer


class FirstPersonMazeGame:
    """V2: First-person maze game controller."""

    def __init__(
        self,
        screen_size: tuple[int, int] = (1024, 768),
        sphere_radius: float = 150.0,
    ) -> None:
        """Initialize the first-person game."""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60

        self.renderer = FirstPersonRenderer(radius=sphere_radius, screen_size=screen_size)
        self.graph = MazeGraph()
        self.generator = AIMapGenerator(use_dummy=True)
        self.save_manager = SaveManager()

        self.dot: DotEntity | None = None

        # V2: First-person control settings
        self.mouse_sensitivity = 0.2
        self.move_speed = 10.0
        self.mouse_grabbed = False

        self.font = pygame.font.Font(None, 24)
        self.status_text = "Press G to generate maze | ESC to toggle mouse | WASD to move"
        self.show_debug = False

    def generate_initial_maze(self, prompt: str = "Create a grid maze") -> None:
        """Generate the initial maze."""
        maze_data = self.generator.generate_maze(
            prompt, start_position=(0.0, 0.0), complexity="medium"
        )

        start_node = self.generator.import_to_graph(maze_data, self.graph)

        if start_node:
            # V2: Create player at start position with first-person properties
            self.dot = DotEntity(
                latitude=start_node.latitude,
                longitude=start_node.longitude,
                speed=self.move_speed,
                yaw=0.0,
                pitch=0.0,
                height=5.0,
            )

            self.status_text = (
                f"Maze generated with {len(self.graph.nodes)} nodes | "
                f"WASD to move, Mouse to look | ESC to toggle mouse"
            )

    def toggle_mouse_grab(self) -> None:
        """Toggle mouse capture for first-person look."""
        self.mouse_grabbed = not self.mouse_grabbed

        if self.mouse_grabbed:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            # Center mouse to avoid jump
            pygame.mouse.set_pos(self.renderer.screen_width // 2, self.renderer.screen_height // 2)
            pygame.mouse.get_rel()  # Clear relative movement
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

    def handle_events(self) -> None:
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.mouse_grabbed:
                        self.toggle_mouse_grab()
                    else:
                        self.running = False

                elif event.key == pygame.K_g:
                    self.generate_initial_maze("Create a random complex maze")

                elif event.key == pygame.K_r:
                    self.graph = MazeGraph()
                    self.dot = None
                    self.status_text = "Maze reset. Press G to generate new maze."

                elif event.key == pygame.K_s:
                    if self.dot:
                        save_path = self.save_manager.save_game(
                            self.graph,
                            (self.dot.latitude, self.dot.longitude),
                            {
                                "yaw": self.dot.yaw,
                                "pitch": self.dot.pitch,
                                "timestamp": pygame.time.get_ticks(),
                            },
                        )
                        self.status_text = f"Game saved to {save_path.name}"

                elif event.key == pygame.K_l:
                    saves = self.save_manager.list_saves()
                    if saves:
                        loaded = self.save_manager.load_game(saves[0])
                        self.graph = loaded["graph"]
                        lat, lon = loaded["player_pos"]

                        # Restore V2 properties
                        yaw = loaded["metadata"].get("yaw", 0.0)
                        pitch = loaded["metadata"].get("pitch", 0.0)

                        self.dot = DotEntity(
                            latitude=lat,
                            longitude=lon,
                            speed=self.move_speed,
                            yaw=yaw,
                            pitch=pitch,
                        )
                        self.status_text = "Game loaded successfully"
                    else:
                        self.status_text = "No save files found"

                elif event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug

                elif event.key == pygame.K_TAB:
                    self.toggle_mouse_grab()

        # V2: Mouse look (only when grabbed)
        if self.mouse_grabbed and self.dot:
            mouse_dx, mouse_dy = pygame.mouse.get_rel()
            if mouse_dx != 0 or mouse_dy != 0:
                self.dot.rotate_view(
                    mouse_dx * self.mouse_sensitivity,
                    mouse_dy * self.mouse_sensitivity,
                )

    def update(self, delta_time: float) -> None:
        """Update game state."""
        if not self.dot:
            return

        # V2: WASD movement (continuous, not event-based)
        keys = pygame.key.get_pressed()

        forward = 0.0
        strafe = 0.0

        if keys[pygame.K_w]:
            forward += 1.0
        if keys[pygame.K_s]:
            forward -= 1.0
        if keys[pygame.K_a]:
            strafe -= 1.0
        if keys[pygame.K_d]:
            strafe += 1.0

        # Apply movement
        if forward != 0.0 or strafe != 0.0:
            self.dot.move_by(forward, strafe, delta_time)

    def render(self) -> None:
        """Render the game."""
        self.renderer.render(self.graph, self.dot)

        # UI overlay
        if not self.mouse_grabbed:
            # Status text
            text_surface = self.font.render(self.status_text, True, (255, 255, 255))
            self.renderer.screen.blit(text_surface, (10, 10))

            # Info text
            info_text = (
                f"Nodes: {len(self.graph.nodes)} | Edges: {len(self.graph.edges)} | "
                f"FPS: {int(self.clock.get_fps())}"
            )
            info_surface = self.font.render(info_text, True, (200, 200, 200))
            self.renderer.screen.blit(info_surface, (10, 40))

            # Controls
            controls = (
                "TAB:Grab Mouse | WASD:Move | Mouse:Look | G:Generate | S:Save | L:Load | R:Reset"
            )
            control_surface = self.font.render(controls, True, (180, 180, 180))
            self.renderer.screen.blit(control_surface, (10, self.renderer.screen_height - 30))

        # Debug info
        if self.show_debug and self.dot:
            debug_lines = [
                f"Position: ({self.dot.latitude:.2f}, {self.dot.longitude:.2f})",
                f"Yaw: {self.dot.yaw:.1f}° | Pitch: {self.dot.pitch:.1f}°",
                f"Mouse: {'GRABBED' if self.mouse_grabbed else 'FREE'}",
            ]

            y_offset = 70
            for line in debug_lines:
                debug_surface = self.font.render(line, True, (255, 255, 0))
                self.renderer.screen.blit(debug_surface, (10, y_offset))
                y_offset += 25

        # Crosshair (when mouse is grabbed)
        if self.mouse_grabbed:
            center_x = self.renderer.screen_width // 2
            center_y = self.renderer.screen_height // 2
            pygame.draw.circle(self.renderer.screen, (255, 255, 255), (center_x, center_y), 3, 1)
            pygame.draw.line(
                self.renderer.screen,
                (255, 255, 255),
                (center_x - 10, center_y),
                (center_x + 10, center_y),
                1,
            )
            pygame.draw.line(
                self.renderer.screen,
                (255, 255, 255),
                (center_x, center_y - 10),
                (center_x, center_y + 10),
                1,
            )

        pygame.display.flip()

    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        self.generate_initial_maze()

        # Auto-grab mouse on start
        self.toggle_mouse_grab()

        while self.running:
            delta_time = self.clock.tick(self.fps) / 1000.0

            self.handle_events()
            self.update(delta_time)
            self.render()

        self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.mouse_grabbed:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        self.renderer.cleanup()
        pygame.quit()


def main() -> int:
    """Entry point for V2 first-person game."""
    game = FirstPersonMazeGame(screen_size=(1024, 768))
    game.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
