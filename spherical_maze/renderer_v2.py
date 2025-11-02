"""V2: First-person spherical maze renderer with 3D walls."""

import math
from typing import TYPE_CHECKING

import numpy as np
import pygame

if TYPE_CHECKING:
    from spherical_maze.maze_graph import MazeGraph
    from spherical_maze.navigation import DotEntity


class FirstPersonRenderer:
    """Renders the maze from a first-person perspective inside the sphere."""

    def __init__(self, radius: float, screen_size: tuple[int, int]) -> None:
        """Initialize the first-person renderer."""
        self.radius = radius
        self.screen_width, self.screen_height = screen_size

        # V2: First-person camera settings
        self.fov = 90.0  # Field of view in degrees
        self.wall_height = 8.0  # Height of maze walls
        self.path_width = 3.0  # Width of paths (for wall generation)
        self.render_distance = 100.0  # Maximum render distance

        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Spherical Maze - First Person")

        # Colors
        self.bg_color = (10, 10, 30)
        self.floor_color = (60, 80, 100)
        self.wall_color = (120, 140, 160)
        self.wall_dark_color = (80, 90, 100)
        self.ceiling_color = (20, 20, 40)

    def spherical_to_cartesian(
        self, latitude: float, longitude: float, radius: float | None = None
    ) -> tuple[float, float, float]:
        """Convert spherical coordinates to 3D Cartesian coordinates."""
        if radius is None:
            radius = self.radius

        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)

        x = radius * math.cos(lat_rad) * math.cos(lon_rad)
        y = radius * math.cos(lat_rad) * math.sin(lon_rad)
        z = radius * math.sin(lat_rad)

        return x, y, z

    def get_camera_position(self, player: "DotEntity") -> tuple[float, float, float]:
        """Calculate camera position from player position."""
        # Player position is on the sphere surface, camera is slightly above
        camera_radius = self.radius + player.height
        return self.spherical_to_cartesian(player.latitude, player.longitude, camera_radius)

    def get_view_matrix(self, player: "DotEntity") -> np.ndarray:
        """Calculate view matrix based on player position and orientation."""
        # Camera position
        cam_x, cam_y, cam_z = self.get_camera_position(player)

        # Calculate view direction from yaw and pitch
        yaw_rad = math.radians(player.yaw)
        pitch_rad = math.radians(player.pitch)

        # Forward vector (where camera is looking)
        forward_x = math.cos(pitch_rad) * math.cos(yaw_rad)
        forward_y = math.cos(pitch_rad) * math.sin(yaw_rad)
        forward_z = math.sin(pitch_rad)

        # Target point (where we're looking at)
        target_x = cam_x + forward_x
        target_y = cam_y + forward_y
        target_z = cam_z + forward_z

        # Up vector (world up, toward sphere center from camera)
        up_x, up_y, up_z = -cam_x, -cam_y, -cam_z
        up_length = math.sqrt(up_x**2 + up_y**2 + up_z**2)
        if up_length > 0:
            up_x /= up_length
            up_y /= up_length
            up_z /= up_length

        # Create view matrix using lookAt logic
        # Forward direction (normalized)
        f_x = target_x - cam_x
        f_y = target_y - cam_y
        f_z = target_z - cam_z
        f_length = math.sqrt(f_x**2 + f_y**2 + f_z**2)
        if f_length > 0:
            f_x /= f_length
            f_y /= f_length
            f_z /= f_length

        # Right vector (cross product of forward and up)
        r_x = f_y * up_z - f_z * up_y
        r_y = f_z * up_x - f_x * up_z
        r_z = f_x * up_y - f_y * up_x
        r_length = math.sqrt(r_x**2 + r_y**2 + r_z**2)
        if r_length > 0:
            r_x /= r_length
            r_y /= r_length
            r_z /= r_length

        # Recalculate up vector (cross product of right and forward)
        u_x = r_y * f_z - r_z * f_y
        u_y = r_z * f_x - r_x * f_z
        u_z = r_x * f_y - r_y * f_x

        # Build view matrix
        view_matrix = np.array(
            [
                [r_x, r_y, r_z, -(r_x * cam_x + r_y * cam_y + r_z * cam_z)],
                [u_x, u_y, u_z, -(u_x * cam_x + u_y * cam_y + u_z * cam_z)],
                [-f_x, -f_y, -f_z, -(-f_x * cam_x + -f_y * cam_y + -f_z * cam_z)],
                [0, 0, 0, 1],
            ]
        )

        return view_matrix

    def project_to_screen(
        self, x: float, y: float, z: float, view_matrix: np.ndarray
    ) -> tuple[int, int, float] | None:
        """Project 3D world coordinates to 2D screen using perspective projection."""
        # Apply view matrix
        world_pos = np.array([x, y, z, 1.0])
        view_pos = view_matrix @ world_pos

        # Check if point is behind camera
        depth = -view_pos[2]
        if depth <= 0.1:
            return None

        # Perspective projection
        fov_rad = math.radians(self.fov)
        scale = (self.screen_height / 2) / math.tan(fov_rad / 2)

        screen_x = int(self.screen_width / 2 + (view_pos[0] / depth) * scale)
        screen_y = int(self.screen_height / 2 - (view_pos[1] / depth) * scale)

        return screen_x, screen_y, depth

    def render_wall_segment(
        self,
        p1_lat: float,
        p1_lon: float,
        p2_lat: float,
        p2_lon: float,
        view_matrix: np.ndarray,
    ) -> None:
        """Render a 3D wall segment between two points."""
        # Calculate floor points (on sphere surface)
        floor1 = self.spherical_to_cartesian(p1_lat, p1_lon)
        floor2 = self.spherical_to_cartesian(p2_lat, p2_lon)

        # Calculate top points (elevated above surface)
        top1 = self.spherical_to_cartesian(p1_lat, p1_lon, self.radius + self.wall_height)
        top2 = self.spherical_to_cartesian(p2_lat, p2_lon, self.radius + self.wall_height)

        # Calculate perpendicular offset for wall width
        # Direction vector
        dx = floor2[0] - floor1[0]
        dy = floor2[1] - floor1[1]
        dz = floor2[2] - floor1[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)

        if length < 0.01:
            return

        # Normalize
        dx /= length
        dy /= length
        dz /= length

        # Get perpendicular vectors for wall sides
        # Use cross product with up vector (radial direction)
        up_x, up_y, up_z = floor1[0], floor1[1], floor1[2]
        up_length = math.sqrt(up_x**2 + up_y**2 + up_z**2)
        up_x /= up_length
        up_y /= up_length
        up_z /= up_length

        # Right vector (perpendicular to path)
        right_x = dy * up_z - dz * up_y
        right_y = dz * up_x - dx * up_z
        right_z = dx * up_y - dy * up_x
        right_length = math.sqrt(right_x**2 + right_y**2 + right_z**2)
        if right_length > 0:
            right_x /= right_length
            right_y /= right_length
            right_z /= right_length

        # Calculate wall edge points
        hw = self.path_width / 2  # Half width

        # Left edge points
        left_floor1 = (floor1[0] - right_x * hw, floor1[1] - right_y * hw, floor1[2] - right_z * hw)
        left_floor2 = (floor2[0] - right_x * hw, floor2[1] - right_y * hw, floor2[2] - right_z * hw)
        left_top1 = (top1[0] - right_x * hw, top1[1] - right_y * hw, top1[2] - right_z * hw)
        left_top2 = (top2[0] - right_x * hw, top2[1] - right_y * hw, top2[2] - right_z * hw)

        # Right edge points
        right_floor1 = (
            floor1[0] + right_x * hw,
            floor1[1] + right_y * hw,
            floor1[2] + right_z * hw,
        )
        right_floor2 = (
            floor2[0] + right_x * hw,
            floor2[1] + right_y * hw,
            floor2[2] + right_z * hw,
        )
        right_top1 = (top1[0] + right_x * hw, top1[1] + right_y * hw, top1[2] + right_z * hw)
        right_top2 = (top2[0] + right_x * hw, top2[1] + right_y * hw, top2[2] + right_z * hw)

        # Draw left wall
        self._draw_quad(
            left_floor1, left_floor2, left_top2, left_top1, view_matrix, self.wall_color
        )

        # Draw right wall
        self._draw_quad(
            right_floor1, right_floor2, right_top2, right_top1, view_matrix, self.wall_color
        )

        # Draw floor (path)
        self._draw_quad(
            left_floor1, right_floor1, right_floor2, left_floor2, view_matrix, self.floor_color
        )

    def _draw_quad(
        self,
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        p3: tuple[float, float, float],
        p4: tuple[float, float, float],
        view_matrix: np.ndarray,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a 3D quad (4-sided polygon)."""
        # Project all points
        proj1 = self.project_to_screen(*p1, view_matrix)
        proj2 = self.project_to_screen(*p2, view_matrix)
        proj3 = self.project_to_screen(*p3, view_matrix)
        proj4 = self.project_to_screen(*p4, view_matrix)

        # Check if all points are visible
        if not all([proj1, proj2, proj3, proj4]):
            return

        # Calculate average depth for sorting
        avg_depth = (proj1[2] + proj2[2] + proj3[2] + proj4[2]) / 4

        # Draw the quad
        points = [
            (proj1[0], proj1[1]),
            (proj2[0], proj2[1]),
            (proj3[0], proj3[1]),
            (proj4[0], proj4[1]),
        ]

        try:
            # Shade based on depth
            depth_factor = max(0.3, min(1.0, 50.0 / avg_depth))
            shaded_color = (
                int(color[0] * depth_factor),
                int(color[1] * depth_factor),
                int(color[2] * depth_factor),
            )
            pygame.draw.polygon(self.screen, shaded_color, points)
        except (ValueError, OverflowError):
            pass

    def render(self, graph: "MazeGraph", player: "DotEntity") -> None:
        """Render the maze from first-person perspective."""
        self.screen.fill(self.bg_color)

        if player is None:
            pygame.display.flip()
            return

        # Calculate view matrix
        view_matrix = self.get_view_matrix(player)

        # Draw ceiling
        mid_y = self.screen_height // 2
        pygame.draw.rect(self.screen, self.ceiling_color, (0, 0, self.screen_width, mid_y))

        # Draw floor with gradient for depth perception
        floor_dark = (30, 40, 50)
        for y in range(mid_y, self.screen_height):
            factor = (y - mid_y) / (self.screen_height - mid_y)
            color = (
                int(self.floor_color[0] * (1 - factor) + floor_dark[0] * factor),
                int(self.floor_color[1] * (1 - factor) + floor_dark[1] * factor),
                int(self.floor_color[2] * (1 - factor) + floor_dark[2] * factor),
            )
            pygame.draw.line(self.screen, color, (0, y), (self.screen_width, y))

        # Render all edges as 3D wall segments
        for edge in graph.edges.values():
            if edge.blocked:
                continue

            node_a = graph.nodes.get(edge.node_a)
            node_b = graph.nodes.get(edge.node_b)

            if node_a is None or node_b is None:
                continue

            # Render the wall segment
            self.render_wall_segment(
                node_a.latitude,
                node_a.longitude,
                node_b.latitude,
                node_b.longitude,
                view_matrix,
            )

        pygame.display.flip()

    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()
