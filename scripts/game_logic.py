import engine
import random
import copy
import os
import platform
import sys
import time

# Display Configuration
ANSI_BG_RED = "\033[41m"
ANSI_RESET  = "\033[0m"
ANSI_CLS    = "\033[2J"
ANSI_HOME   = "\033[H"

TILE_FLOOR = 0
TILE_WALL = 1
MAP_W = 20
MAP_H = 15
WORLD_SIZE = 5 

# Weapon Database configuration mapping internal IDs to display name and damage values
WEAPON_DB = {
    "fists": ("Fists", 1),
    "rusty_sword": ("Rusty Sword", 3),
    "iron_sword": ("Iron Sword", 5),
    "battle_axe": ("Battle Axe", 8)
}

# Global State
allGrid = [[None for _ in range(WORLD_SIZE)] for _ in range(WORLD_SIZE)]
currentMapX = 2
currentMapY = 2

game_grid = [] 
enemies = [] 
chests = []

def trigger_damage_flash():
    # Visual feedback for taking damage using ANSI escape codes
    # This blocks the main thread for 100ms to emphasize the hit
    sys.stdout.write(ANSI_BG_RED)
    sys.stdout.write(ANSI_CLS)
    sys.stdout.flush()
    
    time.sleep(0.1)
    
    sys.stdout.write(ANSI_RESET)
    sys.stdout.write(ANSI_CLS)
    sys.stdout.write(ANSI_HOME)
    sys.stdout.flush()

# Region Persistence Logic
def save_zone(mx, my):
    # Serialize current zone state into the global grid
    # We must explicitly copy lists to avoid reference issues when reloading later
    global allGrid, game_grid, enemies, chests
    
    zone_data = {
        "grid": game_grid,
        "enemies": list(enemies), 
        "chests": list(chests)
    }
    allGrid[my][mx] = zone_data

def load_zone(mx, my):
    # Retrieve zone data from memory or generate a fresh zone if none exists
    global allGrid, game_grid, enemies, chests
    
    zone_data = allGrid[my][mx]
    
    if zone_data:
        print(f"\n[!] Loading existing zone ({mx}, {my})...")
        game_grid = zone_data["grid"]
        enemies = list(zone_data["enemies"]) 
        chests = list(zone_data["chests"])
    else:
        generate_map()

# Procedural Generation (Conway's Game of Life)
def count_alive_neighbors(map_grid, x, y):
    height, width = len(map_grid), len(map_grid[0])
    count = 0   
    directions = [(-1, -1), (0, -1), (1, -1), (-1, 0),(1, 0), (-1, 1), (0, 1), (1, 1)]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        is_out_of_bounds = (nx < 0 or ny < 0 or nx >= width or ny >= height)
        # Treat out of bounds as walls to encourage closed rooms
        if is_out_of_bounds or map_grid[ny][nx] == TILE_WALL:
            count += 1
    return count

def do_conways(old_map):
    # Apply one iteration of Conway's rules to smooth the noise
    height = len(old_map)
    width = len(old_map[0])
    new_map = copy.deepcopy(old_map)
    
    for y in range(height):
        for x in range(width):
            neighbors = count_alive_neighbors(old_map, x, y)
            if old_map[y][x] == TILE_WALL:
                new_map[y][x] = TILE_FLOOR if neighbors < 4 else TILE_WALL
            else:
                new_map[y][x] = TILE_WALL if neighbors > 4 else TILE_FLOOR
    return new_map

def generate_map():
    global game_grid, enemies, chests
    print(f"\n[!] Generating NEW zone ({currentMapX}, {currentMapY})...")
    
    enemies = [] 
    chests = []
    temp_map = []

    # Step 1: Fill map with random noise
    for y in range(MAP_H):
        row = []
        for x in range(MAP_W):
            row.append(TILE_WALL if random.random() < 0.45 else TILE_FLOOR)
        temp_map.append(row)

    # Step 2: Smooth using Conway's algorithm
    for _ in range(3):
        temp_map = do_conways(temp_map)
    game_grid = temp_map

    # Step 3: Populate entities on valid floor tiles
    for y in range(MAP_H):
        for x in range(MAP_W):
            if game_grid[y][x] == TILE_FLOOR:
                if random.random() < 0.05: 
                    # Enemy(x, y, hp, dmg, type)
                    enemies.append(engine.Enemy(x, y, 10, 2, 1))
                elif random.random() < 0.03: 
                    chests.append(engine.Chest(x, y))
    return game_grid

# Core Gameplay
def get_at(x, y):
    for e in enemies:
        if e.x == x and e.y == y: return e
    for c in chests:
        if c.x == x and c.y == y: return c
    return None

def is_walkable(x, y):
    # Boundary check is permissive to allow map transitions
    if x < 0 or y < 0 or x >= MAP_W or y >= MAP_H: return True
    return game_grid[y][x] != TILE_WALL

def open_chest(chest_obj, player):
    print("Opening chest...")
    # Dynamically fetch valid items from the C++ backend
    if hasattr(engine, "getAllItemIDs"):
        valid_ids = engine.getAllItemIDs()
        if valid_ids:
            item_id = random.choice(valid_ids)
            print(f"You found an item ID: {item_id}!")
            player.addItem(item_id)
            
            # Auto-equip logic if it's a weapon
            # This is a simple check; a robust system would check item type first
            item_name = player.inspectItem(item_id).lower().replace(" ", "_")
            if item_name in WEAPON_DB:
                player.current_weapon_id = item_name
                print(f"Equipped {item_name}!")
    
    if chest_obj in chests:
        chests.remove(chest_obj)

def printMap(player): 
    print(f"\nLocation: Sector ({currentMapX},{currentMapY})")
    for y in range(len(game_grid) - 1, -1, -1):
        line = ""
        for x in range(len(game_grid[y])):
            entity = get_at(x, y)
            if x == player.x and y == player.y: line += "@ " 
            elif isinstance(entity, engine.Enemy): line += "E " 
            elif isinstance(entity, engine.Chest): line += "C "
            elif game_grid[y][x] == TILE_WALL: line += "# " 
            else: line += ". " 
        print(line)

def move_enemies(player):
    global enemies
    
    for e in enemies:
        # Distance check to prevent cross-map aggro
        dist_x = player.x - e.x
        dist_y = player.y - e.y
        distance = (dist_x**2 + dist_y**2)**0.5
        
        if distance > 8: continue

        # Greedy pathfinding: attempt to close the largest gap first
        step_x = 0
        step_y = 0
        
        if abs(dist_x) >= abs(dist_y):
            step_x = 1 if dist_x > 0 else -1
        else:
            step_y = 1 if dist_y > 0 else -1

        nx = e.x + step_x
        ny = e.y + step_y

        blocked = False
        
        # Validation checks
        if not is_walkable(nx, ny): blocked = True
        if get_at(nx, ny): blocked = True # Prevent entity stacking

        # Player Interaction
        if nx == player.x and ny == player.y:
            trigger_damage_flash()
            print(f"-> You were hit by an enemy! (-1 HP)")
            player.hp -= 1
            blocked = True 
        
        # Fallback Movement (Try the other axis if primary is blocked)
        if blocked:
            nx, ny = e.x, e.y
            if step_x != 0: 
                step_y = 1 if dist_y > 0 else -1
                ny += step_y
            else: 
                step_x = 1 if dist_x > 0 else -1
                nx += step_x
            
            # Ensure fallback doesn't walk into walls or the player
            if is_walkable(nx, ny) and not get_at(nx, ny) and (nx != player.x or ny != player.y):
                e.x = nx
                e.y = ny
        else:
            e.x = nx
            e.y = ny

def start_game():
    global currentMapX, currentMapY
    player = engine.Player()
    
    # Attach dynamic Python-only property for weapon tracking
    player.current_weapon_id = "fists"
    
    # Initial load triggers map generation
    load_zone(currentMapX, currentMapY)
    
    # Safe Spawn Logic
    player.x, player.y = 1, 1
    while not is_walkable(player.x, player.y):
        player.x += 1 

    print("System Initialized.")
    print("Controls: (WASD) Move, (E)Interact, (K)Save, (L)Load, (X)Quit")

    while True:
        # HUD Render
        w_name, w_dmg = WEAPON_DB.get(player.current_weapon_id, WEAPON_DB["fists"])
        print(f"\n[Pos: {player.x}, {player.y}] HP: {player.hp} | Wep: {w_name} (Dmg: {w_dmg})")
        
        printMap(player)
        
        try:
            user_input = input("Action: ").strip().lower()
        except EOFError: break
        if not user_input: continue
        key = user_input[0]

        if key == 'x': break
        elif key == 'k': engine.save_game(player)
        elif key == 'l': engine.load_game(player)
        elif key == 'e':
            obj = get_at(player.x, player.y)
            if isinstance(obj, engine.Chest): open_chest(obj, player)
            else: print("Nothing here.")

        elif key in ['w', 'a', 's', 'd']:
            nx, ny = player.x, player.y
            if key == 'w': ny += 1
            elif key == 's': ny -= 1
            elif key == 'a': nx -= 1
            elif key == 'd': nx += 1
            
            # Map Transition Logic
            map_transition = False
            new_mx, new_my = currentMapX, currentMapY
            new_px, new_py = nx, ny

            if nx < 0:
                new_mx -= 1; new_px = MAP_W - 1; map_transition = True
            elif nx >= MAP_W:
                new_mx += 1; new_px = 0; map_transition = True
            elif ny < 0:
                new_my -= 1; new_py = MAP_H - 1; map_transition = True
            elif ny >= MAP_H:
                new_my += 1; new_py = 0; map_transition = True
            # Clear screen based on OS
            if platform.system() == "Windows":
                os.system('cls')
            else:
                os.system('clear')   
            
            if map_transition:
                # Prevent walking off the world edge
                if new_mx < 0 or new_mx >= WORLD_SIZE or new_my < 0 or new_my >= WORLD_SIZE:
                    print("You have reached the edge of the world.")
                else:
                    save_zone(currentMapX, currentMapY)
                    currentMapX, currentMapY = new_mx, new_my
                    load_zone(currentMapX, currentMapY)
                    
                    player.x = new_px
                    player.y = new_py
                    
                    # Prevent spawning inside a wall after transition
                    if not is_walkable(player.x, player.y):
                         game_grid[player.y][player.x] = TILE_FLOOR

            else:
                target = get_at(nx, ny)
                if isinstance(target, engine.Enemy):
                    # Combat Logic
                    weapon_info = WEAPON_DB.get(player.current_weapon_id, WEAPON_DB["fists"])
                    damage = weapon_info[1]
                    
                    target.hp -= damage
                    print(f"-> You hit Enemy with {weapon_info[0]} for {damage} dmg. (HP: {target.hp})")
                    
                    if target.hp <= 0: enemies.remove(target)
                
                elif is_walkable(nx, ny):
                    player.x = nx
                    player.y = ny
                    move_enemies(player)
                else:
                    print("Blocked.")
        else:
            print("Unknown command.")