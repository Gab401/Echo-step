# Class for the board game
# Classes:
#   - Tile
#   - BoardGame

# Generic import
from math import sqrt
import pygame
import os
from collections import deque
import numpy as np

# Local import
from Constants import *

# Tile class
class Tile:

    def __init__(self, window, x, y, behaviour=None, path_to_image=PATH_TO_TILES + DEFAULT_TILE + ".png"):

        # Coordinates of the upper left corner of the tile
        self.x = x 
        self.y = y

        # The window to draw the tile on
        self.window = window

        # Image of the tile
        self.image = pygame.image.load(path_to_image)

        # Behaviour of the tile
        self.behaviour = behaviour
        if self.behaviour is None and path_to_image == PATH_TO_TILES + DEFAULT_TILE + ".png":
            self.behaviour = "water"

        # Altitude transition with the neighboring tiles (N, E, S, W)
        self.alt_transition = [0, 0, 0, 0]

        # Relative altitude subgrid of the tile 
        self.rel_alt_subgrid = [[0 for _ in range(4)] for _ in range(4)]


    def draw(self):
        # Draw the tile on the window at its coordinates
        self.window.blit(self.image, (self.x, self.y))



# Random rule class
class RandomRule:

    def __init__(self, name):
        self.name = name

        # Dictionary of the parameters of the rule : keys = 'TXY', value = probability of the key
        self.parameters = {}

    
    def addParameter(self, tile_code, probability):
        self.parameters[tile_code] = probability


    def isValid(self):
        assert sum(self.parameters.values()) == 100, f"Probabilities of the rule {self.name} do not sum to 100%."


    def randomTile(self):
        # Return a random tile code according to the probabilities of the parameters
        import random
        r = random.random()
        cumulative_probability = 0.0
        for tile_code, probability in self.parameters.items():
            cumulative_probability += probability/100
            if r < cumulative_probability:
                return tile_code
        raise ValueError("Probabilities do not sum to 100%")
    
    def __str__(self):
        return f"Random rule {self.name} with parameters : {self.parameters}"




# Board game class
class BoardGame:

    def __init__(self, window, map_name=DEFAULT_MAP, debug=False):

        self.debug = debug

        # Check if the map file exists
        assert os.path.exists(PATH_TO_MAPS + map_name + ".txt"), f"Map file {map_name}.txt not found in {PATH_TO_MAPS} folder."

        # Check if the tile folder exists
        assert os.path.exists(PATH_TO_TILES), f"Tile folder {PATH_TO_TILES} not found."

        self.window = window

        # Dictionary containing the tile information
        self.tile_codes = {}    # Keys = tile codes (strings of 2 characters), values = path to the image of the tile
        self.scanTileFolder()
        
        # Features of the map
        self.map_name = map_name
        self.tiles = [[None for _ in range(NB_TILES_X)] for _ in range(NB_TILES_Y)] 
        self.surface = pygame.Surface((NB_TILES_X * TILE_SIZE, NB_TILES_Y * TILE_SIZE)) # Surface to draw the tiles on, which will be blitted on the window in the draw method

        # Features of the tiles
        self.rules = {}     
        self.alt_transitions = {}  # Dictionary of the altitude transitions : keys = tile code, value = [N, E, S, W] where N, E, S, W are the altitude differences with the neighboring tiles in the 4 directions (N, E, S, W)
        self.alt_subgrid = {} # Dictionary of the altitude subgrid : keys = tile code, value = 2D list of the altitudes of the tile (with a resolution of TILE_SIZE // RESIZE_FACTOR pixels)
        self.behaviour = {} # Dictionary of the behaviour of the tiles : keys = tile code, value = behaviour (string)

        # Initial poositions of the characters on the map : keys = character name, value = [(x1, y1), (x2, y2), ...]
        self.init_character_positions = {}

        self.loadMap()

        self.macro_altitudes = np.zeros((NB_TILES_Y, NB_TILES_X)) # Matrix of the macro altitudes of the tiles (altitude of the top of the tile)
        self.micro_altitudes = np.zeros((NB_TILES_Y * 4, NB_TILES_X * 4)) # Matrix of the micro altitudes of the tiles, with a resolution of TILE_SIZE // RESIZE_FACTOR pixels
        self.computeMacroAltitudes()
        self.computeMicroAltitudes()
        

    def loadMap(self):
        """
            Load the map from a file and create the tiles accordingly.
            The structure of the map file is as in the example "TestMap.txt" in the "Maps" folder.
        """
        if self.debug:
            print(f" ---- Loading map {self.map_name} ---- ")

        # Open the map file and read it line by line
        with open(PATH_TO_MAPS + self.map_name + ".txt", "r") as f:

            # Passe the lines until the line "MAP" is reached
            while True:
                line = f.readline()

                if line.strip() == "MAP":
                    break

                if line[0] == '#': # Skip comments
                    continue

                if line.split(';')[0] == "RULE": # Specific rule
                    rule_name = line.split(';')[1].strip()
                    self.rules[rule_name] = RandomRule(rule_name)
                    
                    while True:
                        line = f.readline()

                        if line.strip() == "ENDRULE":
                            break

                        if line[0] == '#': # Skip comments
                            continue

                        tile_code, probability = line.split(';')
                        tile_code = tile_code.strip()[1:] # Remove the 'T' at the beginning of the tile code
                        probability = float(probability.strip())
                        self.rules[rule_name].addParameter(tile_code, probability)
                    self.rules[rule_name].isValid()
                    if self.debug:
                        print(self.rules[rule_name])

                if line.split(';')[0] == "ALT_TRANSITION": # Altitude transition

                    # Read the tile codes
                    tiles = []
                    for code in line.split(';')[1:]:
                        code = code.strip()[1:] # Remove the 'T' at the beginning of the tile code
                        tiles.append(code)
                    
                    # Read the altitude differences
                    line = f.readline()
                    alt_differences = []
                    for alt in line.split(';'):
                        alt = alt.strip()
                        if alt == "I":
                            alt_differences.append(float('inf'))
                        else:
                            alt_differences.append(int(alt))
                    
                    # Add the altitude transition to the dictionary
                    for tile in tiles:
                        self.alt_transitions[tile] = alt_differences
                    if self.debug:
                        print(f"Altitude transition for tiles {tiles} : {alt_differences}")

                if line.split(';')[0] == "ALT_SUBGRID": # Altitude subgrid

                    # Read the tile code
                    tile_code = []
                    for code in line.split(';')[1:]:
                        code = code.strip()[1:] # Remove the 'T' at the beginning of the tile code
                        tile_code.append(code)
                    
                    # Read the altitude subgrid
                    alt_subgrid = []
                    for _ in range(4):
                        line = f.readline()
                        alt_subgrid.append([float('inf') if alt.strip() == "I" else int(alt.strip()) for alt in line.split(';')])
                    
                    # Add the altitude subgrid to the dictionary
                    for tile in tile_code:
                        self.alt_subgrid[tile] = alt_subgrid
                    if self.debug:
                        print(f"Altitude subgrid for tiles {tile_code} : {alt_subgrid}")

                if line.split(';')[0] == "BEHAVIOUR": # Behaviour

                    # Read the tile codes
                    tiles = []
                    for code in line.split(';')[1:-1]:
                        code = code.strip()[1:] # Remove the 'T' at the beginning of the tile code
                        tiles.append(code)
                    
                    # Read the behaviour
                    line = f.readline()
                    behaviour = line.strip()

                    # Add the behaviour to the corresponding tiles
                    for tile in tiles:
                        self.behaviour[tile] = behaviour
                    if self.debug:
                        print(f"Behaviour for tiles {tiles} : {behaviour}")

                if line.split(';')[0] == "POSITION": # Initial position of the characters

                    # Read the character name
                    character_name = line.split(';')[1].strip()

                    # Read the positions
                    positions = []
                    line = f.readline()
                    while line.strip() != "ENDPOSITION":
                        if line[0] == '#': # Skip comments
                            line = f.readline()
                            continue
                        x, y = line.split(';')
                        x = int(x.strip())
                        y = int(y.strip())
                        positions.append((x, y))
                        line = f.readline()
                    
                    # Add the positions to the dictionary
                    self.init_character_positions[character_name] = positions

            # Read the map line by line
            y = 0
            while True:

                x = 0
                line = f.readline()

                if line[0] == '#': # Skip comments
                    continue
                if line.strip() == "ENDMAP": # If needed we fill the remaining lines with empty tiles until the end of the map
                    for y in range(y, NB_TILES_Y):
                        for x in range(NB_TILES_X):
                            self.tiles[y][x] = Tile(self.surface, x * TILE_SIZE, y * TILE_SIZE)
                    break

                for tile_code in line.split(';'):

                    tile_code = tile_code.strip()

                    if tile_code == "ENDLINE": # If needed we fill the remaining columns with empty tiles until the end of the line
                        for x in range(x, NB_TILES_X):
                            self.tiles[y][x] = Tile(self.surface, x * TILE_SIZE, y * TILE_SIZE)
                        break

                    # Check the tile code
                    assert len(tile_code) == 3, f"Invalid tile code {tile_code} in map file {self.map_name}.txt. Tile codes should be 3 characters long."

                    if tile_code[0] == 'T': # Normal mode
                        tile_code = tile_code[1:]
                        assert tile_code[0] in DIGITS and tile_code[1] in DIGITS, f"Invalid tile code {tile_code} in map file {self.map_name}.txt."
                        assert tile_code in self.tile_codes.keys(), f"Tile code {tile_code} not found in tile folder."
                    
                    elif tile_code[0] == 'R': # Random mode
                        assert tile_code in self.rules.keys(), f"Rule {tile_code} not found in map file {self.map_name}.txt."
                        tile_code = self.rules[tile_code].randomTile()
                        assert tile_code in self.tile_codes.keys(), f"Tile code {tile_code} not found in tile folder."
                    
                    else:
                        raise ValueError(f"Invalid tile code {tile_code} in map file {self.map_name}.txt. Tile codes should start with 'T' or 'R'.")

                    # Create the tile and add it to the list of tiles
                    self.tiles[y][x] = Tile(self.surface, x * TILE_SIZE, y * TILE_SIZE, path_to_image=self.tile_codes[tile_code])

                    # Add the altitude transition and subgrid to the tile if they exist
                    if tile_code in self.alt_transitions.keys():
                        self.tiles[y][x].alt_transition = self.alt_transitions[tile_code]
                    if tile_code in self.alt_subgrid.keys():
                        self.tiles[y][x].rel_alt_subgrid = self.alt_subgrid[tile_code]

                    # Add the behaviour to the tile if it exists
                    if tile_code in self.behaviour.keys():
                        self.tiles[y][x].behaviour = self.behaviour[tile_code]

                    x += 1
                                    
                y += 1

        # Draw the tiles on the surface
        for x in range(NB_TILES_X):
            for y in range(NB_TILES_Y):
                self.tiles[y][x].draw()

        if self.debug:
            print(f" ---- Map {self.map_name} loaded ---- ")
    

    def scanTileFolder(self):
        """
            Scan the tile folder and return a list of the tile codes and their corresponding images.
            The tile codes are extracted from the file names, which should contain the tile code in the format "Txy", where x and y are digits.
        """

        for file_name in os.listdir(PATH_TO_TILES):

            if file_name.endswith(".png"):

                # Detect a tile code in the file name
                for i in range(len(file_name) - 2):
                    if file_name[i] == 'T' and file_name[i+1] in DIGITS and file_name[i+2] in DIGITS:
                        tile_code = file_name[i+1:i+3]
                        self.tile_codes[tile_code] = PATH_TO_TILES + file_name
                        break
    

    def computeMacroAltitudes_DO_NOT_USE__OBSOLET(self):
        """
            Compute the macro altitudes of the tiles (altitude of the top of the tile) and store them in the macro_altitudes attribute.
            We use a BFS algorithm to compute the altitudes, starting from the tiles in position (0, 0) wich is considered as the reference tile with an altitude of 0.
        """
        visited = [[False for _ in range(NB_TILES_X)] for _ in range(NB_TILES_Y)]
        queue = deque([(0, 0)])
        self.macro_altitudes[0, 0] = 0
        visited[0][0] = True

        # Indices in the alt_transition: [Incoming face of Target, Outgoing face of Current]
        # Correspond to moving: South, West, North, East
        NESW = [[0, 2], [1, 3], [2, 0], [3, 1]]

        while queue:
            x, y = queue.popleft()
            current_altitude = self.macro_altitudes[y, x]

            # (dx, dy) correspond to movements south, west, north, and east
            # Which correspond to the ENTRANCE sides: N (0), E (1), S (2), W (3)
            for i, (dx, dy) in enumerate([(0, 1), (-1, 0), (0, -1), (1, 0)]): # N, E, S, W
                nx, ny = x + dx, y + dy

                if 0 <= nx < NB_TILES_X and 0 <= ny < NB_TILES_Y and not visited[ny][nx]:
                    
                    # Get the altitude transition from the current tile to the neighboring tile
                    target_in_trans = self.tiles[ny][nx].alt_transition[NESW[i][0]]
                    current_out_trans = self.tiles[y][x].alt_transition[NESW[i][1]]

                    # It is blocked
                    if target_in_trans == float('inf') or current_out_trans == float('inf'):
                        continue

                    # Calculate the altitude of the neighboring tile
                    altitude_transition = target_in_trans - current_out_trans

                    self.macro_altitudes[ny, nx] = current_altitude + altitude_transition
                    visited[ny][nx] = True
                    queue.append((nx, ny))
        
        # Print the macro altitudes of the tiles for debugging
        if self.debug:
            print("Macro altitudes of the tiles :")
            for y in range(NB_TILES_Y):
                for x in range(NB_TILES_X):
                    print(f"{int(self.macro_altitudes[y][x])}", end=" ")
                print()


    def computeMacroAltitudes_DO_NOT_USE__OBSOLET_bis(self):
        """
            Compute the macro altitudes of the tiles (altitude of the top of the tile) and store them in the macro_altitudes attribute.
            We use a BFS algorithm to compute the altitudes, starting from the tiles in position (0, 0) wich is considered as the reference tile with an altitude of 0.
        """
        visited = [[False for _ in range(NB_TILES_X)] for _ in range(NB_TILES_Y)]
        queue = deque([])

        # We assume that water has always an altitude of 0
        for y in range(NB_TILES_Y):
            for x in range(NB_TILES_X):
                if self.tiles[y][x].behaviour == "water":  # Ou si le nom est T00
                    self.macro_altitudes[y][x] = 0
                    queue.append((x, y))    
                    visited[y][x] = True

        # If no water
        if not queue: 
            self.macro_altitudes[0, 0] = 0
            queue.append((0, 0))
            visited[0][0] = True

        while queue:
            x, y = queue.popleft()
            current_altitude = self.macro_altitudes[y, x]

            # (dx, dy) correspond to movements south, west, north, and east
            # Which correspond to the ENTRANCE sides
            for dx, dy, in_dir, out_dir in [(0, 1, 0, 2), (-1, 0, 1, 3), (0, -1, 2, 0), (1, 0, 3, 1)]: # N, E, S, W
                nx, ny = x + dx, y + dy

                if 0 <= nx < NB_TILES_X and 0 <= ny < NB_TILES_Y and not visited[ny][nx]:
                    
                    # Get the altitude transition from the current tile to the neighboring tile
                    target_in_trans = self.tiles[ny][nx].alt_transition[in_dir]
                    current_out_trans = self.tiles[y][x].alt_transition[out_dir]

                    # It is blocked
                    if target_in_trans == float('inf') or current_out_trans == float('inf'):
                        continue

                    # Calculate the altitude of the neighboring tile
                    altitude_transition = target_in_trans - current_out_trans

                    # If the altitude change, we only trust the wall we climb on from the south
                    if dx != 0 and altitude_transition != 0:
                        continue
                    
                    # If we are going north, we only trust the altitude change if we are climbing up
                    if dy == -1 and altitude_transition < 0: 
                        continue

                    # If we are going south, we only trust the altitude change if we are climbing down
                    if dy == 1 and altitude_transition > 0: 
                        continue

                    self.macro_altitudes[ny, nx] = current_altitude + altitude_transition
                    visited[ny][nx] = True
                    queue.append((nx, ny))
        
        # Print the macro altitudes of the tiles for debugging
        if self.debug:
            print("Macro altitudes of the tiles :")
            for y in range(NB_TILES_Y):
                for x in range(NB_TILES_X):
                    print(f"{int(self.macro_altitudes[y][x])}", end=" ")
                print()


    def computeMacroAltitudes(self):
        """
            Compute the macro altitudes using a strict Bottom-Up Sweep Algorithm.
            We calculate altitude vertically from the South, then propagate horizontally on flat grounds.
        """
        visited = [[False for _ in range(NB_TILES_X)] for _ in range(NB_TILES_Y)]
        self.macro_altitudes = np.array([[-1 for _ in range(NB_TILES_X)] for _ in range(NB_TILES_Y)])
        
        # We assume that water has always an altitude of 0
        for y in range(NB_TILES_Y):
            for x in range(NB_TILES_X):
                if self.tiles[y][x].behaviour == "water":
                    self.macro_altitudes[y][x] = 0
                    visited[y][x] = True
        
        # we set the altitude of the bottom line to 0
        for x in range(NB_TILES_X):
            if self.macro_altitudes[NB_TILES_Y - 1, x] == -1:
                self.macro_altitudes[NB_TILES_Y - 1, x] = 0
                visited[NB_TILES_Y - 1][x] = True

        # BOTTOM-UP 
        for y in range(NB_TILES_Y - 2, -1, -1): 
            
            # We calculate the altitude of the tiles y based on the tiles y+1
            for x in range(NB_TILES_X):

                if not visited[y][x] and visited[y+1][x]:
                    # North direction : Target = y (Input South = 2), Current = y+1 (Output North = 0)
                    target_in = self.tiles[y][x].alt_transition[2]     
                    current_out = self.tiles[y+1][x].alt_transition[0] 
                    
                    if target_in != float('inf') and current_out != float('inf'):
                        transition = target_in - current_out

                        self.macro_altitudes[y][x] = self.macro_altitudes[y+1][x] + transition
                        visited[y][x] = True
                        
                        # Propagation on the flat ground : BFS
                        queue = deque([(x, y)])
                    
                        while queue:
                            cur_x, cur_y = queue.popleft()

                            for dx, dy, in_dir, out_dir in [(0, 1, 0, 2), (-1, 0, 1, 3), (0, -1, 2, 0), (1, 0, 3, 1)]: # N, E, S, W
                                nx, ny = cur_x + dx, cur_y + dy

                                if 0 <= nx < NB_TILES_X and 0 <= ny < NB_TILES_Y and not visited[ny][nx]:
                                    bfs_target_in = self.tiles[ny][nx].alt_transition[in_dir]
                                    bfs_current_out = self.tiles[cur_y][cur_x].alt_transition[out_dir]

                                    if bfs_target_in != float('inf') or bfs_current_out != float('inf'):
                                        bfs_alt_transition = bfs_target_in - bfs_current_out

                                        # Not flat ground
                                        if bfs_alt_transition != 0: 
                                            continue

                                        # Not flat ground
                                        ok = True
                                        for i in range(4):
                                            if self.tiles[ny][nx].alt_transition[i] != 0:
                                                ok = False
                                                break
                                        
                                        if ok:
                                            self.macro_altitudes[ny, nx] = self.macro_altitudes[y][x]
                                            visited[ny][nx] = True
                                            queue.append((nx, ny))
            """
            print(f"Macro altitudes of the tiles : after processing line {y}")
            for y in range(NB_TILES_Y):
                for x in range(NB_TILES_X):
                    print(f"{int(self.macro_altitudes[y, x]):2}", end=" ")
                print()  
            """

        # Debug
        if self.debug:
            print("Macro altitudes of the tiles :")
            for y in range(NB_TILES_Y):
                for x in range(NB_TILES_X):
                    print(f"{int(self.macro_altitudes[y, x]):2}", end=" ")
                print()
        
        # If we have an hole, the map is invalid
        for y in range(NB_TILES_Y):
            for x in range(NB_TILES_X):
                if self.macro_altitudes[y, x] == -1:
                    raise ValueError("Invalid map: Hole found")


    def computeMicroAltitudes(self):
        """
            Compute the micro altitudes of the tiles
            The calculation of the micro altitudes is the following :
                    altitude =  macro_altitude of the tile + relative altitude from the subgrid 
        """
        for x in range(NB_TILES_X):
            for y in range(NB_TILES_Y):
                tile = self.tiles[y][x]
                for i in range(4):
                    for j in range(4):
                        self.micro_altitudes[y * 4 + i, x * 4 + j] = self.macro_altitudes[y, x] + tile.rel_alt_subgrid[i][j]


    def getAltitudeMasks(self):
        """
            Compute the altitude masks of the map and return them.
            Return a dictionary of the altitude masks : keys = altitude, value = list of coordinates of the pixels with this altitude
        """
        # Compute the altitude masks
        altitude_masks = {} # Dictionary of the altitude masks : keys = altitude, value = list of coordinates of the pixels with this altitude
        for x in range(NB_TILES_X * 4):
            for y in range(NB_TILES_Y * 4):
                altitude = self.micro_altitudes[y, x]
                if altitude == float('inf'):
                    continue
                if altitude not in altitude_masks.keys():
                    altitude_masks[altitude] = []
                x1 = x * (TILE_SIZE // 4) 
                y1 = y * (TILE_SIZE // 4)
                x2 = x1 + (TILE_SIZE // 4)
                y2 = y1 + (TILE_SIZE // 4)
                for i in range(x1, x2):
                    for j in range(y1, y2):
                        altitude_masks[altitude].append((i, j))

        if self.debug:
            print("Altitude masks computed :")
            for altitude, coordinates in altitude_masks.items():
                print(f"Altitude {altitude} : {len(coordinates)} pixels")
    
        return altitude_masks     


    def getMacroAltitude(self, x, y):
        """
            Get the macro altitude of the tile at the coordinates (x, y) in pixels.
            We first convert the coordinates from pixels to tile coordinates, then we return the macro altitude of the corresponding tile.
        """
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        return float(self.macro_altitudes[tile_y, tile_x])
    

    def getMicroAltitude(self, x, y):
        """
            Get the micro altitude of the tile at the coordinates (x, y) in pixels.
            We first convert the coordinates from pixels to tile coordinates, then we return the micro altitude of the corresponding tile.
        """
        x = max(0, min(x, NB_TILES_X * TILE_SIZE - 1)) # Ensure x is within the bounds of the map
        y = max(0, min(y, NB_TILES_Y * TILE_SIZE - 1)) # Ensure y is within the bounds of the map

        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        
        subgrid_x = (x % TILE_SIZE) // (TILE_SIZE // 4)
        subgrid_y = (y % TILE_SIZE) // (TILE_SIZE // 4)
        return self.micro_altitudes[tile_y * 4 + subgrid_y, tile_x * 4 + subgrid_x]


    def isWater(self, x, y):
        """
            Check if the tile at the coordinates (x, y) in pixels is a water tile.
        """
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        return self.tiles[tile_y][tile_x].behaviour == "water"


    def draw(self):
        # Draw the surface with the tiles on the window
        self.window.blit(self.surface, (0, 0))


    def getShortestPath(self, start_x, start_y, end_x, end_y, in_water=False):
        """
            Get the shortest path from the coordinates start to the coordinates end, using a BFS algorithm.
            The path is returned as a list of tile coordinates (in tiles, not pixels).
        """
        start_x = start_x // TILE_SIZE
        start_y = start_y // TILE_SIZE
        end_x = end_x // TILE_SIZE
        end_y = end_y // TILE_SIZE
        visited = [[False for _ in range(NB_TILES_X)] for _ in range(NB_TILES_Y)]
        queue = deque([(start_x, start_y, [])])
        visited[start_y][start_x] = True

        while queue:
            x, y, path = queue.popleft()

            if (x, y) == (end_x, end_y):
                path = path + [(x, y)]
                return path

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy

                if 0 <= nx < NB_TILES_X and 0 <= ny < NB_TILES_Y and not visited[ny][nx]:
                    if in_water and self.tiles[ny][nx].behaviour != "water":
                        continue
                    visited[ny][nx] = True
                    queue.append((nx, ny, path + [(x, y)]))
        
        return None # No path found
    
    
    def getListOfAltitudes(self):
        """
            Get the list of altitudes of the map.
        """
        altitudes = set()
        for y in range(NB_TILES_Y):
            for x in range(NB_TILES_X):
                altitude = self.macro_altitudes[y, x]
                if altitude != float('inf'):
                    altitudes.add(altitude)
        return sorted(list(altitudes))


    def getCharacterInitialPositions(self):
        """
            Get the initial positions of the characters on the map.
            Return a dictionary : keys = character name, value = list of coordinates of the initial positions of the character.
        """
        if self.debug:
            print("Initial positions of the characters :")
            for name, positions in self.init_character_positions.items():
                print(f"  {name}: {positions}")
        return self.init_character_positions


















if __name__ == "__main__":

    # Initialize Pygame
    pygame.init()

    # Create the window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # Create BoardGame
    board_game = BoardGame(window)

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fill the window with white
        window.fill((255, 255, 255))

        # Draw the tiles
        board_game.draw()

        # Update the display
        pygame.display.flip()


