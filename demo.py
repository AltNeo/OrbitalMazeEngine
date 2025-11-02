"""Quick demo script to test the game without GUI."""

from spherical_maze.ai_generator import AIMapGenerator
from spherical_maze.maze_graph import MazeGraph
from spherical_maze.navigation import DotEntity, PathFollower


def main() -> None:
    """Run a simple headless demo."""
    print("Spherical Maze Demo")
    print("=" * 50)

    print("\n1. Creating maze graph...")
    graph = MazeGraph()
    generator = AIMapGenerator(use_dummy=True)

    print("2. Generating a spiral maze...")
    maze_data = generator.generate_maze(
        "Create a spiral maze", start_position=(0.0, 0.0), complexity="medium"
    )
    print(f"   Generated {len(maze_data['nodes'])} nodes and {len(maze_data['edges'])} edges")

    print("\n3. Importing maze to graph...")
    start_node = generator.import_to_graph(maze_data, graph)
    print(f"   Graph now has {len(graph.nodes)} nodes and {len(graph.edges)} edges")

    print("\n4. Creating dot entity at start...")
    if start_node:
        dot = DotEntity(latitude=start_node.latitude, longitude=start_node.longitude, speed=20.0)
        print(f"   Dot placed at ({dot.latitude:.2f}, {dot.longitude:.2f})")

        print("\n5. Finding path to end node...")
        nodes_list = list(graph.nodes.values())
        if len(nodes_list) > 1:
            end_node = nodes_list[-1]
            path = graph.shortest_path(start_node.id, end_node.id)

            if path:
                print(f"   Path found with {len(path)} waypoints")

                print("\n6. Simulating dot movement...")
                follower = PathFollower(dot, graph)
                follower.start_following(path)

                steps = 0
                max_steps = 1000
                while not follower.is_complete() and steps < max_steps:
                    follower.update(0.1)
                    steps += 1

                    if steps % 100 == 0:
                        print(f"   Step {steps}: Dot at ({dot.latitude:.2f}, {dot.longitude:.2f})")

                if follower.is_complete():
                    print(f"\n   SUCCESS! Dot reached destination in {steps} steps")
                    print(f"   Final position: ({dot.latitude:.2f}, {dot.longitude:.2f})")
                else:
                    print(f"\n   Reached max steps ({max_steps})")
            else:
                print("   No path found!")
        else:
            print("   Not enough nodes for pathfinding")

    print("\n7. Testing cycle detection...")
    has_cycle = graph.has_cycle()
    print(f"   Graph has cycles: {has_cycle}")

    print("\n8. Testing save/load...")
    from spherical_maze.persistence import SaveManager

    save_manager = SaveManager()
    if start_node:
        save_path = save_manager.save_game(
            graph, (start_node.latitude, start_node.longitude), {"demo": True}
        )
        print(f"   Game saved to: {save_path.name}")

        loaded = save_manager.load_game(save_path)
        print("   Game loaded successfully!")
        print(f"   Loaded graph has {len(loaded['graph'].nodes)} nodes")

        save_path.unlink()
        print("   Cleaned up save file")

    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nTo run the full game with GUI, execute: python main.py")


if __name__ == "__main__":
    main()
