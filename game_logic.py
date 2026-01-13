import engine
import random

# --- CONFIG ---
TILE_FLOOR = 0
TILE_WALL = 1
TILE_ENEMY = 2

map = [] 

def generate_map(width, height):
    global map
    print(f"[PYTHON] Generating {width}x{height} map...")
    
    current_map = [] # Reset map

    for y in range(height):
        row = []
        for x in range(width):
            # Borders around the map
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                row.append(TILE_WALL)
            # Random Walls
            elif random.random() < 0.2:
                row.append(TILE_WALL)
            else:
                row.append(TILE_FLOOR)
        current_map.append(row)
    
    return current_map

def is_walkable(x, y):
    # Check boundaries
    if y < 0 or y >= len(map) or x < 0 or x >= len(map[0]):
        return False
    # Check wall
    return map[y][x] != TILE_WALL

def printMap():
    for i in map:
        for j in map[0]:
            print[i][j]

def handle_input(key_code, player):
    key = key_code.lower()
    
    new_x = player.x
    new_y = player.y

    if key == 'w': new_y += 1
    elif key == 's': new_y -= 1
    elif key == 'a': new_x -= 1
    elif key == 'd': new_x += 1
    else:
        print("[Python] Unknown command")
        return

    # Check the map
    if is_walkable(new_x, new_y):
        player.x = new_x
        player.y = new_y
        print(f"Moved to {player.x}, {player.y}")
    else:
        print("That is a wall.")