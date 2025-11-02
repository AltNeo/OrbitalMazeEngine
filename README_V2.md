# Spherical Maze V2 - First-Person Explorer

## 🎮 What's New in V2?

V2 transforms the spherical maze from a **top-down globe viewer** into an **immersive first-person maze explorer**!

### V1 → V2 Comparison

| Feature | V1 (Top-Down) | V2 (First-Person) |
|---------|---------------|-------------------|
| **Perspective** | Orthographic view of entire sphere | Inside the maze, first-person view |
| **Camera** | Rotates around the globe | You ARE the camera |
| **Walls** | 2D lines on sphere surface | 3D extruded walls with height |
| **Controls** | WASD rotates globe | WASD moves player, Mouse looks |
| **Experience** | Strategic map view | Immersive maze exploration |

## 🚀 Quick Start

### Installation
```bash
cd E:\Spherical_Maze
pip install -e ".[dev]"
```

### Run V2 (First-Person)
```bash
python main_v2.py
```

### Run V1 (Top-Down) - Still Available
```bash
python main.py
```

## 🎯 V2 Controls

### Movement
- **W** - Move forward
- **S** - Move backward
- **A** - Strafe left
- **D** - Strafe right

### View Control
- **Mouse** - Look around (when grabbed)
- **TAB** or **ESC** - Toggle mouse grab/release

### Game Commands
- **G** - Generate new maze
- **R** - Reset maze
- **S** - Save game (saves position AND view direction)
- **L** - Load game
- **F3** - Toggle debug info
- **ESC** - Exit (when mouse is free)

## 🏗️ Architecture Changes

### New Components

#### 1. FirstPersonRenderer (`renderer_v2.py`)
Replaces `SphereRenderer` with true 3D perspective:

```python
# V1: Orthographic projection
screen_x = center_x + x * zoom

# V2: Perspective projection with depth
scale = fov / depth
screen_x = center_x + (x / depth) * scale
```

**Key Features:**
- View matrix calculation from player position
- Perspective projection with field of view
- 3D wall extrusion with height
- Depth-based shading
- Back-face culling

#### 2. Enhanced DotEntity (`navigation.py`)
New first-person properties and methods:

```python
@dataclass
class DotEntity:
    # ... existing fields ...
    
    # V2 additions
    yaw: float = 0.0      # Horizontal rotation
    pitch: float = 0.0    # Vertical rotation  
    height: float = 5.0   # Height above surface
    
    def move_by(forward, strafe, delta_time)  # Manual movement
    def rotate_view(delta_yaw, delta_pitch)   # Mouse look
```

#### 3. FirstPersonMazeGame (`game_v2.py`)
Complete rewrite of game loop:

- **Mouse capture** for first-person look
- **Continuous WASD** movement (not event-based)
- **View direction** tied to player yaw/pitch
- **Camera position** calculated from player position

### Rendering Pipeline

```
V1: World → Globe Rotation → 2D Projection → Screen
V2: World → View Matrix (from player) → 3D Perspective → Screen
```

## 🎨 Visual Features

### 3D Walls
Paths are now corridors with:
- **Floor** - Walkable path surface
- **Left Wall** - 3D extruded polygon
- **Right Wall** - 3D extruded polygon
- **Height** - Configurable wall height (default: 8.0 units)

### Perspective Depth
- Distant objects appear smaller
- Depth-based color shading
- Creates "corridor" feeling from target image

### Camera System
- Position: On sphere surface + height offset
- Up Vector: Points away from sphere center
- Forward Vector: Based on yaw and pitch
- True first-person "lookAt" view matrix

## 🔧 Configuration

Edit `game_v2.py` to customize:

```python
# Renderer settings
FirstPersonRenderer(
    radius=150.0,           # Sphere radius
    screen_size=(1024, 768) # Window size
)

# In FirstPersonRenderer.__init__:
self.fov = 90.0            # Field of view (degrees)
self.wall_height = 8.0     # Wall height
self.path_width = 3.0      # Corridor width

# In FirstPersonMazeGame.__init__:
self.mouse_sensitivity = 0.2  # Mouse look speed
self.move_speed = 10.0        # Movement speed
```

## 📊 Technical Details

### View Matrix Calculation
Uses "lookAt" algorithm:
1. Calculate camera position from player lat/lon + height
2. Calculate forward vector from yaw/pitch
3. Calculate right vector (cross product)
4. Calculate up vector (perpendicular to sphere)
5. Build 4x4 view transformation matrix

### Wall Extrusion
For each edge (path segment):
1. Get floor centerline points on sphere
2. Calculate perpendicular "right" vector
3. Offset left/right by path_width/2
4. Create top points at floor + wall_height
5. Draw quads: left wall, right wall, floor

### Perspective Projection
```python
# After view transform:
depth = -view_pos[2]
scale = (screen_height / 2) / tan(fov / 2)
screen_x = center_x + (view_pos[0] / depth) * scale
screen_y = center_y - (view_pos[1] / depth) * scale
```

## 🧪 Testing

V2 includes updated tests for new functionality:

```bash
# Run all tests
pytest

# Run V2-specific tests
pytest tests/test_navigation.py -k "yaw or pitch or move_by"
```

## 🎯 Design Goals Achieved

✅ **First-person perspective** - Camera IS the player  
✅ **3D extruded walls** - True corridors with height  
✅ **Mouse look** - Smooth view control  
✅ **WASD movement** - Intuitive FPS controls  
✅ **Perspective projection** - Depth perception  
✅ **Immersive experience** - Exploring from inside  

## 🔄 Backward Compatibility

V1 remains fully functional:
- `main.py` - V1 top-down game
- `game.py` - V1 game engine
- `renderer.py` - V1 orthographic renderer

V2 adds new files without breaking V1:
- `main_v2.py` - V2 first-person game
- `game_v2.py` - V2 game engine
- `renderer_v2.py` - V2 perspective renderer

## 🚧 Known Limitations

1. **Collision Detection**: Currently disabled for free movement
2. **Wall Rendering**: Simple quads (no textures yet)
3. **Performance**: May drop FPS with 1000+ edges
4. **Maze Density**: Works best with medium-complexity mazes

## 🎮 Recommended Settings

For best experience:

```python
# Generate mazes with:
complexity="medium"  # Not too dense
pattern="grid"       # Clear corridors
```

## 📈 Future Enhancements

- [ ] Collision detection with maze walls
- [ ] Textured walls and floors
- [ ] Minimap overlay
- [ ] Jump/crouch mechanics
- [ ] Lighting and shadows
- [ ] Particle effects
- [ ] Multi-player support

## 🎉 Try It Now!

```bash
python main_v2.py
```

Press **G** to generate a maze, then use **WASD** and **Mouse** to explore!

**Welcome to the inside of the spherical maze!** 🌍🎮
