"""Navigation and pathfinding system for the maze."""

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable
from uuid import UUID

if TYPE_CHECKING:
    from spherical_maze.maze_graph import MazeGraph


@dataclass
class DotEntity:
    """Represents the player/dot entity navigating the maze."""

    latitude: float
    longitude: float
    speed: float = 1.0
    target_node: UUID | None = None
    path_queue: list[UUID] = field(default_factory=list)
    current_path_index: int = 0

    # V2: First-person view properties
    yaw: float = 0.0  # Horizontal rotation (left/right)
    pitch: float = 0.0  # Vertical rotation (up/down)
    height: float = 5.0  # Height above sphere surface
    last_reached_node: UUID | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_position(cls, latitude: float, longitude: float, speed: float = 1.0) -> "DotEntity":
        """Create a dot entity at a specific position."""
        return cls(latitude=latitude, longitude=longitude, speed=speed)

    def move_by(self, forward: float, strafe: float, delta_time: float) -> None:
        """Move the dot manually based on yaw direction (V2 first-person control).

        Args:
            forward: Forward/backward movement (-1 to 1)
            strafe: Left/right strafing (-1 to 1)
            delta_time: Time since last frame
        """
        if forward == 0.0 and strafe == 0.0:
            return

        # Calculate movement speed
        move_distance = self.speed * delta_time

        # Convert yaw to radians for calculation
        yaw_rad = math.radians(self.yaw)

        # Calculate movement vectors based on yaw
        # Forward direction aligned with yaw
        forward_lat = forward * move_distance * math.cos(yaw_rad)
        forward_lon = forward * move_distance * math.sin(yaw_rad)

        # Strafe direction perpendicular to yaw
        strafe_lat = strafe * move_distance * math.sin(yaw_rad)
        strafe_lon = -strafe * move_distance * math.cos(yaw_rad)

        # Apply movement
        self.latitude += forward_lat + strafe_lat
        self.longitude += forward_lon + strafe_lon

        # Clamp latitude to valid range
        self.latitude = max(-90.0, min(90.0, self.latitude))

        # Wrap longitude
        if self.longitude > 180.0:
            self.longitude -= 360.0
        elif self.longitude < -180.0:
            self.longitude += 360.0

    def rotate_view(self, delta_yaw: float, delta_pitch: float) -> None:
        """Rotate the player's view (V2 mouse look).

        Args:
            delta_yaw: Change in horizontal rotation
            delta_pitch: Change in vertical rotation
        """
        self.yaw += delta_yaw
        self.pitch += delta_pitch

        # Wrap yaw to 0-360 range
        self.yaw = self.yaw % 360.0

        # Clamp pitch to prevent over-rotation
        self.pitch = max(-89.0, min(89.0, self.pitch))

    def set_path(self, path: list[UUID]) -> None:
        """Set the path for the dot to follow."""
        self.path_queue = path.copy()
        self.current_path_index = 0
        if path:
            self.target_node = path[0]

    def update(self, delta_time: float, graph: "MazeGraph") -> bool:
        """Update dot position along path. Returns True if reached destination."""
        self.last_reached_node = None

        if not self.path_queue or self.current_path_index >= len(self.path_queue):
            return True

        target_id = self.path_queue[self.current_path_index]
        if target_id not in graph.nodes:
            return True

        target = graph.nodes[target_id]

        distance = self._calculate_distance(
            self.latitude, self.longitude, target.latitude, target.longitude
        )

        if distance < 0.5:
            self.latitude = target.latitude
            self.longitude = target.longitude
            target.visited = True
            self.last_reached_node = target_id

            self.current_path_index += 1
            if self.current_path_index >= len(self.path_queue):
                return True

            self.target_node = self.path_queue[self.current_path_index]
            return False

        move_distance = self.speed * delta_time
        if move_distance >= distance:
            self.latitude = target.latitude
            self.longitude = target.longitude
        else:
            ratio = move_distance / distance
            self.latitude += (target.latitude - self.latitude) * ratio
            self.longitude += (target.longitude - self.longitude) * ratio

            if self.longitude > 180:
                self.longitude -= 360
            elif self.longitude < -180:
                self.longitude += 360

        return False

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance between two points."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)

        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return math.degrees(c) * 111.0


class PathFollower:
    """Manages path following behavior for dot entity."""

    def __init__(self, dot: DotEntity, graph: "MazeGraph") -> None:
        """Initialize path follower."""
        self.dot = dot
        self.graph = graph
        self.is_following = False
        self.completed = False
        self.waypoint_callback: Callable[[UUID], None] | None = None

    def start_following(self, path: list[UUID]) -> None:
        """Start following a path."""
        self.dot.set_path(path)
        self.is_following = True
        self.completed = False

    def set_waypoint_callback(self, callback: Callable[[UUID], None] | None) -> None:
        """Register a callback invoked whenever the dot reaches a waypoint."""
        self.waypoint_callback = callback

    def update(self, delta_time: float) -> None:
        """Update path following."""
        if not self.is_following or self.completed:
            return

        reached = self.dot.update(delta_time, self.graph)

        if self.dot.last_reached_node is not None and self.waypoint_callback is not None:
            self.waypoint_callback(self.dot.last_reached_node)

        if reached:
            self.completed = True
            self.is_following = False

    def is_complete(self) -> bool:
        """Check if path following is complete."""
        return self.completed

    def stop(self) -> None:
        """Stop following the current path."""
        self.is_following = False
        self.dot.path_queue.clear()
