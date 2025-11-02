"""Spherical world rendering system using Pygame."""

import math
from typing import TYPE_CHECKING

import numpy as np
import pygame

if TYPE_CHECKING:
    from spherical_maze.maze_graph import MazeGraph, MazeNode
    from spherical_maze.navigation import DotEntity


class SphereRenderer:
    """Renders the spherical maze world using 2D projection."""

    def __init__(self, radius: float, screen_size: tuple[int, int]) -> None:
        """Initialize the renderer."""
        self.radius = radius
        self.screen_width, self.screen_height = screen_size
        self.zoom = 1.0
        self.camera_lat = 0.0
        self.camera_lon = 0.0
        self.camera_pitch = 0.0
        self.camera_yaw = 0.0

        self.min_zoom = 0.5
        self.max_zoom = 5.0

        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Spherical Maze")

        self.bg_color = (6, 8, 20)
        self.sphere_color = (18, 28, 55)
        self.sphere_highlight = (55, 85, 135)
        self.grid_color = (45, 90, 140)
        self.wall_shadow_color = (10, 18, 32)
        self.wall_color = (30, 50, 90)
        self.wall_rim_color = (70, 110, 170)
        self.path_color = (210, 235, 255)
        self.path_highlight = (255, 255, 255)
        self.node_color = (255, 245, 170)
        self.dot_color = (255, 90, 90)

    def spherical_to_cartesian(
        self, latitude: float, longitude: float
    ) -> tuple[float, float, float]:
        """Convert spherical coordinates to 3D Cartesian coordinates."""
        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)

        x = self.radius * math.cos(lat_rad) * math.cos(lon_rad)
        y = self.radius * math.cos(lat_rad) * math.sin(lon_rad)
        z = self.radius * math.sin(lat_rad)

        return x, y, z

    def apply_camera_transform(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        """Apply camera rotation to 3D coordinates."""
        pitch_rad = math.radians(self.camera_pitch)
        yaw_rad = math.radians(self.camera_yaw)

        cos_pitch = math.cos(pitch_rad)
        sin_pitch = math.sin(pitch_rad)
        cos_yaw = math.cos(yaw_rad)
        sin_yaw = math.sin(yaw_rad)

        x_rot = x * cos_yaw - y * sin_yaw
        y_rot = x * sin_yaw + y * cos_yaw

        z_rot = z * cos_pitch - x_rot * sin_pitch
        x_final = z * sin_pitch + x_rot * cos_pitch

        return x_final, y_rot, z_rot

    def project_with_depth(
        self, latitude: float, longitude: float
    ) -> tuple[tuple[int, int], float] | None:
        """Project spherical coordinates returning screen position and depth."""
        x, y, z = self.spherical_to_cartesian(latitude, longitude)
        x, y, z = self.apply_camera_transform(x, y, z)

        if z < 0:
            return None

        screen_x = int(self.screen_width / 2 + x * self.zoom)
        screen_y = int(self.screen_height / 2 - y * self.zoom)

        if 0 <= screen_x < self.screen_width and 0 <= screen_y < self.screen_height:
            return (screen_x, screen_y), z

        return None

    def project_to_screen(self, latitude: float, longitude: float) -> tuple[int, int] | None:
        """Project spherical coordinates to 2D screen space."""
        result = self.project_with_depth(latitude, longitude)
        if result is None:
            return None
        return result[0]

    def is_visible(self, latitude: float, longitude: float) -> bool:
        """Check if a point on the sphere is visible from the camera."""
        return self.project_with_depth(latitude, longitude) is not None

    def rotate_camera(self, pitch: float, yaw: float) -> None:
        """Rotate the camera by the given angles."""
        self.camera_pitch = max(-90.0, min(90.0, self.camera_pitch + pitch))
        self.camera_yaw += yaw

    def set_zoom(self, zoom: float) -> None:
        """Set the zoom level with clamping."""
        self.zoom = max(self.min_zoom, min(self.max_zoom, zoom))

    def _draw_sphere_shell(self) -> None:
        """Render the base sphere shading."""
        center = (self.screen_width // 2, self.screen_height // 2)
        radius_px = int(self.radius * self.zoom)
        pygame.draw.circle(self.screen, self.sphere_color, center, radius_px)
        rim_radius = max(1, int(radius_px * 0.94))
        pygame.draw.circle(
            self.screen,
            self.sphere_highlight,
            center,
            rim_radius,
            max(1, int(2 * self.zoom)),
        )

    def _draw_lat_lon_grid(self) -> None:
        """Overlay a simple latitude/longitude grid for spatial cues."""
        latitudes = [-60, -30, 0, 30, 60]
        longitudes = list(range(-150, 180, 30))
        step = 6
        line_width = max(1, int(2 * self.zoom))

        for lat in latitudes:
            samples = []
            for lon in range(-180, 181, step):
                projected = self.project_with_depth(lat, lon)
                if projected is None:
                    continue
                samples.append(projected[0])
            if len(samples) >= 2:
                pygame.draw.lines(self.screen, self.grid_color, False, samples, line_width)

        for lon in longitudes:
            samples = []
            for lat in range(-90, 91, step):
                projected = self.project_with_depth(lat, lon)
                if projected is None:
                    continue
                samples.append(projected[0])
            if len(samples) >= 2:
                pygame.draw.lines(self.screen, self.grid_color, False, samples, line_width)

    @staticmethod
    def _build_ribbon(
        points: list[tuple[float, float]], widths: list[float]
    ) -> list[tuple[int, int]]:
        """Create a screen-space ribbon polygon given centerline points and widths."""
        if len(points) < 2:
            x, y = points[0]
            return [(int(x), int(y))] * 4

        left: list[tuple[int, int]] = []
        right: list[tuple[int, int]] = []

        for idx, (x, y) in enumerate(points):
            if idx == 0:
                dx = points[idx + 1][0] - x
                dy = points[idx + 1][1] - y
            elif idx == len(points) - 1:
                dx = x - points[idx - 1][0]
                dy = y - points[idx - 1][1]
            else:
                dx = points[idx + 1][0] - points[idx - 1][0]
                dy = points[idx + 1][1] - points[idx - 1][1]

            length = math.hypot(dx, dy) or 1.0
            nx = -dy / length
            ny = dx / length
            w = widths[idx]

            left.append((int(x + nx * w), int(y + ny * w)))
            right.append((int(x - nx * w), int(y - ny * w)))

        return left + right[::-1]

    def render(
        self, graph: "MazeGraph", dot: "DotEntity | None" = None, show_all_nodes: bool = True
    ) -> None:
        """Render the maze graph and optional dot entity."""
        self.screen.fill(self.bg_color)
        self._draw_sphere_shell()
        self._draw_lat_lon_grid()

        edge_segments: list[tuple[float, list[tuple[float, float]], list[float]]] = []
        for edge in graph.edges.values():
            if edge.blocked:
                continue

            node_a = graph.nodes.get(edge.node_a)
            node_b = graph.nodes.get(edge.node_b)
            if node_a is None or node_b is None:
                continue

            path_source = edge.path_points or [
                (node_a.latitude, node_a.longitude),
                (node_b.latitude, node_b.longitude),
            ]

            projected_path: list[tuple[float, float]] = []
            depths: list[float] = []

            for lat, lon in path_source:
                projected = self.project_with_depth(lat, lon)
                if projected is None:
                    continue
                (px, py), depth = projected
                projected_path.append((float(px), float(py)))
                depths.append(depth)

            if len(projected_path) >= 2:
                avg_depth = sum(depths) / len(depths)
                edge_segments.append((avg_depth, projected_path, depths))

        edge_segments.sort(key=lambda item: item[0])

        base_width = 5.0 * self.zoom
        outer_bonus = 4.0 * self.zoom

        for _, path_points, depths in edge_segments:
            if len(path_points) < 2:
                continue

            widths: list[float] = []
            for depth in depths:
                depth_factor = 0.6 + depth / max(1.0, self.radius * 1.2)
                widths.append(max(2.0, base_width * depth_factor))

            outer = self._build_ribbon(path_points, [w + outer_bonus for w in widths])
            body = self._build_ribbon(path_points, widths)
            walkway = self._build_ribbon(path_points, [max(1.0, w * 0.45) for w in widths])

            pygame.draw.polygon(self.screen, self.wall_shadow_color, outer)
            pygame.draw.polygon(self.screen, self.wall_color, body)
            pygame.draw.polygon(self.screen, self.path_color, walkway)
            center = [(int(x), int(y)) for x, y in path_points]
            pygame.draw.lines(
                self.screen,
                self.wall_rim_color,
                False,
                center,
                max(1, int(self.zoom * 1.5)),
            )
            pygame.draw.lines(
                self.screen,
                self.path_highlight,
                False,
                center,
                max(1, int(self.zoom)),
            )

        visible_nodes: list[tuple["MazeNode", tuple[tuple[int, int], float]]] = []
        for node in graph.nodes.values():
            projected = self.project_with_depth(node.latitude, node.longitude)
            if projected is None:
                continue
            visible_nodes.append((node, projected))

        if show_all_nodes:
            for node, (screen_pos, depth) in visible_nodes:
                size = max(4, int(6 * self.zoom * (1 + depth / (self.radius * 1.5))))
                color = (150, 255, 150) if node.visited else self.node_color
                pygame.draw.circle(self.screen, self.wall_shadow_color, screen_pos, size + 2)
                pygame.draw.circle(self.screen, color, screen_pos, size)

        if dot is not None:
            projected = self.project_with_depth(dot.latitude, dot.longitude)
            if projected is not None:
                dot_pos, depth = projected
                size = max(6, int(8 * self.zoom * (1 + depth / (self.radius * 1.5))))
                pygame.draw.circle(self.screen, self.wall_shadow_color, dot_pos, size + 3)
                pygame.draw.circle(self.screen, self.dot_color, dot_pos, size)

        pygame.display.flip()

    def get_view_matrix(self) -> np.ndarray:
        """Get the current view transformation matrix."""
        pitch_rad = math.radians(self.camera_pitch)
        yaw_rad = math.radians(self.camera_yaw)

        pitch_matrix = np.array(
            [
                [math.cos(pitch_rad), 0, math.sin(pitch_rad)],
                [0, 1, 0],
                [-math.sin(pitch_rad), 0, math.cos(pitch_rad)],
            ]
        )

        yaw_matrix = np.array(
            [
                [math.cos(yaw_rad), -math.sin(yaw_rad), 0],
                [math.sin(yaw_rad), math.cos(yaw_rad), 0],
                [0, 0, 1],
            ]
        )

        return np.dot(yaw_matrix, pitch_matrix)

    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()
