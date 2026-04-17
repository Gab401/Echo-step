# Generic constants

# Window
WINDOW_WIDTH = 1024     # 32 tiles wide
WINDOW_HEIGHT = 800     # 25 tiles high
FPS = 60                # Frames per second


# Constants for the tiles
TILE_SIZE = 32
NB_TILES_X = WINDOW_WIDTH // TILE_SIZE
NB_TILES_Y = WINDOW_HEIGHT // TILE_SIZE


# Constants for the wave simulation
C = 10.0         # Wave speed (m/s)
DX = 1 / TILE_SIZE       # Spatial step (m)
DT =  0.6 * DX / C       # Time step (s), Courant–Friedrichs–Lewy (CFL) condition for stability
ALPHA = 1     # Damping coefficient
BOUNDARY_DAMPING = 50.0  # Damping coefficient for boundaries
SEUIL = 1e-3   # Threshold for considering the wave as extinguished
RESIZE_FACTOR = 4 # One pixel in the simulation corresponds to RESIZE_FACTOR pixels on the screen
BS = 10 # Boundary size : size of the boundary layer in pixels (of the simulation, not the screen)
WAVE_SPEED_MULTIPLIER = 3 # Multiplier for the wave speed (the stability condition makes the speed a spatial constant, but we can use a multiplier to increase it)
WATER_WAVE_SPEED_MULTIPLIER = 1 # Multiplier for the wave speed in water (if the first altitude level is water, we use a specific wave speed multiplier for water)


# Pathes for the construction of the maps
PATH_TO_MAPS = "Maps/"
PATH_TO_TILES = "Images/tiles/v2/"
DEFAULT_TILE = "T00_water"
DEFAULT_MAP = "Level1"

# Path for the sounds
PATH_TO_SOUNDS = "Sounds/v1/"

# Path for the menu
PATH_TO_MENU = "Images/Menu/test1-Gemini/v2/"
PATH_TO_FONTS = "Fonts/"

# Authorized characters in the tile codes
DIGITS = "0123456789ABCDEF"


# Stars
PATH_TO_STAR_IMAGE = "Images/star/v1/1.png"
PATH_TO_EMPTY_STAR_IMAGE = "Images/star/v1/2.png"


# General constants for the moving creatures
GRAVITY = 0.025 # pixels per frame^2
OPPOSITES = {"up": "down", "down": "up", "left": "right", "right": "left"}
DIRS_VEC = {
        "right": (1, 0), 
        "left": (-1, 0),
        "down": (0, 1), 
        "up": (0, -1)
    }
VERTICAL_OFFSET_COEFFICIENT = TILE_SIZE // 2 # DO NOT CHANGE, Coefficient for the vertical offset when drawing the creatures, to create a depth effect (the higher the creature, the more it is drawn up)

# Constants for the main character
HERO_PATH_TO_IMAGES = "Images/hero/v1_without_shadow/"
HEALTH_BAR_PATH_TO_IMAGES = "Images/health_bar/v2/" 
HERO_WIDTH = 32
HERO_HEIGHT = 60
HERO_OFFSET_ANCHORING_Y = 0
HERO_HITBOX_WIDTH_UP_DOWN = 15
HERO_HITBOX_WIDTH_LEFT_RIGHT = 23
HERO_HITBOX_HEIGHT_UP_DOWN = 8
HERO_HITBOX_HEIGHT_LEFT_RIGHT = 8
HERO_GAUSSIAN_LIGHT_AREA_PARAMETERS = (200, 200, 6.5) 

HERO_JUMP_SPEED = 0.3 # step per frame (one step corresponds to an half tile)
HERO_WALK_SPEED = 1 # pixels per frame
HERO_RUN_SPEED = 3 # pixels per frame
HERO_SWIM_SPEED = 2 # pixels per frame
HERO_WALK_RATIO = 10 # Number of frames for each image when walking
HERO_RUN_RATIO = 2 # Number of frames for each image when running
HERO_SWIM_RATIO = 5 # Number of frames for each image when swimming
HERO_WALK_NOISE_AMPLITUDE = 0.5 # Amplitude of the noise added to the wave when the hero walks
HERO_RUN_NOISE_AMPLITUDE = 0.75 # Amplitude of the noise added to the wave when the hero runs
HERO_SWIM_NOISE_AMPLITUDE = 0.5 # Amplitude of the noise added to the wave when the hero swims
HERO_JUMP_NOISE_AMPLITUDE = 1.5 # Amplitude of the noise added to the wave when the hero jumps
HERO_WISTLE_NOISE_AMPLITUDE = 2 # Amplitude of the noise added to the wave when the hero whistles

HERO_VOLUME_RUN = 0.2 # Sound factor for running 
HERO_FREQ_RUN = 10 # Time between two noise peaks when the hero runs (in frames)
HERO_VOLUME_WALK = 0.1 # Sound factor for walking 
HERO_FREQ_WALK = 18 # Time between two noise peaks when the hero walks (in frames)
HERO_VOLUME_SWIM = 0.1 # Sound factor for swimming 
HERO_FREQ_SWIM = 20 # Time between two noise peaks when the hero swims (in frames)
HERO_WHISTLE_VOLUME = 0.3 # Sound factor for whistling 
HERO_WISTHLE_EXTINCTION_TIME = 1300 # Time in milliseconds for the whistle sound to fade out after the hero stops whistling

# Constants for the orc
ORC_PATH_TO_IMAGES = "Images/orc/v1.2_(x1.5)/"
ORC_OFFSET_ANCHORING_Y = 15
ORC_HITBOX_WIDTH_UP_DOWN = 10
ORC_HITBOX_WIDTH_LEFT_RIGHT = 10
ORC_HITBOX_HEIGHT_UP_DOWN = 20
ORC_HITBOX_HEIGHT_LEFT_RIGHT = 10
ORC_GAUSSIAN_LIGHT_AREA_PARAMETERS = (150, 15, 10)

ORC_IDLE_SPEED = 0.1 # pixels per frame, speed at which the orc moves when idle (patrolling)
ORC_IDLE_PROBABILITY_CHANGE_DIRECTION = 3 # Probability for the orc to change direction when idle (%)
ORC_IDLE_RATIO = 25 # Number of frames for each image when idle
ORC_SOUND_HUNTING_INTENSITY_THRESHOLD = 0.05 # Threshold of the noise amplitude for the orc to start hunting the hero
ORC_SOUND_HUNTING_TIME_DERIVATIVE_THRESHOLD = 0.01 # Threshold of the derivative of the noise amplitude for the orc to start hunting the hero
ORC_HUNTING_SPEED = 4 # pixels per frame
ORC_HUNTING_RATIO = 5 # Number of frames for each image when hunting
ORC_RADIUS_OF_ACTION = 150 # pixels, radius in which the orc can move around its starting position
ORC_HUNTING_TIME = 30*FPS # frames, time during which the orc hunts the hero after detecting him
ORC_CATCH_DISTANCE = 30 # pixels, distance at which the orc catches the hero
ORC_CATCH_RATIO = 5 # Number of frames for each image when catching

ORC_VOLUME_HUNTING = 0.1 # Sound factor for the orc hunting
ORC_FREQ_HUNTING = 150 # Time between two noise peaks when the orc is hunting (in frames)
ORC_VOLUME_LAUGHING = 0.2 # Sound factor for the orc laughing


# Constants for the water creature
WATER_CREATURE_PATH_TO_IMAGES = "Images/water_monster/v0.1_(x1.5)/"
WATER_CREATURE_OFFSET_ANCHORING_Y = 0
WATER_CREATURE_HITBOX_WIDTH_UP_DOWN = 20
WATER_CREATURE_HITBOX_WIDTH_LEFT_RIGHT = 40
WATER_CREATURE_HITBOX_HEIGHT_UP_DOWN = 40
WATER_CREATURE_HITBOX_HEIGHT_LEFT_RIGHT = 20
WATER_CREATURE_HITBOX_MARGIN = 5
WATER_CREATURE_GAUSSIAN_LIGHT_AREA_PARAMETERS = (300, 50, 15)

WATER_CREATURE_APPEAR_RATIO = 5 # Number of frames for each image when appearing, same ratio for disappearing
WATER_CREATURE_SOUND_APPEAR_INTENSITY_THRESHOLD = 0.05 # Threshold of the noise amplitude for the water creature to start appearing
WATER_CREATURE_SOUND_APPEAR_TIME_DERIVATIVE_THRESHOLD = 0.01 # Threshold of the derivative of the noise amplitude for the water creature to start appearing
WATER_CREATURE_HUNTING_SPEED = 5 # pixels per frame
WATER_CREATURE_HUNTING_RATIO = 5 # Number of frames for each image when hunting
WATER_CREATURE_MAX_HUNTING_TIME = 30*FPS # frames, time during which the water creature hunts the hero after appearing
WATER_CREATURE_CATCH_DISTANCE = 30 # pixels, distance at which the water creature catches the hero
WATER_CREATURE_CATCH_RATIO = 4 # Number of frames for each image when catching
WATER_CREATURE_CATCH_SPEED = HERO_SWIM_SPEED

WATER_CREATURE_ATTACK_VOLUME = 0.5 # Sound factor for the water creature attack



if __name__ == "__main__":
    import main