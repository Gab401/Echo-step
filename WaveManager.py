# Wave simulation using the d'Alembert method with damping


# Generic imports
import pygame
import numpy as np

# Local imports
from Constants import *


class Wave:

    """
        Class representing a wave simulation using the d'Alembert method with damping.
    """

    # Class variables for masks and obstacles
    global_obstacles_mask = None
    global_obstacles = {}

    def __init__(self, wave_speed_multiplier=WAVE_SPEED_MULTIPLIER, offset_transparency=None):
        """
            Initializes the wave simulation with given grid dimensions.
            Parameters:
                - window: Pygame window for visualization.
                - wave_speed_multiplier: Multiplier for the wave speed.
                - offset_transparency: Transparency offset for the wave visualization (debug).
        """
        # Parameters for the wave simulation
        self.n_X = (WINDOW_WIDTH // RESIZE_FACTOR) + 2 * BS 
        self.n_Y = (WINDOW_HEIGHT // RESIZE_FACTOR) + 2 * BS
        self.COEFF1 = (C*DT/DX)**2 # Coefficient for the wave update formula
        self.COEFF2 = ALPHA * DT       # Coefficient for the damping term
        self.COEFF3 = BOUNDARY_DAMPING * DT       # Coefficient for the boundary condition (ABC)
        self.wave_speed_multiplier = wave_speed_multiplier  # Multiplier for the wave speed

        # Initialize wave amplitude arrays
        self.u = np.zeros((self.n_X, self.n_Y))  # Current wave amplitude
        self.p = np.zeros((self.n_X, self.n_Y))  # Previous wave amplitude
        self.f = np.zeros((self.n_X, self.n_Y))  # Future wave amplitude

        # Obstacles and masks specific to this instance
        self.obstacles = {}  # Dictionary to store obstacles
        self.obstacles_mask = np.ones((self.n_X, self.n_Y), dtype=bool)
        if Wave.global_obstacles_mask is None:
            Wave.global_obstacles_mask = np.ones((self.n_X, self.n_Y), dtype=bool)

        # Boundaries
        self.boundaries_mask = np.zeros((self.n_X, self.n_Y), dtype=bool)  # Mask for boundaries (False for interior, True for boundaries)
        self.boundaries_mask[:BS, :] = True  # Left boundary
        self.boundaries_mask[-BS:, :] = True  # Right boundary
        self.boundaries_mask[:, :BS] = True  # Top boundary
        self.boundaries_mask[:, -BS:] = True  # Bottom boundary

        # Keep in memory all the setPixel appeals to apply them when update is called
        self.set_pixel_calls = []   # List of lists [x, y, value] for each setPixel call

        self.offset_transparency = offset_transparency  # Transparency offset for the wave visualization (debug)


    def setPixel(self, x, y, value=1.0):
        """
            Public method to set the amplitude of the wave at a specific pixel.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
                - value (float): Amplitude value to set at the pixel.
        """
        self.set_pixel_calls.append((x, y, value))  # Store the call for later application


    def __setPixel(self, x, y, value=1.0):
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


    def addRandomObstacle(self, obst, name, mask_name=None):
        """
            Adds a random obstacle to the wave simulation.
            Parameters:
                - obst (list of tuples): List of (x, y) coordinates (in the window) for the obstacle.
                - name (str): Name of the obstacle.
                - mask_name (int): 0 = global mask, 1 = specific mask
        """
        scaled_obst = []
        for x, y in obst:
            x = (x // RESIZE_FACTOR) + BS
            y = (y // RESIZE_FACTOR) + BS
            scaled_obst.append((x, y))

        if mask_name==0:
            Wave.global_obstacles[name] = scaled_obst
            for (x, y) in scaled_obst:
                if 0 <= x and x < self.n_X and 0 <= y and y < self.n_Y:
                    Wave.global_obstacles_mask[x, y] = False  # Mark the obstacle location in the global mask
        elif mask_name==1:
            self.obstacles[name] = scaled_obst
            for (x, y) in scaled_obst:
                if 0 <= x and x < self.n_X and 0 <= y and y < self.n_Y:
                    self.obstacles_mask[x, y] = False  # Mark the obstacle location in the specific mask


    def addRectangularObstacle(self, x_start, x_end, y_start, y_end, name, mask_name=None):
        """
            Adds a rectangular obstacle to the wave simulation.
            Parameters:
                - x_start (int): Starting X coordinate of the rectangle in the window.
                - y_start (int): Starting Y coordinate of the rectangle in the window.
                - x_end (int): Ending X coordinate of the rectangle in the window.
                - y_end (int): Ending Y coordinate of the rectangle in the window.
                - name (str): Name of the obstacle.
                - mask_name (int): 0 = global mask, 1 = specific mask
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
                - mask_name (int): 0 = global mask, 1 = specific mask
        """
        obstacle = [(x, y) for x in range(WINDOW_WIDTH) for y in range(WINDOW_HEIGHT)
                    if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius ** 2]
        self.addRandomObstacle(obstacle, name, mask_name)


    def removeObstacle(self, name, mask_name=None):
        """
            Removes an obstacle from the wave simulation by its name.
            Parameters:
                - name (str): Name of the obstacle to remove.
                - mask_name (int): Name of the mask to remove from the obstacle, 0=global mask, 1=specific mask
        """
        if mask_name==0:
            if name in Wave.global_obstacles:
                for (x, y) in Wave.global_obstacles[name]:
                    if 0 <= x < self.n_X and 0 <= y < self.n_Y:
                        Wave.global_obstacles_mask[x, y] = True  # Unmark the obstacle location in the global mask
                del Wave.global_obstacles[name]
        elif mask_name==1:
            if name in self.obstacles:
                for (x, y) in self.obstacles[name]:
                    if 0 <= x < self.n_X and 0 <= y < self.n_Y:
                        self.obstacles_mask[x, y] = True  # Unmark the obstacle location in the mask
                del self.obstacles[name]


    def __update(self):
        """
            Updates the wave simulation for the next time step using the d'Alembert method with damping.
        """        
        # Apply obstacles by setting the wave amplitude to zero at obstacle locations
        self.u *= Wave.global_obstacles_mask  # Apply the global mask to all instances of the wave simulation
        self.u *= self.obstacles_mask  # Apply the specific mask for this instance of the wave simulation

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

        return self.u


    def update(self):
        """
            Public method to update the wave simulation for the next time step.
            We apply the wave speed multiplier here to allow increasing the wave speed without affecting the stability condition (which is based on the spatial step and time step).
        """
        for _ in range(self.wave_speed_multiplier):

            # Apply all the setPixel calls before updating the wave simulation
            if len(self.set_pixel_calls) > 0:
                for (x, y, value) in self.set_pixel_calls:
                    self.__setPixel(x, y, value)
            
            # Update
            self.__update()
        
        self.set_pixel_calls = []  # Clear the setPixel calls after applying them


    def getSimulationState(self):
        """
            Returns the current state of the wave simulation.
            Returns:
            np.ndarray: 2D array representing the current wave amplitude at each grid point.
                -> The coordinates of the array correspond to the grid points in the simulation, not the window coordinates
        """
        return self.u


    def getMask(self):
        """
            Returns the specific mask of this wave simulation (without the global mask).
        """
        return self.obstacles_mask


    def setMask(self, mask):
        """
            Sets the specific mask of this wave simulation (without the global mask).
            Parameters:
                - mask (np.ndarray): 2D array of bool representing the mask to set (True for free space, False for obstacles).
        """
        self.obstacles_mask = mask
        

    def drawResult(self):
        """
            Draws the current state of the wave on a surface and returns it.
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

        # Adding the alpha channel to the surface
        pygame.surfarray.pixels_alpha(surf)[:] = alpha_array

        # Apply the offset transparency for debugging purposes
        if self.offset_transparency is not None:
            pygame.surfarray.pixels_alpha(surf)[:] = np.clip(pygame.surfarray.pixels_alpha(surf)[:] + self.offset_transparency, 0, 255)

        return surf      


    def setWaveSpeedMultiplier(self, multiplier):
        """
            Sets the wave speed multiplier for this wave simulation.
            Parameters:
                - multiplier (int): Multiplier for the wave speed. Higher values will increase the wave speed.
        """
        self.wave_speed_multiplier = multiplier


    def _getGradient(self, x, y):
        """
            Returns the gradient of the wave at a specific pixel.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
            Returns:
                - (float, float): Gradient of the wave at the specified pixel (gradient_x, gradient_y).
        """
        x = (x // RESIZE_FACTOR) + BS  
        y = (y // RESIZE_FACTOR) + BS
        if 1 <= x < self.n_X - 1 and 1 <= y < self.n_Y - 1:
            gradient_x = (self.u[x + 1, y] - self.u[x - 1, y]) / (2 * DX)
            gradient_y = (self.u[x, y + 1] - self.u[x, y - 1]) / (2 * DX)
            return gradient_x, gradient_y
        else:
            return 0.0, 0.0  # No gradient outside the valid range
        

    def _getEnergyFlow(self, x, y):
        """
            Returns the energy flow of the wave at a specific pixel.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
            Returns:
                - (float, float): Energy flow of the wave at the specified pixel (flow_x, flow_y).
        """
        gradient_x, gradient_y = self._getGradient(x, y)
        x = (x // RESIZE_FACTOR) + BS
        y = (y // RESIZE_FACTOR) + BS
        du = self.u[x, y] - self.p[x, y]  # Time derivative of the wave amplitude
        energy_flow_x = du * gradient_x
        energy_flow_y = du * gradient_y

        return energy_flow_x, energy_flow_y
    

    def _getIntensity(self, x, y):
        """
            Returns the intensity of the wave at a specific pixel.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
            Returns:
                - float: Intensity of the wave at the specified pixel.
        """
        x = (x // RESIZE_FACTOR) + BS
        y = (y // RESIZE_FACTOR) + BS
        return np.abs(self.u[x, y])






class WaveManager:

    """
        Class to manage multiple wave simulations, to each simulation correspond a different mask of obstacles to simulate the different levels of the map.
    """

    def __init__(self, window, board_game, offset_transparency=None):
        """
            Initialize the WaveManager with altitude masks and wave speed multipliers.
            Parameters:
                - window: Pygame window for visualization.
                - board_game: BoardGame instance to get the altitude masks and wave speed multipliers.
                - offset_transparency: Transparency offset for the wave visualization (debug).
        """
        # Get the altitude masks from the board game
        altitude_masks = board_game.getAltitudeMasks()

        # Get the unique altitudes in descending order
        self.altitudes = sorted(list(set(altitude_masks)), reverse=True) 
        if self.altitudes[0] == float('inf'):
            self.altitudes = self.altitudes[1:] # Remove the infinite altitude if it exists 

        assert len(self.altitudes) > 0, "There must be at least one altitude level in the altitude masks."

        # Set the wave speed multiplier for each altitude level (if the first level is water, we use a specific wave speed multiplier for water)  
        wave_speed_multiplier = {altitude: WAVE_SPEED_MULTIPLIER for altitude in altitude_masks.keys()}  
        
        x_test, y_test = altitude_masks[self.altitudes[-1]][0]  # Get the coordinates of a pixel with altitude 0 (water)
        if board_game.isWater(x_test, y_test):
            wave_speed_multiplier[self.altitudes[-1]] = WATER_WAVE_SPEED_MULTIPLIER  # Set a specific wave speed multiplier for water
            #print("Water wave speed multiplier set to", WATER_WAVE_SPEED_MULTIPLIER)

        # List to store multiple wave simulations, one for each altitude level
        self.waves = [Wave() for _ in range(len(self.altitudes))]  

        # Set the masks for each wave simulation based on the altitude masks
        for i, altitude in enumerate(self.altitudes):
            for j in range(i):  
                self.waves[i].addRandomObstacle(altitude_masks[self.altitudes[j]], f"Altitude_{self.altitudes[j]}", mask_name=1)
            
            if altitude in wave_speed_multiplier.keys():
                self.waves[i].setWaveSpeedMultiplier(wave_speed_multiplier[altitude])  # Set the wave speed multiplier for this altitude level

        self.window = window  # Store the window for visualization

        # Light area (not a wave, just a light area)
        self.light_areas = {}  # Dictionary to store light areas, format: {name: mask} where mask is a 2D np.array(uint8), the mask is substracted from the image
        self.light_areas_position = {}  # Position of the light area (x, y) in the window, used for visualization

        self.offset_transparency = offset_transparency  # Transparency offset for the wave visualization (debug)


    def setPixel(self, x, y, altitude, value=1.0):
        """
            Sets the amplitude of the wave at a specific pixel for all wave simulations.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
                - altitude (float): Altitude level of the pixel, used to determine which wave simulation to update.
                       If None, the pixel will be set in all wave simulations.
                - value (float): Amplitude value to set at the pixel.
        """

        if altitude is None:
            for wave in self.waves:
                wave.setPixel(x, y, value)
        else:
            self.waves[self.altitudes.index(altitude)].setPixel(x, y, value) 

    
    def addRandomObstacle(self, obst, name):
        """
            Adds a random obstacle to all wave simulations.
            Parameters:
                - obst (list of tuples): List of (x, y) coordinates (in the window) for the obstacle.
                - name (str): Name of the obstacle.
        """
        self.waves[0].addRandomObstacle(obst, name, mask_name=0)  # Add the obstacle to the global mask of the first wave simulation (which will be shared by all wave simulations)


    def addRectangularObstacle(self, x_start, x_end, y_start, y_end, name):
        """
            Adds a rectangular obstacle to all wave simulations.
            Parameters:
                - x_start (int): Starting X coordinate of the rectangle in the window.
                - y_start (int): Starting Y coordinate of the rectangle in the window.
                - x_end (int): Ending X coordinate of the rectangle in the window.
                - y_end (int): Ending Y coordinate of the rectangle in the window.
                - name (str): Name of the obstacle.
        """
        obstacle = [(x, y) for x in range(x_start, x_end) for y in range(y_start, y_end)]
        self.addRandomObstacle(obstacle, name)

    
    def addCircularObstacle(self, x_center, y_center, radius, name):
        """
            Adds a circular obstacle to all wave simulations.
            Parameters:
                - x_center (int): X coordinate of the circle center in the window.
                - y_center (int): Y coordinate of the circle center in the window.
                - radius (int): Radius of the circle in the window.
                - name (str): Name of the obstacle.
        """
        obstacle = [(x, y) for x in range(WINDOW_WIDTH) for y in range(WINDOW_HEIGHT)
                    if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius ** 2]
        self.addRandomObstacle(obstacle, name)


    def removeObstacle(self, name):
        """
            Removes an obstacle from all wave simulations by its name.
            Parameters:
                - name (str): Name of the obstacle to remove.
        """
        self.waves[0].removeObstacle(name, mask_name=0)  # Remove the obstacle from the global mask of the first wave simulation (which will be shared by all wave simulations)


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
            if x is not None and y is not None:
                self.light_areas_position[name] = (x//RESIZE_FACTOR, y//RESIZE_FACTOR)
            else:
                self.light_areas_position[name] = (None, None)  


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


    def update(self):
        """
            Updates all wave simulations for the next time step.
        """
        for wave in self.waves:
            wave.update()


    def draw(self):
        """
            Draws the current state of all wave simulations on the window.
        """

        # Combine the results of all wave simulations 
        surf = self.waves[0].drawResult().copy()
        for wave in self.waves[1:]:
            surf.blit(wave.drawResult(), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)  #Multiplication
        

         # Apply light areas if provided
        for name, (x, y) in list(self.light_areas_position.items()):
            if x is not None and y is not None:
                if name in self.light_areas:

                    light_mask = self.light_areas[name]
                    h, w = light_mask.shape 

                    # Create a surface for the light mask
                    light_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                    light_surf.fill((0, 0, 0, 0))  # Start with a fully transparent surface

                    # Add the light mask to the surface
                    pygame.surfarray.pixels_alpha(light_surf)[:] = light_mask

                    # Blit the light surface onto the main surface using additive blending
                    surf.blit(light_surf, (x, y), special_flags=pygame.BLEND_RGBA_SUB)              
                else:
                    self.light_areas_position.pop(name)  # Remove the light area if it doesn't exist anymore

        # Apply the offset transparency for debugging purposes
        if self.offset_transparency is not None:
            pygame.surfarray.pixels_alpha(surf)[:] = np.clip(pygame.surfarray.pixels_alpha(surf)[:] + self.offset_transparency, 0, 255)
            
        # Upscale the surface to fit the window
        scaled_surf = pygame.transform.scale(surf, (WINDOW_WIDTH, WINDOW_HEIGHT))

        self.window.blit(scaled_surf, (0, 0))  # Blit the combined surface onto the window
    

    def getIntensity(self, x, y, altitude=None): 
        """
            Returns the intensity of the wave at a specific pixel for the appropriate wave simulation based on the altitude.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
                - altitude (float): Altitude of the pixel.
            Returns:
                - float: Intensity of the wave at the specified pixel.
        """
        if altitude is None:
            sum_intensity = 0.0
            for wave in self.waves:
                sum_intensity += wave._getIntensity(x, y)
            return sum_intensity
        else:
            return self.waves[self.altitudes.index(altitude)]._getIntensity(x, y)
        

    def getGradient(self, x, y, altitude=None):
        """
            Returns the gradient of the sum of the waves at a specific pixel for the appropriate wave simulation based on the altitude.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
            Returns:
                - (float, float): Gradient of the wave at the specified pixel (gradient_x, gradient_y).
        """
        if altitude is None:
            sum_gradient_x = 0.0
            sum_gradient_y = 0.0
            for wave in self.waves:
                gradient_x, gradient_y = wave._getGradient(x, y)
                sum_gradient_x += gradient_x
                sum_gradient_y += gradient_y
            return sum_gradient_x, sum_gradient_y
        else:
            return self.waves[self.altitudes.index(altitude)]._getGradient(x, y)
    

    def getEnergyFlow(self, x, y, altitude=None):
        """
            Returns the energy flow of the sum of the waves at a specific pixel for the appropriate wave simulation based on the altitude.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
            Returns:
                - (float, float): Energy flow of the wave at the specified pixel (flow_x, flow_y).
        """
        if altitude is None:
            sum_flow_x = 0.0
            sum_flow_y = 0.0
            for wave in self.waves:
                flow_x, flow_y = wave._getEnergyFlow(x, y)
                sum_flow_x += flow_x
                sum_flow_y += flow_y
            return sum_flow_x, sum_flow_y
        else:
            return self.waves[self.altitudes.index(altitude)]._getEnergyFlow(x, y)
    

    def getTimeDerivative(self, x, y, altitude=None):
        """
            Returns the time derivative of the wave at a specific pixel for the appropriate wave simulation based on the altitude.
            Parameters:
                - x (int): X coordinate of the pixel in the window.
                - y (int): Y coordinate of the pixel in the window.
                - altitude (float): Altitude of the pixel.
            Returns:
                - float: Time derivative of the wave at the specified pixel.
        """
        x_grid = (x // RESIZE_FACTOR) + BS
        y_grid = (y // RESIZE_FACTOR) + BS
        if altitude is None:
            sum_time_derivative = 0.0
            for wave in self.waves:
                du = wave.u[x_grid, y_grid] - wave.p[x_grid, y_grid]  # Time derivative of the wave amplitude
                sum_time_derivative += du
            return sum_time_derivative
        else:
            wave = self.waves[self.altitudes.index(altitude)]
            du = wave.u[x_grid, y_grid] - wave.p[x_grid, y_grid]  # Time derivative of the wave amplitude
            return du

        




if __name__ == "__main__":
    # ----------------- WaveManager test -----------------
    from math import sin, pi
    import time
    from BoardGame import BoardGame

    # Initialize Pygame
    pygame.init()

    # Create the window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # Create the board game
    board_game = BoardGame(window)

    # Create wave simulations
    wave = WaveManager(window, board_game)

    # Add obstacles for testing
    #wave.addRectangularObstacle(300, 315, 200, 600, "TestRectangularObstacle")
    #wave.addCircularObstacle(700, 400, 50, "TestCircularObstacle")

    # Functions for setting the exitance of the source pixel (for testing)
    def square_wave(t):
        return 1.0 if (t % 1.0) < 0.2 else 0.0
    def exitance(t):
        return 1.0 #+ 0.5 * square_wave(t) * sin(2 * pi * 50.0 * t)

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
        t = 1
        value = exitance(t)

        # Keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            source_x = max(0, source_x - HERO_RUN_SPEED)
        if keys[pygame.K_RIGHT]:
            source_x = min(WINDOW_WIDTH - 1, source_x + HERO_RUN_SPEED)
        if keys[pygame.K_UP]:
            source_y = max(0, source_y - HERO_RUN_SPEED)
        if keys[pygame.K_DOWN]:
            source_y = min(WINDOW_HEIGHT - 1, source_y + HERO_RUN_SPEED)
        if keys[pygame.K_SPACE]:  # Reset the wave simulation
            value += 5.0

        # Update wave simulation
        wave.setPixel(source_x, source_y, 0.0, value=value)
        wave.update()

        # Fill the window with white
        window.fill((255, 255, 255))

        # Draw the board game
        board_game.draw()

        # Draw the wave
        wave.draw()

        # Update the display
        pygame.display.flip()



    
"""
if __name__ == "__main__":
    
    # ----------------- Wave test using Pygame for visualization -----------------
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
    wave = Wave()

    # Add obstacles for testing
    wave.addRectangularObstacle(300, 315, 200, 600, "TestRectangularObstacle", 1)
    wave.addCircularObstacle(700, 400, 50, "TestCircularObstacle", 0)

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
        t = 1
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
            value += 1.0

        # Update wave simulation
        wave.setPixel(source_x, source_y, value=value)
        wave.update()

        # Fill the window with white
        window.fill((255, 255, 255))

        # Draw the board game
        #board_game.draw()

        # Draw the wave
        surf = wave.drawResult()
        window.blit(surf, (0, 0))

        # Update the display
        pygame.display.flip()
"""