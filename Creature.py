# Generic imports
import os
import pygame
from numpy import sqrt
import random
import heapq

# Local imports
from Constants import *
from Objects import Star


class Creature:

    id = 0

    def __init__(self, 
                 window,
                 BoardGame, 
                 Wave, 
                 Bridge,
                 x, y, 
                 name="Creature", 
                 offset_anchoring_y=0,
                 hitbox_width_up_down=None, hitbox_width_left_right=None, hitbox_height_up_down=None, hitbox_height_left_right=None,
                 path_to_images=None,
                 display_hitbox=False):
        """
            Initialize the creature with its position, name and path to its images.
            Parameters:
                - window : the window to draw the creature on
                - BoardGame : the board game object
                - Wave : the wave simulation object
                - x, y : coordinates of the bottom center of the creature (in pixels)
                - name : name of the creature (default: "Creature")
                - offset_anchoring_y : offset for the anchoring point of the creature (default: 0)
                - hitbox_width_up_down : width of the creature's hitbox when facing up or down (default: None)
                - hitbox_width_left_right : width of the creature's hitbox when facing left or right (default: None)
                - hitbox_height_up_down : height of the creature's hitbox when facing up or down (default: None)
                - hitbox_height_left_right : height of the creature's hitbox when facing left or right (default: None)
                - path_to_images : path to the folder containing the images of the creature (default: None)
                    In this folder there should be image for directions (up, down, left, right) and for states (stop, walk, swim, ...)
                    The images should be named as follows: "state_direction_nb.png", where state is either "stop" or "walk", direction is either "up", "down", "left" or "right" and nb is the number of the image (starting from 0).
                    Two images for shadows (shadow_up_down.png and shadow_left_right.png) can also be added in the folder to display shadows for the creature (optional). 
                - display_hitbox : whether to display the hitbox of the creature for testing purposes (default: False)
        """
        self.window = window
        self.name = name if not(Bridge.isRegistered(name)) else f"{name}_{Creature.id}"
        self.Wave = Wave
        self.Bridge = Bridge
        self.BoardGame = BoardGame
        self.hitbox_width_up_down = hitbox_width_up_down
        self.hitbox_width_left_right = hitbox_width_left_right
        self.hitbox_height_up_down = hitbox_height_up_down
        self.hitbox_height_left_right = hitbox_height_left_right
        self.offset_anchoring_y = offset_anchoring_y

        self.display_hitbox = display_hitbox
        self.shadow = False
        self.drawing_ratio = 1  # Displayed image change every 1/drawing_ratio frames

        self.path_to_images = path_to_images

        # Dictionary of the images of the creature : keys = "state_direction_nb", value = image
        self.images = {}

        # Current state, direction and speed of the creature and next image number to display (for animation)
        self.x = x  # Coordinates of the bottom center of the creature
        self.y = y
        self.z = BoardGame.getMacroAltitude(x, y)  # Altitude of the creature (in step, where one step corresponds to an half tile)
        self.vz = 0 # Vertical speed of the creature (in step per frame)
        self.state = "stop" if self.BoardGame.isWater(x, y) == False else "swimstop"
        self.direction = "down"
        self.image_number = 0

        assert isinstance(self.z, (int, float)), f"The altitude of the creature {self.name} should be a number, but got {type(self.z)} instead."
        assert self.path_to_images is None or os.path.exists(self.path_to_images), f"The path to the images of the creature {self.name} does not exist: {self.path_to_images}"

        # Load the images of the creature if the path to the images is provided
        if self.path_to_images is not None:
            for state in ["stop", "walk", "swimstop", "swimwalk", "attack", "appear", "disappear"]:
                for direction in ["up", "down", "left", "right"]:
                    nb = 0
                    while True:
                        image_path = self.path_to_images + f"{state}_{direction}_{nb}.png"
                        if not os.path.exists(image_path):
                            break
                        self.images[f"{state}_{direction}_{nb}"] = pygame.image.load(image_path)
                        nb += 1

            # Check if the shadows images are provided and load them if they are
            shadow_up_down_path = self.path_to_images + "shadow_up_down.png"
            shadow_left_right_path = self.path_to_images + "shadow_left_right.png"
            if os.path.exists(shadow_up_down_path) and os.path.exists(shadow_left_right_path):
                self.images["shadow_up_down"] = pygame.image.load(shadow_up_down_path)
                self.images["shadow_left_right"] = pygame.image.load(shadow_left_right_path)                
                self.shadow = True
                self.SHADOW_OFFSET_X = self.images["shadow_up_down"].get_width() // 2
                self.SHADOW_OFFSET_Y = self.images["shadow_up_down"].get_height()

        # Size of the creature
        self.WIDTH = self.images[list(self.images.keys())[0]].get_width() 
        self.HEIGHT = self.images[list(self.images.keys())[0]].get_height()

        self.y_to_draw = self.y - self.HEIGHT

        self.Bridge.register_creature(self)
        Creature.id += 1


    def clear():
        Creature.id = 0


    def draw(self, frame_count):
        if self.path_to_images is None:
            pygame.draw.circle(self.window, (255, 0, 0), (self.x, self.y), 10)
            return
        
        # Get altitudes
        ground_z = self.BoardGame.getMacroAltitude(self.x, self.y)
        jump_height = self.z - ground_z

        # If we are on the floor and state is "jump", we change it to "stop" to display the correct image
        if jump_height <= 0 and self.state == "jump":
            self.state = "stop"

        # Draw shadow (attached to ground)
        if self.shadow and self.BoardGame.isWater(self.x, self.y) == False: # No shadow if the creature is in water
            if self.direction in ["up", "down"]:
                base_shadow = self.images["shadow_up_down"]
            else:
                base_shadow = self.images["shadow_left_right"]
            
            shadow_pos_x = self.x - self.SHADOW_OFFSET_X
            shadow_pos_y = self.y - self.SHADOW_OFFSET_Y

            # Shadow shrinks when character is above ground
            if jump_height > 0:
                scale_factor = max(0.1, 1.0 - (jump_height * 0.3)) 
                new_width = int(base_shadow.get_width() * scale_factor)
                new_height = int(base_shadow.get_height() * scale_factor)
                
                if new_width > 0 and new_height > 0:
                    shadow_image = pygame.transform.scale(base_shadow, (new_width, new_height))
                    shadow_pos_x = self.x - (new_width // 2)
                    shadow_pos_y = self.y - self.SHADOW_OFFSET_Y + (base_shadow.get_height() - new_height)//2
                else:
                    shadow_image = None
            else:
                shadow_image = base_shadow

            if shadow_image:
                self.window.blit(shadow_image, (shadow_pos_x, shadow_pos_y))

        # Draw character at absolute altitude
        state = self.state
        if self.BoardGame.isWater(self.x, self.y) and self.z == self.BoardGame.getMacroAltitude(self.x, self.y):
            if state == "stop":
                state = "swimstop"
            elif state == "walk":
                state = "swimwalk"
        image_key = f"{state}_{self.direction}_{self.image_number}"
        if image_key not in self.images:
            self.image_number = 0
            image_key = f"{state}_{self.direction}_{self.image_number}"
        
        image = self.images[image_key]
        pos_x = self.x - self.WIDTH // 2
        self.getYToDraw()
        
        self.window.blit(image, (pos_x, self.y_to_draw))

        # Draw hitbox
        if self.display_hitbox:
            hitbox = self._get_feet_hitbox(self.x, self.y, self.direction)
            pygame.draw.rect(self.window, (0, 255, 0), hitbox, 1)
            pygame.draw.circle(self.window, (0, 0, 255), (self.x, self.y), 3)
        
        if frame_count % self.drawing_ratio == 0:
            self.image_number += 1


    def _get_feet_hitbox(self, x, y, direction):
        """
            Get a pygame.Rect representing the hitbox of the feet of the creature
        """
        if direction in ["up", "down"]:
            hitbox_width = self.hitbox_width_up_down
            hitbox_height = self.hitbox_height_up_down
        else:
            hitbox_width = self.hitbox_width_left_right
            hitbox_height = self.hitbox_height_left_right

        rect_x = x - (hitbox_width / 2)
        rect_y = y - hitbox_height

        return pygame.Rect(rect_x, rect_y, hitbox_width, hitbox_height)
    

    def _get_physical_z(self, x, y):
        """
            Get the physical altitude of the creature at the given coordinates (in pixels)
        """
        # Assure that the coordinates are within the bounds of the window
        x = max(0, min(WINDOW_WIDTH - 1, x))
        y = max(0, min(WINDOW_HEIGHT - 1, y))

        micro_alt = self.BoardGame.getMicroAltitude(x, y)
        macro_alt = self.BoardGame.getMacroAltitude(x, y)

        if micro_alt == float('inf'):
            if self.z >= macro_alt:
                return macro_alt - 1
            else:
                return float('inf')
        return micro_alt

    
    def _move(self, direction, speed):
        """
            Move the creature in the given direction with the given speed if it is possible (not blocked by an obstacle and not too low).
            Parameters:
                - direction : the direction to move in ("up", "down", "left" or "right")
                - speed : the speed of the movement (in pixels per frame)
            Returns:
                - True if the creature has moved, False otherwise
        """
        if speed == 0:
            return True

        self.direction = direction

        # Check if the creature can move in the given direction
        nx, ny = self.x, self.y
        if direction == "up":
            ny = max(0, self.y - speed)
        elif direction == "down":
            ny = min(WINDOW_HEIGHT - 1, self.y + speed)
        elif direction == "left":
            nx = max(0, self.x - speed)
        elif direction == "right":
            nx = min(WINDOW_WIDTH - 1, self.x + speed)

        futur_hitbox = self._get_feet_hitbox(nx, ny, direction)

        corners = []
        if direction == "up":
            corners = [futur_hitbox.topleft, futur_hitbox.topright]
        elif direction == "down":
            corners = [futur_hitbox.bottomleft, futur_hitbox.bottomright]
        elif direction == "left":
            corners = [futur_hitbox.topleft, futur_hitbox.bottomleft]
        elif direction == "right":
            corners = [futur_hitbox.topright, futur_hitbox.bottomright]

        # Check if the creature can move to the new position (not blocked by an obstacle and not too low)
        can_move = True
        for cx, cy in corners:
            target_z = self._get_physical_z(cx, cy)

            if self.z < target_z:
                can_move = False
                break
        
        if can_move:
            last_x, last_y = self.x, self.y
            self.x, self.y = nx, ny
            
            # If altitude changes, we update the y coordinate of the creature according to the altitude of the ground
            altitude_diff = self.BoardGame.getMacroAltitude(nx, ny) - self.BoardGame.getMacroAltitude(last_x, last_y)
            if altitude_diff < 0:
                if direction != "up": # If the creature is moving up, we don't want to change its y coordinate because it is jumping and we want to keep the jump height constant    
                    self.y -= int(altitude_diff * TILE_SIZE // 2)
                    self._jump(0.075) # Add a vertical speed boost when going down to make the movement more natural
                elif direction == "up" :
                    self._jump(0.01) # Add a smaller vertical speed boost when going up to make the movement more natural

            elif altitude_diff > 0:
                if direction != "down": # If the creature is moving down, we don't want to change its y coordinate because it is jumping and we want to keep the jump height constant    
                    self.y -= int(altitude_diff * TILE_SIZE // 2 )              
            return True
        return False            
    

    def _apply_gravity(self):
        # Apply gravity to the creature and update its altitude
        self.z += self.vz
        self.vz -= GRAVITY
        curr_micro_alt = self.BoardGame.getMicroAltitude(self.x, self.y)
        if self.z < curr_micro_alt:
            if curr_micro_alt != float('inf'):
                self.z = curr_micro_alt
            else:
                self.z = self.BoardGame.getMacroAltitude(self.x, self.y)


    def _jump(self, value=HERO_JUMP_SPEED):
        # Make the creature jump and update its altitude
        self.vz = value


    def _stop(self):
        # Stop the creature and update its state
        self.state = "stop"

    
    def _walk(self, speed=HERO_WALK_SPEED):
        # Start the creature and update its state
        self.state = "walk"
        self.speed = speed

    
    def _attack(self):
        # Make the creature attack and update its state
        self.state = "attack"


    def receiveEvent(self, event, sender_name=None):
        """
            Method to receive events from other creatures through the bridge
        """
        raise NotImplementedError()


    def getYToDraw(self):
        ground_z = self.BoardGame.getMacroAltitude(self.x, self.y)
        jump_height = self.z - ground_z
        self.y_to_draw = self.y - self.HEIGHT - int(jump_height * VERTICAL_OFFSET_COEFFICIENT) 
        if self.direction == "up":
            self.y_to_draw += self.offset_anchoring_y
        return self.y_to_draw


    def update(self, keys, frame_count):
        raise NotImplementedError()
    

    def isInCatchState(self):
        raise NotImplementedError()


class MainCharacter(Creature):

    def __init__(self, window, board_game, wave, bridge, x, y, name="MainCharacter", display_hitbox=False):
        super().__init__(window, 
                         board_game, 
                         wave, 
                         bridge,
                         x, y, 
                         name,
                         offset_anchoring_y=HERO_OFFSET_ANCHORING_Y,
                         hitbox_width_up_down=HERO_HITBOX_WIDTH_UP_DOWN, hitbox_width_left_right=HERO_HITBOX_WIDTH_LEFT_RIGHT, hitbox_height_up_down=HERO_HITBOX_HEIGHT_UP_DOWN, hitbox_height_left_right=HERO_HITBOX_HEIGHT_LEFT_RIGHT,
                         path_to_images = HERO_PATH_TO_IMAGES,
                         display_hitbox=display_hitbox)

        self.speed = HERO_WALK_SPEED
        self.health = 6

        if wave is not None:
            # Add light areas to the wave simulation for the main character
            self.SIZE_LIGHT_AREA, a, sigma = HERO_GAUSSIAN_LIGHT_AREA_PARAMETERS
            wave.addGaussianLightArea(self.SIZE_LIGHT_AREA, a, sigma, self.name + "Light")

        # Download the image of the health bar
        self.health_bar_images = []
        for i in range(7):
            image_path = HEALTH_BAR_PATH_TO_IMAGES + f"/{i}.png"
            self.health_bar_images.append(pygame.image.load(image_path))

        # Download the image of the star bar
        self.empty_star_image = pygame.image.load(PATH_TO_EMPTY_STAR_IMAGE).convert_alpha()
        self.star_image = pygame.image.load(PATH_TO_STAR_IMAGE).convert_alpha()
        self.nb_stars_collected = 0
        self.nb_stars_total = None
        self.STAR_HEIGHT = self.star_image.get_height()
        self.STAR_SPACING = 10

        self.MAX_ALTITUDE = max(self.BoardGame.getListOfAltitudes())

        # Sounds
        self.sounds = {}
        self.sounds["step"] = pygame.mixer.Sound(PATH_TO_SOUNDS + "step.ogg")
 
    
    def update(self, keys, frame_count):

        last_x, last_y = self.x, self.y
        last_altitude = self.BoardGame.getMacroAltitude(last_x, last_y)
            
        noise_value = 0

        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or self.BoardGame.isWater(self.x, self.y):
            self._walk(HERO_SWIM_SPEED)
            self.drawing_ratio = HERO_SWIM_RATIO
        else:
            self._walk(HERO_RUN_SPEED)
            self.drawing_ratio = HERO_WALK_RATIO

        if keys[pygame.K_UP]:
            self._move("up", self.speed)
            noise_value += HERO_WALK_NOISE_AMPLITUDE if self.speed == HERO_WALK_SPEED else HERO_RUN_NOISE_AMPLITUDE
        elif keys[pygame.K_DOWN]:
            self._move("down", self.speed)
            noise_value += HERO_WALK_NOISE_AMPLITUDE if self.speed == HERO_WALK_SPEED else HERO_RUN_NOISE_AMPLITUDE
        elif keys[pygame.K_LEFT]:
            self._move("left", self.speed)
            noise_value += HERO_WALK_NOISE_AMPLITUDE if self.speed == HERO_WALK_SPEED else HERO_RUN_NOISE_AMPLITUDE
        elif keys[pygame.K_RIGHT]:
            self._move("right", self.speed)
            noise_value += HERO_WALK_NOISE_AMPLITUDE if self.speed == HERO_WALK_SPEED else HERO_RUN_NOISE_AMPLITUDE
        else:
            self._stop()

        if keys[pygame.K_s]:
            if self.BoardGame.getMicroAltitude(self.x, self.y) == self.z:
                self._jump() 
                noise_value += HERO_JUMP_NOISE_AMPLITUDE
                
        self._apply_gravity()

        if keys[pygame.K_SPACE]:
            noise_value += HERO_WISTLE_NOISE_AMPLITUDE

        # Debug
        if keys[pygame.K_1]:
            star_name = Star.stars_list[0]  # Get the first star
            star_x, star_y, _ = self.Bridge.getPosition(star_name)
            self.Bridge.sendEvent(star_name, "collected", self.name)
            self.nb_stars_collected += 1
            if self.nb_stars_collected == self.nb_stars_total:
                    self.Bridge.gameOver({"total_nb_stars": self.nb_stars_total, "collected_nb_stars": self.nb_stars_collected, "final_state": "win"})
            pygame.time.wait(200) # Wait a bit to avoid collecting all the stars at once when pressing 1

        # Add noise to the wave simulation 
        self.Wave.setPixel(self.x, self.y - self.HEIGHT // 2, min(int(self.z), self.MAX_ALTITUDE), noise_value)

        # Update the light area of the main character in the wave simulation
        if self.Wave is not None:
            source_x = self.x
            source_y = self.y - self.HEIGHT // 2
            self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)

        # Check the star position and update the number of stars collected
        for star_name in Star.stars_list:
            star_x, star_y, _ = self.Bridge.getPosition(star_name)
            if abs(self.x - star_x) < TILE_SIZE//2 and abs(self.y - star_y) < TILE_SIZE//2:
                self.Bridge.sendEvent(star_name, "collected", self.name)
                self.nb_stars_collected += 1

                if self.nb_stars_collected == self.nb_stars_total:
                    self.Bridge.gameOver({"total_nb_stars": self.nb_stars_total, "collected_nb_stars": self.nb_stars_collected, "final_state": "win"})


    def receiveEvent(self, event, sender_name=None):
        if event == "caught_by_orc":
            self.health -= 1

        if event == "caught_by_water_creature":
            self.health -= 2
        
        if self.health <= 0:
            self.Bridge.gameOver({"total_nb_stars": self.nb_stars_total, "collected_nb_stars": self.nb_stars_collected, "final_state": "lose"})


    def drawInfo(self, frame_count):

        # Draw health bar
        health_bar_image = self.health_bar_images[self.health]
        self.window.blit(health_bar_image, (10, 10))

        # Draw star bar
        if self.nb_stars_total is None:
            self.nb_stars_total = self.Bridge.getNbStars()
            self.STAR_BAR_POSITION = (WINDOW_WIDTH - self.STAR_HEIGHT * self.nb_stars_total - self.STAR_SPACING * (self.nb_stars_total - 1) - 10, 10)

        for i in range(self.nb_stars_total):
            if i < self.nb_stars_collected:
                star_image = self.star_image
            else:
                star_image = self.empty_star_image
            pos_x = self.STAR_BAR_POSITION[0] + i * (self.STAR_HEIGHT + self.STAR_SPACING)
            pos_y = self.STAR_BAR_POSITION[1]
            self.window.blit(star_image, (pos_x, pos_y))        


    def isInCatchState(self):
        return False


class Orc(Creature):
    """
        A fast ennemy creature but that remains in a small area and doesn't jump
    """

    def __init__(self, window, board_game, wave, bridge, x, y, name="Orc", display_hitbox=False):
        super().__init__(window, 
                         board_game, 
                         wave, 
                         bridge,
                         x, y, 
                         name,
                         offset_anchoring_y=ORC_OFFSET_ANCHORING_Y,
                         hitbox_width_up_down=ORC_HITBOX_WIDTH_UP_DOWN, hitbox_width_left_right=ORC_HITBOX_WIDTH_LEFT_RIGHT, hitbox_height_up_down=ORC_HITBOX_HEIGHT_UP_DOWN, hitbox_height_left_right=ORC_HITBOX_HEIGHT_LEFT_RIGHT,
                         path_to_images = ORC_PATH_TO_IMAGES,
                         display_hitbox=display_hitbox)
        self.start_x = x
        self.start_y = y

        assert not self.BoardGame.isWater(x, y), f"The orc {self.name} cannot be initialized in water at position ({x}, {y}). Please choose a position on land."

        self.FSM_state = "idle"

        # Hunting and flee states
        self.target_direction_x = 0
        self.target_direction_y = 0
        self.last_direction = self.direction
        self.start_time_hunting = None
        
        # Catch state
        self.start_time_catch = None

        # Add light areas to the wave simulation for the orc
        if wave is not None:
            self.SIZE_LIGHT_AREA, a, sigma = ORC_GAUSSIAN_LIGHT_AREA_PARAMETERS
            wave.addGaussianLightArea(self.SIZE_LIGHT_AREA, a, sigma, self.name + "Light")
            wave.setLightAreaPosition(self.name + "Light", None, None) 


    def _move(self, direction, speed):
        
        nx, ny = self.x, self.y
        if direction == "up":
            ny = max(self.HEIGHT, self.y - speed)
        elif direction == "down":
            ny = min(WINDOW_HEIGHT - 1, self.y + speed)
        elif direction == "left":
            nx = max(self.WIDTH//2, self.x - speed)
        elif direction == "right":
            nx = min(WINDOW_WIDTH - self.WIDTH//2, self.x + speed)

        if self.BoardGame.getMacroAltitude(nx, ny) != self.BoardGame.getMacroAltitude(self.x, self.y):
            return False
        
        if self.ManhattanDistanceToStart(nx, ny) > ORC_RADIUS_OF_ACTION:
            return False
        
        result = super()._move(direction, speed)

        if result:
            self.last_direction = direction
        return result


    def ManhattanDistanceToStart(self, x, y):
        """ 
            Calculate the Manhattan distance from the current position to the starting position
            I use this distance to have a square area (circle in Manhattan distance)
        """
        return abs(x - self.start_x) + abs(y - self.start_y)
        

    def update(self, keys, frame_count):
        """
            FSM of the orc :
                - idle : the orc moves randomly around its starting position.
                    - if sound is detected, goes to hunting state
                - hunting : the orc moves towards the main character to try to catch him. The orc follows the direction of the sound.
                    - if time hunting exceeds ORC_HUNTING_TIME, goes back to idle state
                    - if the boundary of the area is reached, goes back to idle state
                    - if approaches the main character at a distance less than 20 pixels, goes in catch state
                - catch : the orc catches the main character 
                    - When done, goes to flee state
                - flee : the orc flees and tries to go back to its starting position
                    - if it reaches its starting position, goes back to idle state
        """
        if self.FSM_state == "idle":
            speed = ORC_IDLE_SPEED
            self.drawing_ratio = ORC_IDLE_RATIO

            if ORC_IDLE_SPEED < 1:
                if frame_count % int(1/ORC_IDLE_SPEED) == 0:
                    speed = 1
                else:
                    speed = 0

            allowed_directions = [self.direction]

            # Change randomly direction
            if random.randint(0, 100) < ORC_IDLE_PROBABILITY_CHANGE_DIRECTION:
                allowed_directions[0] = random.choice([d for d in ["up", "down", "left", "right"] if d != self.direction])
            
            # Add other direction in case the orc is blocked in the current direction
            for d in ["up", "left", "down", "right"]:
                if allowed_directions[0] != d:
                    allowed_directions.append(d)

            # Try to move in the allowed directions
            for d in allowed_directions:
                if self._move(d, speed):
                    break
            
            # Sound detection
            if self.Wave is not None:
                sound_sources = self.Wave.getIntensity(self.x, self.y, self.z)
                if sound_sources >= ORC_SOUND_HUNTING_INTENSITY_THRESHOLD and self.Wave.getTimeDerivative(self.x, self.y, self.z) >= ORC_SOUND_HUNTING_TIME_DERIVATIVE_THRESHOLD:
                    dx, dy = self.Wave.getEnergyFlow(self.x, self.y, self.z)
                    norm = sqrt(dx**2 + dy**2)
                    if norm > 0:
                        self.target_direction_x = dx/norm 
                        self.target_direction_y = dy/norm
                        self.FSM_state = "hunting"
                        self.start_time_hunting = frame_count    

            if self.Wave is not None:
                self.Wave.setLightAreaPosition(self.name + "Light", None, None) 

        elif self.FSM_state == "hunting":
            self.drawing_ratio = ORC_HUNTING_RATIO

            if self.Wave.getIntensity(self.x, self.y, self.z) >= ORC_SOUND_HUNTING_INTENSITY_THRESHOLD:
                dx, dy = self.Wave.getEnergyFlow(self.x, self.y, self.z)
                norm = sqrt(dx**2 + dy**2)
                if norm > 0:
                    # Filter to avoid noise
                    self.target_direction_x = 0.9*self.target_direction_x + 0.1*dx/norm
                    self.target_direction_y = 0.9*self.target_direction_y + 0.1*dy/norm

            # Move in the direction of the main character
            """
            direction_to_follow = []
            if abs(self.target_direction_x) > abs(self.target_direction_y):
                if self.target_direction_x > 0:
                    direction_to_follow = ["right"]
                    if self.target_direction_y > 0:
                        direction_to_follow.append("down")
                    else:
                        direction_to_follow.append("up")
                else:
                    direction_to_follow = ["left"]
                    if self.target_direction_y > 0:
                        direction_to_follow.append("down")
                    else:
                        direction_to_follow.append("up")
            else:
                if self.target_direction_y > 0:
                    direction_to_follow = ["down"]
                    if self.target_direction_x > 0:
                        direction_to_follow.append("right")
                    else:
                        direction_to_follow.append("left")
                else:
                    direction_to_follow = ["up"]
                    if self.target_direction_x > 0:
                        direction_to_follow.append("right")
                    else:
                        direction_to_follow.append("left")
            
            for d in random.sample(["up", "down", "left", "right"], 4):
                # We don't want go backwards
                if d not in direction_to_follow and d != self.OPPOSITES[self.last_direction]:
                    direction_to_follow.append(d)
            """

            scores = {}
            for d, (vx, vy) in DIRS_VEC.items():
                # Scalar product: we want to align with the direction
                score = vx * self.target_direction_x + vy * self.target_direction_y
                
                # We want to keep the same direction
                if d == self.last_direction:
                    score += 0.2  
                    
                # We don't want to go backwards
                if self.last_direction and d == OPPOSITES[self.last_direction]:
                    score -= 1
                    
                scores[d] = score

            direction_to_follow = sorted(scores, key=scores.get, reverse=True)

            for d in direction_to_follow:
                if self._move(d, ORC_HUNTING_SPEED):
                    self.last_direction = d
                    break

            # Update the light area of the orc in the wave simulation
            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)
            
            # If the orc has been hunting for too long, it goes back to idle state
            if frame_count - self.start_time_hunting > ORC_HUNTING_TIME:
                self.FSM_state = "idle"
                return
            
            # If the orc has reached the boundary of the area, it goes back to idle state
            if self.ManhattanDistanceToStart(self.x, self.y) >= ORC_RADIUS_OF_ACTION*0.95:
                self.FSM_state = "idle"
                return
            
            # If the orc is close enough to the main character, it goes in catch state
            main_character_pos = self.Bridge.getPosition("MainCharacter")
            dist = sqrt((self.x - main_character_pos[0])**2 + (self.y - main_character_pos[1])**2)
            if dist < ORC_CATCH_DISTANCE and main_character_pos[2] <= self.z:
                self.FSM_state = "catch"
                self.start_time_catch = frame_count
                self._attack()
                self.image_number = 0
                self.drawing_ratio = ORC_CATCH_RATIO

        elif self.FSM_state == "catch":

            if frame_count - self.start_time_catch == ORC_CATCH_RATIO*3: 
                main_character_pos = self.Bridge.getPosition("MainCharacter")
                dist = sqrt((self.x - main_character_pos[0])**2 + (self.y - main_character_pos[1])**2)
                if dist < ORC_CATCH_DISTANCE*2 and main_character_pos[2] <= self.z:
                    self.Bridge.sendEvent("MainCharacter", "caught_by_orc", sender_name=self.name)
            
            if frame_count - self.start_time_catch > ORC_CATCH_RATIO*6: # Stay in catch state for 1 second
                self.FSM_state = "flee"
                self._walk()

            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)

        elif self.FSM_state == "flee":

            self.target_direction_x = self.start_x - self.x
            self.target_direction_y = self.start_y - self.y
            
            scores = {}
            for d, (vx, vy) in DIRS_VEC.items():
                # Scalar product: we want to align with the direction
                score = vx * self.target_direction_x + vy * self.target_direction_y
                
                # We want to keep the same direction
                if d == self.last_direction:
                    score += 0.2  
                    
                # We don't want to go backwards
                if self.last_direction and d == OPPOSITES[self.last_direction]:
                    score -= 1
                    
                scores[d] = score

            direction_to_follow = sorted(scores, key=scores.get, reverse=True)

            for d in direction_to_follow:
                if self._move(d, ORC_HUNTING_SPEED):
                    self.last_direction = d
                    break

            # If the orc has reached its starting position, it goes back to idle state
            if self.ManhattanDistanceToStart(self.x, self.y) < 10:
                self.FSM_state = "idle"

            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)
        

    def isInCatchState(self):
        return self.FSM_state == "catch"
            
            
class WaterCreature(Creature):
    """
        A creature that can only move in water 
    """

    def __init__(self, window, board_game, wave, bridge, x, y, name="WaterCreature", display_hitbox=False):
        super().__init__(window, 
                         board_game, 
                         wave, 
                         bridge,
                         x, y, 
                         name,
                         offset_anchoring_y=WATER_CREATURE_OFFSET_ANCHORING_Y,
                         hitbox_width_up_down=WATER_CREATURE_HITBOX_WIDTH_UP_DOWN, hitbox_width_left_right=WATER_CREATURE_HITBOX_WIDTH_LEFT_RIGHT, hitbox_height_up_down=WATER_CREATURE_HITBOX_HEIGHT_UP_DOWN, hitbox_height_left_right=WATER_CREATURE_HITBOX_HEIGHT_LEFT_RIGHT,
                         path_to_images = WATER_CREATURE_PATH_TO_IMAGES,
                         display_hitbox=display_hitbox)
        
        self.FSM_state = "waiting"
        self.start_time_appear = None
        self.start_time_hunting = None
        self.since_last_target_change = 0
        self.start_time_disappear = None
        self.path = []
        self.target_direction_x = 0
        self.target_direction_y = 0
        self.last_direction = self.direction
        self.WATER_CREATURE_HUNTING_SPEED = WATER_CREATURE_HUNTING_SPEED + random.randint(-WATER_CREATURE_HUNTING_SPEED//2, WATER_CREATURE_HUNTING_SPEED//2)

        self.NB_APPEAR_IMAGES = 5
        self.NB_CATCH_IMAGES = 5

        if self.Wave is not None:
            # Add light areas to the wave simulation for the water creature
            self.SIZE_LIGHT_AREA, a, sigma = WATER_CREATURE_GAUSSIAN_LIGHT_AREA_PARAMETERS
            wave.addGaussianLightArea(self.SIZE_LIGHT_AREA, a, sigma, self.name + "Light")
            wave.setLightAreaPosition(self.name + "Light", None, None)
    

    def _appear(self):
        # Make the creature appear
        self.state = "appear"
        self.image_number = 0


    def _disappear(self):
        # Make the creature disappear
        self.state = "disappear"
        self.image_number = 0


    def _get_feet_hitbox(self, x, y, direction):
        """
            Get the hitbox of the creature at the given coordinates and direction, but with a security margin to avoid getting stuck in obstacles.
        """
        if direction in ["up", "down"]:
            hitbox_width = self.hitbox_width_up_down + WATER_CREATURE_HITBOX_MARGIN
            hitbox_height = self.hitbox_height_up_down + WATER_CREATURE_HITBOX_MARGIN
        else:
            hitbox_width = self.hitbox_width_left_right + WATER_CREATURE_HITBOX_MARGIN
            hitbox_height = self.hitbox_height_left_right + WATER_CREATURE_HITBOX_MARGIN

        rect_x = x - (hitbox_width / 2)
        rect_y = y - hitbox_height

        # Assure the 4 corners are in the window
        if rect_x + hitbox_width > WINDOW_WIDTH:
            hitbox_width = WINDOW_WIDTH - rect_x
        if rect_x < 0:
            hitbox_width = hitbox_width + rect_x
            rect_x = 0
        if rect_y + hitbox_height > WINDOW_HEIGHT:
            hitbox_height = WINDOW_HEIGHT - rect_y
        if rect_y < 0:
            hitbox_height = hitbox_height + rect_y
            rect_y = 0 

        return pygame.Rect(rect_x, rect_y, hitbox_width, hitbox_height)
    

    def update(self, keys, frame_count):
        """
            FSM of the water creature :
                - waiting : the creature is waiting underwater and doesn't move. 
                    - if the sound is detected, goes to appear state
                - appear : the creature appears at the surface of the water 
                    - when done, goes to hunting state
                - hunting : the creature find the shortest path to the main character and follows it
                    - if the sound is lost for a certain time, goes to disappear state
                    - if close enough to the main character, goes to catch state
                - catch : the creature catches the main character
                    - When done, goes to disappear state
                - disappear : the creature disappears and goes back underwater
                    - when done, goes back to waiting state
        """

        if self.FSM_state == "waiting":
            if self.Wave is not None:
                sound_sources = self.Wave.getIntensity(self.x, self.y, self.z)
                if sound_sources >= WATER_CREATURE_SOUND_APPEAR_INTENSITY_THRESHOLD and self.Wave.getTimeDerivative(self.x, self.y) >= WATER_CREATURE_SOUND_APPEAR_TIME_DERIVATIVE_THRESHOLD:
                    self.FSM_state = "appear"
                    self.drawing_ratio = WATER_CREATURE_APPEAR_RATIO
                    self.start_time_appear = frame_count
                    self._appear()
                
                self.Wave.setLightAreaPosition(self.name + "Light", None, None)

        elif self.FSM_state == "appear":
            if frame_count - self.start_time_appear > WATER_CREATURE_APPEAR_RATIO * self.NB_APPEAR_IMAGES:
                self.FSM_state = "hunting"
                self.start_time_hunting = frame_count
                self.drawing_ratio = WATER_CREATURE_HUNTING_RATIO
                self._walk(self.WATER_CREATURE_HUNTING_SPEED)

            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)

        elif self.FSM_state == "hunting":

            #calculate the shortest path (BFS) to the main character every 30 frames
            if (frame_count % 30 == 0 or frame_count - self.start_time_hunting < 30) and self.Bridge.getPosition("MainCharacter")[2] <= self.z: 
                main_character_pos = self.Bridge.getPosition("MainCharacter")
                path = self.BoardGame.getShortestPath(self.x, self.y, main_character_pos[0], main_character_pos[1], in_water=True)
                if path is not None:
                    # Convert in pixel coordinates
                    for i in range(len(path)):
                        path[i] = (path[i][0]*TILE_SIZE + TILE_SIZE//2, path[i][1]*TILE_SIZE + TILE_SIZE//2)
                    self.path = path
                    self.since_last_target_change = 0

            # Clean the path
            if len(self.path) > 0:
                dist_0 = sqrt((self.path[0][0] - self.x)**2 + (self.path[0][1] - self.y)**2)
                
                # We are on the tile
                if dist_0 < (TILE_SIZE // 2):
                    self.path.pop(0)
                    self.since_last_target_change = 0
                
                elif len(self.path) > 1: # We are closer to the next tile
                    dist_1 = sqrt((self.path[1][0] - self.x)**2 + (self.path[1][1] - self.y)**2)
                    if dist_1 < dist_0:
                        self.path.pop(0)
                        self.since_last_target_change = 0
                
            # Follow the path to the main character with the same logic as the orc
            if len(self.path) > 0 and self.since_last_target_change < 15:
                # Update the target direction based on the next tile in the path
                dist = sqrt((self.path[0][0] - self.x)**2 + (self.path[0][1] - self.y)**2)
                if dist > 0:
                    self.target_direction_x = (self.path[0][0] - self.x) / dist
                    self.target_direction_y = (self.path[0][1] - self.y) / dist
                else:
                    self.target_direction_x = 0
                    self.target_direction_y = 0

                scores = {}
                for d, (vx, vy) in DIRS_VEC.items():
                    # Scalar product: we want to align with the direction
                    score = vx * self.target_direction_x + vy * self.target_direction_y
                    
                    # We want to keep the same direction
                    if d == self.last_direction:
                        score += 0.2  
                        
                    # We don't want to go backwards
                    if self.last_direction and d == OPPOSITES[self.last_direction]:
                        score -= 1
                        
                    scores[d] = score

                direction_to_follow = sorted(scores, key=scores.get, reverse=True)

                for d in direction_to_follow:
                    if self._move(d, self.WATER_CREATURE_HUNTING_SPEED):
                        self.last_direction = d
                        break  

                self.since_last_target_change += 1    

            if frame_count - self.start_time_hunting > WATER_CREATURE_MAX_HUNTING_TIME:
                self.FSM_state = "disappear"
                self.start_time_disappear = frame_count 
                self.drawing_ratio = WATER_CREATURE_APPEAR_RATIO
                self._disappear() 

            hero_x, hero_y, hero_z = self.Bridge.getPosition("MainCharacter")
            dist = sqrt((self.x - hero_x)**2 + (self.y - hero_y)**2)
            if dist < WATER_CREATURE_CATCH_DISTANCE and hero_z <= self.z:
                self.FSM_state = "catch"
                self.start_time_catch = frame_count
                self._attack()
                self.image_number = 0
                self.drawing_ratio = WATER_CREATURE_CATCH_RATIO

            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)

        elif self.FSM_state == "catch":

            main_character_pos = self.Bridge.getPosition("MainCharacter")
            self.target_direction_x = main_character_pos[0] - self.x
            self.target_direction_y = main_character_pos[1] - self.y

            scores = {}
            for d, (vx, vy) in DIRS_VEC.items():
                # Scalar product: we want to align with the direction
                score = vx * self.target_direction_x + vy * self.target_direction_y
                
                # We want to keep the same direction
                if d == self.last_direction:
                    score += 0.2  
                    
                # We don't want to go backwards
                if self.last_direction and d == OPPOSITES[self.last_direction]:
                    score -= 1
                    
                scores[d] = score

            direction_to_follow = sorted(scores, key=scores.get, reverse=True)

            for d in direction_to_follow:
                if self._move(d, WATER_CREATURE_CATCH_SPEED):
                    self.last_direction = d
                    break


            if frame_count - self.start_time_catch == WATER_CREATURE_CATCH_RATIO*self.NB_CATCH_IMAGES:
                main_character_pos = self.Bridge.getPosition("MainCharacter")
                dist = sqrt((self.x - main_character_pos[0])**2 + (self.y - main_character_pos[1])**2)
                if dist < WATER_CREATURE_CATCH_DISTANCE*2 and main_character_pos[2] <= self.z:
                    self.Bridge.sendEvent("MainCharacter", "caught_by_water_creature", sender_name=self.name)
                self.FSM_state = "disappear"
                self.start_time_disappear = frame_count
                self.drawing_ratio = WATER_CREATURE_APPEAR_RATIO
                self._disappear()

            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)


        elif self.FSM_state == "disappear":
            if frame_count - self.start_time_disappear > WATER_CREATURE_APPEAR_RATIO * self.NB_APPEAR_IMAGES:
                self.FSM_state = "waiting"
                self._stop()

            if self.Wave is not None:
                source_x = self.x
                source_y = self.y - self.HEIGHT // 2
                self.Wave.setLightAreaPosition(self.name + "Light", source_x-self.SIZE_LIGHT_AREA//2, source_y-self.SIZE_LIGHT_AREA//2)
            

    def isInCatchState(self):
        return self.FSM_state == "catch"
            

# Link between the classes and their names
# Useful in Game.py
CREATURE_CLASSES = {
    "MainCharacter": MainCharacter,
    "Orc": Orc,
    "WaterCreature": WaterCreature
}







if __name__ == "__main__":

    from old.Game import Game

    # Initialize pygame
    pygame.init()

    # Create the window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Echo-step")

    # Create the game
    game = Game(window, debug=True)

    # Quit pygame
    pygame.quit()


"""
if __name__ == "__main__":
    from BoardGame import BoardGame

    # Initialize Pygame
    pygame.init()

    # Create the window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # Clock to control the frame rate
    clock = pygame.time.Clock()

    # Create the board game
    board_game = BoardGame(window)

    # Bridge
    bridge = Bridge()

    # Create wave simulation
    wave = WaveManager(window, board_game, offset_transparency=50)

    # Add Main Character
    main_character = MainCharacter(window, board_game, wave, bridge, WINDOW_WIDTH // 2 -10, WINDOW_HEIGHT // 2 - 10)

    # Add Orc
    x_orc = [164]#[WINDOW_WIDTH // 2 - 100, WINDOW_WIDTH // 2 - 120, WINDOW_WIDTH // 2 - 120, WINDOW_WIDTH // 2 - 100, WINDOW_WIDTH // 2 + 50]
    y_orc = [630]#[WINDOW_HEIGHT // 2 + 200, WINDOW_HEIGHT // 2 + 220, WINDOW_HEIGHT // 2 + 200, WINDOW_HEIGHT // 2 + 220, WINDOW_HEIGHT // 2 + 100]
    Orcs = []
    for i in range(len(x_orc)):
        orc = Orc(window, board_game, wave, bridge, x_orc[i], y_orc[i], display_hitbox=False)
        Orcs.append(orc)

    # Add water creature
    water_creature = WaterCreature(window, board_game, wave, bridge, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 40, display_hitbox=False)

    # Main loop
    running = True
    frame_count = 0
    while not(bridge.isGameOver()) and running:

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update the main character
        keys = pygame.key.get_pressed()
        main_character.update(keys, frame_count)
        
        # Update the orcs
        for orc in Orcs:
            orc.update(keys, frame_count)

        # Update the water creature
        water_creature.update(keys, frame_count)

        # Update wave simulation
        wave.update()

        # Fill the window with white
        window.fill((255, 255, 255))

        # Draw the board game
        board_game.draw()

        # Draw the main character
        main_character.draw(frame_count)

        # Draw the orcs
        for orc in Orcs:
            orc.draw(frame_count)

        # Draw the water creature
        water_creature.draw(frame_count)

        # Draw the wave simulation with light areas
        wave.draw()

        # Add info
        main_character.drawInfo(frame_count)              

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(FPS)

        frame_count += 1
"""