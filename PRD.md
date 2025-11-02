<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Product Requirements Document (PRD)

## AI-Powered Spherical Maze Game with Persistent Cyclic Tree Structure


***

## 1. Executive Summary

A Python-based game built with Pygame featuring a spherical world canvas where an OpenAI-compatible AI dynamically generates mazes based on user prompts. The game uses a cyclic tree data structure to maintain persistent maze routes, allowing a dot to navigate from start to end points while the maze expands organically during exploration.[^1][^2][^3]

***

## 2. Product Vision

Create an innovative maze exploration game that combines AI creativity with persistent world-building, offering infinite replayability through procedural AI-driven generation on a unique spherical topology.

***

## 3. Technical Architecture

### 3.1 Core Components

**Component 1: Spherical Canvas Renderer (Pygame-based)**

- 2D projection of 3D spherical coordinates using orthographic or stereographic projection[^4][^5]
- UV mapping for texture coordinates on sphere surface[^6]
- Camera system for rotation and zoom
- Anti-aliasing for smooth path rendering[^7]

**Component 2: Cyclic Tree Data Structure**

- Graph-based representation allowing cycles and branches[^1]
- Node: Contains position (lat, lon), connections, metadata
- Edge: Contains path geometry, traversal cost, generation timestamp
- Supports detection of cycles using DFS/BFS algorithms[^3]

**Component 3: AI Maze Generator Interface**

- OpenAI API integration for prompt-based generation[^2][^8]
- Prompt engineering module for maze descriptions
- Parser to convert AI output to graph structure
- Fallback procedural generation for API failures

**Component 4: Navigation \& Physics**

- Path-following algorithm for dot movement
- Collision detection with maze walls
- Smooth interpolation between waypoints
- Input handling for player control

**Component 5: Persistence Layer**

- JSON/Pickle serialization of cyclic tree
- Save/load game states
- Versioning for backward compatibility

***

## 4. Detailed Feature Specifications

### 4.1 Spherical World Rendering

**Requirements:**

- Render sphere with configurable radius and resolution
- Support for 360° rotation (pitch, yaw)
- Zoom levels: 0.5x to 5x
- Frame rate: Minimum 30 FPS with 10,000+ nodes

**Technical Approach (Pygame):**
Since Pygame doesn't natively support 3D, implement a software renderer that:

1. Projects 3D sphere coordinates to 2D screen space using matrix transformations[^5][^4]
2. Calculates spherical coordinates (latitude, longitude) for each maze node
3. Converts to Cartesian coordinates: `x = r * cos(lat) * cos(lon)`, `y = r * cos(lat) * sin(lon)`, `z = r * sin(lat)`[^6]
4. Applies camera transformation matrix
5. Projects to screen using perspective or orthographic projection
6. Renders paths as connected line segments using `pygame.draw.lines()`[^7]

**Rendering Pipeline:**

```
Maze Graph → Spherical Coords → 3D Cartesian → Camera Transform → 2D Projection → Pygame Surface
```


### 4.2 Cyclic Tree Data Structure

**Node Structure:**

```python
class MazeNode:
    id: UUID
    latitude: float  # -90 to 90 degrees
    longitude: float  # -180 to 180 degrees
    connections: List[UUID]  # Adjacent node IDs
    generation_prompt: str  # Prompt that created this node
    visited: bool
    metadata: Dict[str, Any]
```

**Edge Structure:**

```python
class MazeEdge:
    id: UUID
    node_a: UUID
    node_b: UUID
    path_points: List[Tuple[float, float]]  # Intermediate points
    traversal_cost: float
    blocked: bool
    generation_timestamp: datetime
```

**Graph Operations:**

- Add node/edge with cycle detection[^3]
- Find shortest path (Dijkstra's algorithm)
- Detect connected components
- Merge overlapping paths
- Prune unreachable nodes


### 4.3 AI Maze Generation

**Prompt Engineering:**

```
System: You are a maze designer. Generate maze connections on a sphere.
User: Create a [complexity] maze with [style] paths starting from node [id]
AI Response: Parse to extract node positions and connections
```

**Generation Modes:**

1. **Initial Generation**: Create starting maze from single prompt
2. **Expansion Generation**: Add new branches from current player position
3. **Refinement Generation**: Fill gaps or add shortcuts

**Parser Requirements:**

- Extract coordinate pairs from AI text responses
- Identify connection relationships
- Handle ambiguous or invalid outputs gracefully
- Validate generated paths don't intersect existing geometry


### 4.4 Navigation System

**Dot Entity:**

- Position: Current (lat, lon) on sphere
- Velocity: Speed along path
- Target: Next waypoint node
- Path: Queue of nodes to traverse

**Movement Modes:**

1. **Manual Control**: Arrow keys/WASD for direction selection at intersections
2. **Auto-pathfinding**: A* algorithm to find shortest route to destination
3. **Exploration Mode**: Random walk with bias toward unvisited areas

**Physics:**

- Constant speed movement along geodesic paths
- Smooth acceleration/deceleration at nodes
- Gravity simulation (optional): Pull toward sphere center

***

## 5. Implementation Considerations

### 5.1 Pygame-Specific Considerations

**Rendering Performance:**

- Use `pygame.Surface` for double-buffering to prevent flicker[^7]
- Implement spatial partitioning (octree/quadtree) for frustum culling
- Only render visible hemisphere based on camera angle
- Cache projected coordinates between frames when camera is static
- Use `pygame.draw` primitives efficiently; batch draw calls

**Resolution \& Scaling:**

- Support multiple window resolutions (800x600 to 1920x1080)
- Scale UI elements proportionally
- Maintain aspect ratio during projection

**Input Handling:**

- Use `pygame.event.get()` for keyboard/mouse input
- Implement key repeat for smooth continuous movement
- Support mouse drag for camera rotation
- Scroll wheel for zoom control


### 5.2 Data Structure Considerations

**Cyclic Tree Challenges:**

- **Cycle Management**: Allow cycles but prevent infinite loops during traversal using visited sets[^3]
- **Memory Efficiency**: For large mazes (>100k nodes), use sparse representations
- **Spatial Indexing**: Implement k-d tree or R-tree for fast spatial queries (find nearby nodes)
- **Consistency**: Ensure bidirectional edges remain synchronized

**Serialization:**

- Use adjacency list format for space efficiency
- Compress saved files using gzip
- Implement incremental saves (only save changes)
- Version metadata for future compatibility


### 5.3 AI Integration Considerations

**API Management:**

- Rate limiting: Max 60 requests/minute for OpenAI API[^2]
- Caching: Store AI responses to reduce costs
- Timeout handling: 30-second timeout for API calls
- Error handling: Retry logic with exponential backoff
- Cost monitoring: Track token usage and implement budgets

**Prompt Optimization:**

- Keep prompts under 500 tokens for faster responses
- Use few-shot examples in system prompt
- Implement prompt templates for consistency
- A/B test different prompt formats for quality

**Offline Mode:**

- Fallback to procedural generation if API unavailable
- Queue generation requests for later processing
- Cache recent AI responses for similar prompts


### 5.4 Performance Considerations

**Target Specifications:**

- Load time: <3 seconds for saved games with 50k nodes
- Frame rate: 60 FPS with 5k visible nodes, 30 FPS with 20k nodes
- Memory: <500MB RAM for typical game session
- AI response time: <5 seconds for maze generation

**Optimization Strategies:**

- Level of Detail (LOD): Render distant paths with fewer segments
- Occlusion culling: Don't render obscured paths
- Lazy loading: Generate maze chunks on-demand
- Threading: Run AI generation in separate thread
- Profiling: Use cProfile to identify bottlenecks


### 5.5 Mathematical Considerations

**Spherical Geometry:**

- Great circle distance for pathfinding: `d = r * arccos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1))`[^6]
- Handle longitude wraparound at ±180°
- Singularities at poles (lat = ±90°): Use alternate coordinate systems near poles

**Projection Artifacts:**

- Distortion increases away from projection center
- Implement multiple projection types: orthographic, stereographic, equirectangular
- Dynamic reprojection as camera moves

***

## 6. Testing Strategy

### 6.1 Unit Tests

**Module: Spherical Renderer (`test_renderer.py`)**

```python
import unittest
import pygame
from renderer import SphereRenderer, project_to_screen

class TestSphereRenderer(unittest.TestCase):
    
    def setUp(self):
        pygame.init()
        self.renderer = SphereRenderer(radius=100, screen_size=(800, 600))
    
    def test_spherical_to_cartesian_conversion(self):
        """Test conversion from lat/lon to 3D Cartesian coordinates"""
        # North pole
        x, y, z = self.renderer.spherical_to_cartesian(90, 0)
        self.assertAlmostEqual(x, 0, places=5)
        self.assertAlmostEqual(y, 0, places=5)
        self.assertAlmostEqual(z, 100, places=5)
        
        # Equator
        x, y, z = self.renderer.spherical_to_cartesian(0, 0)
        self.assertAlmostEqual(x, 100, places=5)
        self.assertAlmostEqual(y, 0, places=5)
        self.assertAlmostEqual(z, 0, places=5)
    
    def test_projection_within_screen_bounds(self):
        """Test that projected coordinates fall within screen bounds"""
        screen_x, screen_y = self.renderer.project_to_screen(45, 45)
        self.assertTrue(0 <= screen_x <= 800)
        self.assertTrue(0 <= screen_y <= 600)
    
    def test_back_face_culling(self):
        """Test that back-facing paths are not rendered"""
        # Point on back hemisphere
        is_visible = self.renderer.is_visible(-90, 0, camera_lat=90, camera_lon=0)
        self.assertFalse(is_visible)
    
    def test_camera_rotation(self):
        """Test camera rotation updates view correctly"""
        initial_view = self.renderer.get_view_matrix()
        self.renderer.rotate_camera(pitch=45, yaw=30)
        rotated_view = self.renderer.get_view_matrix()
        self.assertFalse(np.array_equal(initial_view, rotated_view))
    
    def test_zoom_limits(self):
        """Test zoom is clamped to valid range"""
        self.renderer.set_zoom(10.0)  # Above max
        self.assertEqual(self.renderer.zoom, 5.0)
        
        self.renderer.set_zoom(0.1)  # Below min
        self.assertEqual(self.renderer.zoom, 0.5)
    
    def tearDown(self):
        pygame.quit()
```

**Module: Cyclic Tree (`test_maze_graph.py`)**

```python
import unittest
from maze_graph import MazeGraph, MazeNode, MazeEdge

class TestMazeGraph(unittest.TestCase):
    
    def setUp(self):
        self.graph = MazeGraph()
        self.node1 = self.graph.add_node(latitude=0, longitude=0)
        self.node2 = self.graph.add_node(latitude=10, longitude=10)
        self.node3 = self.graph.add_node(latitude=20, longitude=20)
    
    def test_add_node(self):
        """Test adding nodes to graph"""
        node = self.graph.add_node(latitude=30, longitude=30)
        self.assertIsNotNone(node.id)
        self.assertEqual(node.latitude, 30)
        self.assertEqual(len(self.graph.nodes), 4)
    
    def test_add_edge(self):
        """Test adding edges between nodes"""
        edge = self.graph.add_edge(self.node1.id, self.node2.id)
        self.assertIn(self.node2.id, self.node1.connections)
        self.assertIn(self.node1.id, self.node2.connections)
    
    def test_cycle_detection(self):
        """Test cycle detection in graph"""
        self.graph.add_edge(self.node1.id, self.node2.id)
        self.graph.add_edge(self.node2.id, self.node3.id)
        self.graph.add_edge(self.node3.id, self.node1.id)  # Creates cycle
        
        has_cycle = self.graph.has_cycle()
        self.assertTrue(has_cycle)
    
    def test_shortest_path(self):
        """Test pathfinding algorithm"""
        self.graph.add_edge(self.node1.id, self.node2.id, cost=1.0)
        self.graph.add_edge(self.node2.id, self.node3.id, cost=1.0)
        self.graph.add_edge(self.node1.id, self.node3.id, cost=5.0)
        
        path = self.graph.shortest_path(self.node1.id, self.node3.id)
        self.assertEqual(path, [self.node1.id, self.node2.id, self.node3.id])
    
    def test_remove_node_updates_connections(self):
        """Test that removing node updates connected edges"""
        self.graph.add_edge(self.node1.id, self.node2.id)
        self.graph.remove_node(self.node2.id)
        
        self.assertNotIn(self.node2.id, self.node1.connections)
        self.assertEqual(len(self.graph.nodes), 2)
    
    def test_find_nearby_nodes(self):
        """Test spatial query for nearby nodes"""
        nearby = self.graph.find_nodes_in_radius(latitude=5, longitude=5, radius=10)
        self.assertIn(self.node1.id, [n.id for n in nearby])
        self.assertIn(self.node2.id, [n.id for n in nearby])
        self.assertNotIn(self.node3.id, [n.id for n in nearby])
    
    def test_serialize_deserialize(self):
        """Test graph serialization and deserialization"""
        self.graph.add_edge(self.node1.id, self.node2.id)
        serialized = self.graph.to_json()
        
        new_graph = MazeGraph.from_json(serialized)
        self.assertEqual(len(new_graph.nodes), len(self.graph.nodes))
        self.assertEqual(len(new_graph.edges), len(self.graph.edges))
```

**Module: AI Generator (`test_ai_generator.py`)**

```python
import unittest
from unittest.mock import patch, MagicMock
from ai_generator import AIMapGenerator

class TestAIMapGenerator(unittest.TestCase):
    
    def setUp(self):
        self.generator = AIMapGenerator(api_key="test_key")
    
    @patch('openai.ChatCompletion.create')
    def test_generate_maze_success(self, mock_openai):
        """Test successful maze generation from AI"""
        mock_response = MagicMock()
        mock_response.choices[^0].message.content = "Node at (10, 20) connects to (30, 40)"
        mock_openai.return_value = mock_response
        
        result = self.generator.generate_maze("Create a simple maze")
        self.assertIsNotNone(result)
        self.assertIn('nodes', result)
        self.assertIn('edges', result)
    
    @patch('openai.ChatCompletion.create')
    def test_generate_maze_api_timeout(self, mock_openai):
        """Test timeout handling"""
        mock_openai.side_effect = TimeoutError()
        
        result = self.generator.generate_maze("Create maze", timeout=1)
        self.assertIsNone(result)
    
    def test_parse_ai_response_valid(self):
        """Test parsing valid AI response"""
        response = "Node at (10, 20) connects to (15, 25) and (20, 30)"
        parsed = self.generator.parse_response(response)
        
        self.assertEqual(len(parsed['nodes']), 3)
        self.assertEqual(len(parsed['edges']), 2)
    
    def test_parse_ai_response_invalid(self):
        """Test parsing invalid AI response"""
        response = "Invalid response with no coordinates"
        parsed = self.generator.parse_response(response)
        
        self.assertEqual(len(parsed['nodes']), 0)
    
    def test_prompt_template_formatting(self):
        """Test prompt template uses correct format"""
        prompt = self.generator.create_prompt(
            start_node=(0, 0),
            complexity="medium",
            style="winding"
        )
        
        self.assertIn("medium", prompt)
        self.assertIn("winding", prompt)
        self.assertIn("0, 0", prompt)
    
    def test_rate_limiting(self):
        """Test rate limiting prevents excessive API calls"""
        for i in range(65):  # Exceed 60/minute limit
            if i < 60:
                self.assertTrue(self.generator.can_make_request())
            else:
                self.assertFalse(self.generator.can_make_request())
```

**Module: Navigation (`test_navigation.py`)**

```python
import unittest
from navigation import DotEntity, PathFollower
from maze_graph import MazeGraph

class TestNavigation(unittest.TestCase):
    
    def setUp(self):
        self.graph = MazeGraph()
        self.node1 = self.graph.add_node(0, 0)
        self.node2 = self.graph.add_node(10, 10)
        self.graph.add_edge(self.node1.id, self.node2.id)
        
        self.dot = DotEntity(start_position=(0, 0))
    
    def test_dot_initialization(self):
        """Test dot entity is created at start position"""
        self.assertEqual(self.dot.latitude, 0)
        self.assertEqual(self.dot.longitude, 0)
        self.assertEqual(self.dot.speed, 1.0)
    
    def test_dot_movement_along_path(self):
        """Test dot moves correctly along defined path"""
        path = [self.node1.id, self.node2.id]
        self.dot.set_path(path, self.graph)
        
        initial_pos = (self.dot.latitude, self.dot.longitude)
        self.dot.update(delta_time=0.1)
        
        # Should have moved toward target
        self.assertNotEqual((self.dot.latitude, self.dot.longitude), initial_pos)
    
    def test_dot_reaches_waypoint(self):
        """Test dot correctly identifies when waypoint is reached"""
        self.dot.target_node = self.node2
        self.dot.latitude = 9.9
        self.dot.longitude = 9.9
        
        reached = self.dot.check_waypoint_reached(threshold=0.5)
        self.assertTrue(reached)
    
    def test_path_following_completion(self):
        """Test path following completes when destination reached"""
        follower = PathFollower(self.dot, self.graph)
        path = [self.node1.id, self.node2.id]
        
        follower.start_following(path)
        
        # Simulate multiple updates until completion
        for _ in range(1000):
            if follower.is_complete():
                break
            follower.update(0.016)  # 60 FPS
        
        self.assertTrue(follower.is_complete())
    
    def test_collision_detection(self):
        """Test collision detection with maze boundaries"""
        # Try to move dot outside valid path
        self.dot.latitude = 5
        self.dot.longitude = 15  # Not on path
        
        collision = self.graph.check_collision(self.dot.latitude, self.dot.longitude)
        self.assertTrue(collision)
```

**Module: Persistence (`test_persistence.py`)**

```python
import unittest
import os
import tempfile
from persistence import SaveManager
from maze_graph import MazeGraph

class TestPersistence(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.save_manager = SaveManager(save_dir=self.temp_dir)
        
        self.graph = MazeGraph()
        self.graph.add_node(0, 0)
        self.graph.add_node(10, 10)
    
    def test_save_game(self):
        """Test saving game state to file"""
        save_path = self.save_manager.save_game(
            graph=self.graph,
            player_pos=(5, 5),
            metadata={"level": 1}
        )
        
        self.assertTrue(os.path.exists(save_path))
    
    def test_load_game(self):
        """Test loading game state from file"""
        save_path = self.save_manager.save_game(self.graph, (5, 5), {})
        
        loaded_data = self.save_manager.load_game(save_path)
        
        self.assertEqual(len(loaded_data['graph'].nodes), 2)
        self.assertEqual(loaded_data['player_pos'], (5, 5))
    
    def test_save_compression(self):
        """Test save files are compressed"""
        # Create large graph
        for i in range(1000):
            self.graph.add_node(i, i)
        
        save_path = self.save_manager.save_game(self.graph, (0, 0), {})
        
        file_size = os.path.getsize(save_path)
        # Compressed size should be less than uncompressed JSON
        self.assertLess(file_size, 100000)  # Arbitrary threshold
    
    def test_version_compatibility(self):
        """Test save format version is stored and checked"""
        save_path = self.save_manager.save_game(self.graph, (0, 0), {})
        
        with open(save_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn('version', data)
        self.assertEqual(data['version'], self.save_manager.CURRENT_VERSION)
    
    def test_auto_save(self):
        """Test auto-save functionality"""
        self.save_manager.enable_auto_save(interval=1.0)
        
        # Simulate game time passing
        time.sleep(1.5)
        self.save_manager.update(self.graph, (10, 10), {})
        
        auto_saves = self.save_manager.list_auto_saves()
        self.assertGreater(len(auto_saves), 0)
    
    def tearDown(self):
        # Clean up temp files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
```


### 6.2 Integration Tests

**Test: End-to-End Maze Generation and Navigation**

```python
def test_full_game_cycle(self):
    """Test complete game flow from generation to navigation"""
    # 1. Initialize systems
    renderer = SphereRenderer(100, (800, 600))
    graph = MazeGraph()
    ai_gen = AIMapGenerator(api_key=os.getenv('OPENAI_API_KEY'))
    
    # 2. Generate initial maze
    prompt = "Create a medium complexity spiral maze"
    maze_data = ai_gen.generate_maze(prompt)
    graph.import_from_dict(maze_data)
    
    # 3. Place dot at start
    start_node = graph.get_node_by_position(0, 0)
    dot = DotEntity(start_position=(start_node.latitude, start_node.longitude))
    
    # 4. Find path to arbitrary end
    end_node = graph.nodes[len(graph.nodes) // 2]
    path = graph.shortest_path(start_node.id, end_node.id)
    
    # 5. Simulate navigation
    follower = PathFollower(dot, graph)
    follower.start_following(path)
    
    # 6. Verify completion
    for _ in range(10000):
        if follower.is_complete():
            break
        follower.update(0.016)
        renderer.render(graph, dot)
    
    self.assertTrue(follower.is_complete())
```


### 6.3 Performance Tests

```python
def test_rendering_performance(self):
    """Test rendering maintains 30 FPS with 20k nodes"""
    graph = MazeGraph()
    for i in range(20000):
        graph.add_node(random.uniform(-90, 90), random.uniform(-180, 180))
    
    renderer = SphereRenderer(100, (1920, 1080))
    
    frame_times = []
    for _ in range(100):
        start = time.time()
        renderer.render(graph, dot=None)
        frame_times.append(time.time() - start)
    
    avg_fps = 1.0 / (sum(frame_times) / len(frame_times))
    self.assertGreaterEqual(avg_fps, 30)

def test_graph_memory_usage(self):
    """Test graph memory stays under 500MB for 100k nodes"""
    graph = MazeGraph()
    for i in range(100000):
        graph.add_node(i % 180 - 90, i % 360 - 180)
    
    memory_mb = sys.getsizeof(graph) / (1024 * 1024)
    self.assertLess(memory_mb, 500)
```


***

## 7. Development Roadmap

### Phase 1: Foundation (Weeks 1-2)

- Set up Pygame project structure
- Implement basic sphere rendering with camera controls
- Create MazeGraph class with basic operations
- Write unit tests for core data structures


### Phase 2: Core Systems (Weeks 3-4)

- Implement spherical coordinate projection
- Build AI integration with OpenAI API[^8][^2]
- Create prompt templates and response parser
- Develop dot navigation system
- Write integration tests


### Phase 3: Advanced Features (Weeks 5-6)

- Add dynamic maze expansion
- Implement persistence layer
- Optimize rendering performance
- Add UI for prompt input and controls


### Phase 4: Polish \& Testing (Weeks 7-8)

- Performance profiling and optimization
- Comprehensive testing (unit, integration, performance)
- Documentation and code cleanup
- Beta testing

***

## 8. Risk Mitigation

| Risk | Impact | Mitigation |
| :-- | :-- | :-- |
| Pygame 3D rendering too slow | High | Implement aggressive culling, LOD, spatial partitioning |
| OpenAI API costs exceed budget | Medium | Cache responses, implement rate limiting, add local fallback |
| Cyclic tree becomes too complex | Medium | Implement graph pruning, limit max nodes per session |
| Spherical math errors | Low | Use tested libraries (numpy), extensive unit tests |
| AI generates invalid mazes | Medium | Robust parsing with validation, fallback generation |


***

## 9. Success Metrics

- **Performance**: Maintain 30+ FPS with 10k+ visible nodes
- **Quality**: 90%+ of AI-generated mazes are playable without manual fixes
- **User Engagement**: Players explore 500+ nodes per session on average
- **Stability**: <1% crash rate during normal gameplay
- **Test Coverage**: >85% code coverage with passing unit tests

***

This comprehensive PRD provides the technical depth, testing strategy, and implementation considerations needed to build your AI-powered spherical maze game in Pygame. The unit tests ensure code quality, while the detailed technical specifications guide implementation.[^4][^5][^8][^2]
<span style="display:none">[^10][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.geeksforgeeks.org/python/create-a-cycle-graph-using-networkx-in-python/

[^2]: https://www.planeks.net/open-ai-api-integration-guide/

[^3]: https://prepinsta.com/data-structures-and-algorithms-in-python/cycle-detection-in-graphs/

[^4]: https://stackoverflow.com/questions/4865636/does-pygame-do-3d

[^5]: https://github.com/Anthony-Gambale/Pygame-3D

[^6]: https://www.songho.ca/opengl/gl_sphere.html

[^7]: https://www.pygame.org/docs/ref/surface.html

[^8]: https://pypi.org/project/openai/

[^9]: https://www.reddit.com/r/gamedev/comments/fcy1y/technique_for_rendering_shapes_on_spherical/

[^10]: https://www.youtube.com/watch?v=D96wb46mjIQ

