# Wave simulation using the d'Alembert method with damping
# Do not use !!!! Use the WaveManager file with its one Wave class instead


# Generic imports
import pygame
import numpy as np

# Local imports
from Constants import *


class Wave:

    """
        Class representing a wave simulation using the d'Alembert method with damping.
    """

    def __init__(self, window):
        """
            Initializes the wave simulation with given grid dimensions.
            Parameters:
                - window: Pygame window for visualization.
        """
        # Parameters for the wave simulation
        self.n_X = (WINDOW_WIDTH // RESIZE_FACTOR) + 2 * BS 
        self.n_Y = (WINDOW_HEIGHT // RESIZE_FACTOR) + 2 * BS
        self.COEFF1 = (C*DT/DX)**2 # Coefficient for the wave update formula
        self.COEFF2 = ALPHA * DT       # Coefficient for the damping term
        self.COEFF3 = BOUNDARY_DAMPING * DT       # Coefficient for the boundary condition (ABC)

        # Initialize wave amplitude arrays
        self.u = np.zeros((self.n_X, self.n_Y))  # Current wave amplitude
        self.p = np.zeros((self.n_X, self.n_Y))  # Previous wave amplitude
        self.f = np.zeros((self.n_X, self.n_Y))  # Future wave amplitude

        # Obstacles
        self.obstacles = {}  # Dictionary to store obstacles

        # Mask to indicate where the wave can propagate (True) or is blocked by an obstacle (False)
        # The permanent mask is always aplied 
        # Other masks can be keep in memory and applied or removed when needed
        self.obstacles_masks = {"permanent": np.ones((self.n_X, self.n_Y), dtype=bool)}  
        self.current_mask_name = None

        # Boundaries
        self.boundaries_mask = np.zeros((self.n_X, self.n_Y), dtype=bool)  # Mask for boundaries (False for interior, True for boundaries)
        self.boundaries_mask[:BS, :] = True  # Left boundary
        self.boundaries_mask[-BS:, :] = True  # Right boundary
        self.boundaries_mask[:, :BS] = True  # Top boundary
        self.boundaries_mask[:, -BS:] = True  # Bottom boundary

        # Light area (not a wave, just a light area)
        self.light_areas = {}  # Dictionary to store light areas, format: {name: mask} where mask is a 2D np.array(uint8), the mask is substracted from the image
        self.light_areas_position = {}  # Position of the light area (x, y) in the window, used for visualization

        # Pygame
        self.window = window  # Pygame window for visualization

        # Other
        self.time = 0.0  # Simulation time


    def setPixel(self, x, y, value=1.0):
        """
            Sets the amplitude of the wave at a specific pixel.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
                - value (float): Amplitude value to set at the pixel.
        """
        x = (x // RESIZE_FACTOR) + BS  # Convert window coordinates to simulation grid coordinates
        y = (y // RESIZE_FACTOR) + BS
        if 0 <= x < self.n_X and 0 <= y < self.n_Y:
            self.u[x, y] = value


    def addToPixel(self, x, y, value):
        """
            Adds a value to the amplitude of the wave at a specific pixel.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
                - value (float): Amplitude value to add at the pixel.
        """
        x = (x // RESIZE_FACTOR) + BS  
        y = (y // RESIZE_FACTOR) + BS
        if 0 <= x < self.n_X and 0 <= y < self.n_Y:
            self.u[x, y] += value


    def addMask(self, mask_name):
        """
            Adds a mask to the wave simulation, allowing to apply it later to block wave propagation in specific areas.
            Parameters:
                - mask_name (str): Name of the mask to add.
        """
        if mask_name not in self.obstacles_masks:
            self.obstacles_masks[mask_name] = np.ones((self.n_X, self.n_Y), dtype=bool)

    
    def removeMask(self, mask_name):
        """
            Removes a mask from the wave simulation.
            Parameters:
                - mask_name (str): Name of the mask to remove.
        """
        if mask_name in self.obstacles_masks:
            del self.obstacles_masks[mask_name]
            if self.current_mask_name == mask_name:
                self.current_mask_name = None  # Unset the current mask if it was the one removed

    
    def applyMask(self, mask_name):
        """
            Applies a mask to the wave simulation, blocking wave propagation in the areas defined by the mask.
            Parameters:
                - mask_name (str): Name of the mask to apply.
        """
        if mask_name in self.obstacles_masks:
            self.current_mask_name = mask_name
        elif mask_name is None:
            self.current_mask_name = None  # Unset the current mask to apply only the permanent mask
        else:
            raise ValueError(f"Mask '{mask_name}' does not exist. Please add it before applying.")
        

    def copyMask(self, mask_name_to_copy, mask_name):
        """
            Copies an existing mask to a new mask name.
            Parameters:
                - mask_name_to_copy (str): Name of the existing mask to copy.
                - mask_name (str): Name of the new mask to create as a copy.
        """
        if mask_name_to_copy in self.obstacles_masks:
            self.obstacles_masks[mask_name] = self.obstacles_masks[mask_name_to_copy].copy()
        else:
            raise ValueError(f"Mask '{mask_name_to_copy}' does not exist. Please add it before copying.")


    def addRandomObstacle(self, obst, name, mask_name=None):
        """
            Adds a random obstacle to the wave simulation.
            Parameters:
                - obst (list of tuples): List of (x, y) coordinates (in the window) for the obstacle.
                - name (str): Name of the obstacle.
                - mask_name (str): Name of the mask to apply to the obstacle, if None we apply the permanent mask
        """
        scaled_obst = []
        for x, y in obst:
            x = (x // RESIZE_FACTOR) + BS
            y = (y // RESIZE_FACTOR) + BS
            scaled_obst.append((x, y))

        self.obstacles[name] = scaled_obst

        for (x, y) in scaled_obst:
            if 0 <= x and x < self.n_X and 0 <= y and y < self.n_Y:
                if mask_name is not None:
                    self.obstacles_masks[mask_name][x, y] = False
                else:
                    self.obstacles_masks["permanent"][x, y] = False


    def addRectangularObstacle(self, x_start, x_end, y_start, y_end, name, mask_name=None):
        """
            Adds a rectangular obstacle to the wave simulation.
            Parameters:
                - x_start (int): Starting X coordinate of the rectangle in the window.
                - y_start (int): Starting Y coordinate of the rectangle in the window.
                - x_end (int): Ending X coordinate of the rectangle in the window.
                - y_end (int): Ending Y coordinate of the rectangle in the window.
                - name (str): Name of the obstacle.
                - mask_name (str): Name of the mask to apply to the obstacle, if None we apply the permanent mask
        """
        obstacle = [(x, y) for x in range(x_start, x_end) for y in range(y_start, y_end)]
        self.addRandomObstacle(obstacle, name, mask_name)


    def addCircularObstacle(self, x_center, y_center, radius, name, mask_name=None):
        """
            Adds a circular obstacle to the wave simulation.
            Parameters:
                - x_center (int): X coordinate of the circle center in the window.
                - y_center (int): Y coordinate of the circle center in the window.
                - radius (int): Radius of the circle in the window.
                - name (str): Name of the obstacle.
                - mask_name (str): Name of the mask to apply to the obstacle, if None we apply the permanent mask
        """
        obstacle = [(x, y) for x in range(WINDOW_WIDTH) for y in range(WINDOW_HEIGHT)
                    if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius ** 2]
        self.addRandomObstacle(obstacle, name, mask_name)


    def removeObstacle(self, name, mask_names=None):
        """
            Removes an obstacle from the wave simulation by its name.
            Parameters:
                - name (str): Name of the obstacle to remove.
                - mask_names (str): List of the name of the masks to remove from the obstacle, if None we remove the permanent mask
        """
        if name in self.obstacles:
            for (x, y) in self.obstacles[name]:
                if 0 <= x < self.n_X and 0 <= y < self.n_Y:
                    if mask_names:
                        for mask_name in mask_names:
                            self.obstacles_masks[mask_name][x, y] = True
                    else:
                        self.obstacles_masks["permanent"][x, y] = True  # Unmark the obstacle location in the mask
            del self.obstacles[name]


    def addLightArea(self, mask, name):
        """
            Adds a light area to the simulation.
            Parameters:
                - mask (np.ndarray): 2D array of uint8 representing the light area (0 for no light, 255 for full light).
                - name (str): Name of the light area.
        """
        self.light_areas[name] = mask

    
    def setLightAreaPosition(self, name, x, y):
        """
            Sets the position of a light area in the window for visualization.
            Parameters:
                - name (str): Name of the light area.
                - x (int): X coordinate of the light area in the window.
                - y (int): Y coordinate of the light area in the window.
        """
        if name in self.light_areas:
            self.light_areas_position[name] = (x, y)


    def addGaussianLightArea(self, size, amplitude, sigma, name):
        """
            Add a circular light area using a Gaussian bell
            Parameters:
                - size: Size of the light area in pixels (diameter of the circle).
                - amplitude: Amplitude of the distribution
                - sigma: Standard deviation of the Gaussian distribution (controls the spread of the light).
                - name: Name of the light area.
        """
        size = int(size // RESIZE_FACTOR) 
        x_center = size // 2
        y_center = size // 2

        # Create a grid of coordinates
        x_grid = np.arange(size)
        y_grid = np.arange(size)
        X, Y = np.meshgrid(x_grid, y_grid)

        # Calculate the Gaussian distribution
        light_matrix = amplitude * np.exp(-((X - x_center)**2 + (Y - y_center)**2) / (2 * sigma**2))

        # Set to 0 values outside the circle of given size
        radius = size // 2
        light_matrix[(X - x_center)**2 + (Y - y_center)**2 > radius**2] = 0

        self.addLightArea(light_matrix.astype(np.uint8), name)


    def removeLightArea(self, name):
        """
            Removes a light area from the simulation by its name.
            Parameters:
                - name (str): Name of the light area to remove.
        """
        if name in self.light_areas:
            del self.light_areas[name]


    def __update(self):
        """
            Updates the wave simulation for the next time step using the d'Alembert method with damping.
        """        
        # Apply obstacles by setting the wave amplitude to zero at obstacle locations
        self.u *= self.obstacles_masks["permanent"]  # Apply the permanent mask
        if self.current_mask_name is not None:
            self.u *= self.obstacles_masks[self.current_mask_name]  # Apply the current mask if it exists 

        # We use a variable damping coefficient
        variable_coeff2 = self.COEFF2 / (0.01 + 10 * np.abs(self.u)) + self.COEFF3 * self.boundaries_mask  # Damping increases with wave amplitude
        
        # Update future wave amplitude based on current and previous amplitudes
        self.f[+1:-1, +1:-1] = (2*self.u[+1:-1, +1:-1] - self.p[+1:-1, +1:-1] 
                     + self.COEFF1 * (self.u[+1:-1, 2:] - 2*self.u[+1:-1, +1:-1] + self.u[+1:-1, :-2] + 
                                                      self.u[+2:,+1:-1] - 2*self.u[+1:-1, +1:-1] + self.u[:-2, +1:-1])
                     - variable_coeff2[+1:-1, +1:-1] * (self.u[+1:-1, +1:-1] - self.p[+1:-1, +1:-1]))
        
        # Thresholding to consider the wave as extinguished
        self.f[np.abs(self.f) < SEUIL] = 0.0

        # Update previous and current wave amplitudes for the next iteration
        temp = self.p
        self.p = self.u
        self.u = self.f
        self.f = temp  # Reuse the array for future calculations
        self.time += DT  # Increment simulation time

        return self.u


    def update(self):
        """
            Public method to update the wave simulation for the next time step.
            We apply the wave speed multiplier here to allow increasing the wave speed without affecting the stability condition (which is based on the spatial step and time step).
        """
        for _ in range(WAVE_SPEED_MULTIPLIER):
            self.__update()


    def getTime(self):
        """
            Returns the current simulation time.
            Returns:
            float: Current simulation time in seconds.
        """
        return self.time


    def getSimulationState(self):
        """
            Returns the current state of the wave simulation.
            Returns:
            np.ndarray: 2D array representing the current wave amplitude at each grid point.
                -> The coordinates of the array correspond to the grid points in the simulation, not the window coordinates
        """
        return self.u
    

    def setCurrentMask(self, mask_name):
        """
            Sets the current mask to apply for obstacles.
            Parameters:
                - mask_name (str): Name of the mask to set as current, if None we apply only the permanent mask
        """
        self.applyMask(mask_name)


    def draw(self):
        """
            Draws the current state of the wave simulation on the Pygame window.
            Parameters:
               - light_areas (dict): Optional dictionary of light areas to apply during the update
                 Format : {name: (x, y)} where (x, y) is the position of the light source in the window.
        """

        # Surface to draw the wave simulation
        surf = pygame.Surface((self.n_X - 2*BS, self.n_Y - 2*BS), pygame.SRCALPHA)
        surf.fill((0, 0, 0))

        # Wave intensity
        wave_intensity = np.clip(np.abs(self.u[BS:-BS, BS:-BS]) * 255, 0, 255).astype(np.uint8)
        alpha_array = (255 - wave_intensity)

        # Apply light areas if provided
        for name, (x, y) in self.light_areas_position.items():
            if name in self.light_areas:

                light_mask = self.light_areas[name]
                h, w = light_mask.shape

                # Center of the light area in the simulation grid
                x_grid = (x // RESIZE_FACTOR) + w//2 
                y_grid = (y // RESIZE_FACTOR) + h//2 

                # Area in the alpha array
                x1 = max(0, x_grid - w // 2)
                x2 = min(self.n_X - 2*BS, x_grid + w // 2)
                y1 = max(0, y_grid - h // 2)
                y2 = min(self.n_Y - 2*BS, y_grid + h // 2)

                # Corresponding area in the light mask
                mask_x1 = max(0, w // 2 - x_grid)                  
                mask_x2 = min(w, mask_x1 + (x2 - x1))
                mask_y1 = max(0, h // 2 - y_grid)
                mask_y2 = min(h, mask_y1 + (y2 - y1))

                # Subtract the light mask from the alpha array
                # We use signed int because of underflow
                alpha_array[x1:x2, y1:y2] = np.clip(alpha_array[x1:x2, y1:y2].astype(np.int16) - light_mask[mask_x1:mask_x2, mask_y1:mask_y2], 0, 255).astype(np.uint8)
            else:
                self.light_areas_position.pop(name)  # Remove the light area if it doesn't exist anymore

        # Adding the alpha channel to the surface
        pygame.surfarray.pixels_alpha(surf)[:] = alpha_array

        # Upscale and draw
        scaled_surf = pygame.transform.scale(surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.window.blit(scaled_surf, (0, 0))


    

if __name__ == "__main__":
    
    # ----------------- Test using Pygame for visualization -----------------
    from math import sin, pi
    import time
    from BoardGame import BoardGame

    # Initialize Pygame
    pygame.init()

    # Create the window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # Create the board game
    board_game = BoardGame(window)

    # Create wave simulation
    wave = Wave(window)

    # Add obstacles for testing
    wave.addRectangularObstacle(300, 315, 200, 600, "TestRectangularObstacle")
    wave.addCircularObstacle(700, 400, 50, "TestCircularObstacle")

    # Add light areas for testing
    SIZE_LIGHT_AREA = 200
    wave.addGaussianLightArea(SIZE_LIGHT_AREA, 100, 7.8, "MainCharacterLight")

    # Functions for setting the exitance of the source pixel (for testing)
    def square_wave(t):
        return 1.0 if (t % 1.0) < 0.2 else 0.0
    def exitance(t):
        return 0.5 #+ 0.5 * square_wave(t) * sin(2 * pi * 50.0 * t)

    # Position of thee source
    source_x = WINDOW_WIDTH // 2
    source_y = WINDOW_HEIGHT // 2

    # Main loop
    running = True
    while running:

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Value for the source pixel
        t = wave.getTime()
        value = exitance(t)

        # Keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            source_x = max(0, source_x - 1)
        if keys[pygame.K_RIGHT]:
            source_x = min(WINDOW_WIDTH - 1, source_x + 1)
        if keys[pygame.K_UP]:
            source_y = max(0, source_y - 1)
        if keys[pygame.K_DOWN]:
            source_y = min(WINDOW_HEIGHT - 1, source_y + 1)
        if keys[pygame.K_SPACE]:  # Reset the wave simulation
            t = wave.getTime()
            value += 1.0

        # Update wave simulation
        wave.setPixel(source_x, source_y, value=value)
        wave.update()

        # Fill the window with white
        window.fill((255, 255, 255))

        # Draw the board game
        board_game.draw()

        # Light areas
        wave.setLightAreaPosition("MainCharacterLight", source_x-SIZE_LIGHT_AREA//2, source_y-SIZE_LIGHT_AREA//2)

        # Draw the wave
        wave.draw()

        # Update the display
        pygame.display.flip()
