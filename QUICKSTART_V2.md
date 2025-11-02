# V2 Quick Start - First-Person Maze Explorer

## 🚀 Run V2 (30 seconds)

```bash
cd E:\Spherical_Maze
python main_v2.py
```

## 🎮 Controls

### Essential (Learn These First)
- **Mouse** - Look around (auto-grabbed on start)
- **W** - Forward
- **A** - Strafe left
- **S** - Backward
- **D** - Strafe right
- **TAB** - Release/grab mouse
- **ESC** - Quit (when mouse is free)

### Advanced
- **G** - Generate new maze
- **R** - Reset everything
- **S** - Save game
- **L** - Load last save
- **F3** - Toggle debug info

## 📋 Quick Tips

1. **Mouse gets captured automatically** on start
   - Move mouse to look around
   - Press **TAB** to release if needed

2. **WASD moves you** (not the world)
   - W/S = forward/back in direction you're looking
   - A/D = strafe left/right

3. **Generate a maze first**
   - Press **TAB** to release mouse
   - Press **G** to generate
   - Press **TAB** again to grab mouse

4. **Adjust settings** in `spherical_maze/game_v2.py`:
   ```python
   self.mouse_sensitivity = 0.2  # Mouse speed
   self.move_speed = 10.0        # Walk speed
   ```

## 🔄 Switching Between V1 and V2

```bash
# V1: Top-down strategic view
python main.py

# V2: First-person explorer (NEW!)
python main_v2.py
```

Both work independently, use same saves!

## 🐛 Troubleshooting

**Q: Mouse doesn't work**
- Press **TAB** to grab mouse

**Q: Can't see maze**
- Press **G** to generate
- Use mouse to look around

**Q: Movement feels slow/fast**
- Edit `move_speed` in game_v2.py

**Q: Mouse too sensitive**
- Edit `mouse_sensitivity` in game_v2.py

**Q: Want to quit but mouse is grabbed**
- Press **TAB** first
- Then press **ESC**

## ⚡ Performance

If FPS drops:
1. Generate simpler mazes (press **G** repeatedly)
2. Reduce screen size in code
3. Close other applications

## 📚 Learn More

- `README_V2.md` - Full user guide
- `V2_DESIGN.md` - Technical details
- `V2_SUMMARY.md` - Complete overview

## 🎉 That's It!

You're ready to explore spherical mazes in first-person!

**Pro tip**: Generate a "grid" maze for best corridor feel:
```bash
# Edit main_v2.py line 42:
self.generate_initial_maze("Create a grid maze")
```

Happy exploring! 🎮🌍
