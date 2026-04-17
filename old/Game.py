# Generic imports
import pygame
from numpy import sin, pi

# Local imports
from Constants import *
from BoardGame import BoardGame
from WaveManager import WaveManager
from Creature import *
from Bridge import Bridge
from Objects import *


class Game:
    """
        Class representing the game, containing the main loop and the main objects of the game (board game, wave manager, creatures, bridge).
    """

    def __init__(self, window, map_name=DEFAULT_MAP, debug=False):

        self.window = window
        self.debug = debug

        # Create the board game
        self.board_game = BoardGame(window)

        # Bridge
        self.bridge = Bridge()

        # Create wave simulation
        if self.debug:
            self.wave = WaveManager(window, self.board_game, offset_transparency=100)
        else:
            self.wave = WaveManager(window, self.board_game)

        # Create the creatures and the objects
        self.objects = []
        self.creatures = []
        init_character_positions = self.board_game.getCharacterInitialPositions()
        
        assert "MainCharacter" in init_character_positions, "The map must contain a MainCharacter with its initial position(s) defined."
        x, y = init_character_positions["MainCharacter"][0]
        self.creatures.append(MainCharacter(window, self.board_game, self.wave, self.bridge, x, y, display_hitbox=self.debug))

        for character_name, positions in init_character_positions.items():
            if character_name != "MainCharacter":
                if character_name in CREATURE_CLASSES:
                    CreatureClass = CREATURE_CLASSES[character_name]
                    for x, y in positions:
                        self.creatures.append(CreatureClass(window, self.board_game, self.wave, self.bridge, x, y, display_hitbox=self.debug))
                elif character_name in OBJECT_CLASSES:
                    ObjectClass = OBJECT_CLASSES[character_name]
                    for x, y in positions:
                        self.objects.append(ObjectClass(window, self.board_game, self.wave, self.bridge, x, y))
                else:
                    raise ValueError(f"Unknown character name '{character_name}' in the map. It should be either 'MainCharacter' or one of the following: {list(CREATURE_CLASSES.keys()) + list(OBJECT_CLASSES.keys())}.")

        # Main loop
        frame_count = 0
        running = True
        clock = pygame.time.Clock()
        while not(self.bridge.isGameOver()) and running:

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update the game state
            keys = pygame.key.get_pressed()

            # Update the creatures
            for creature in self.creatures:
                creature.update(keys, frame_count)

            # Update the wave simulation
            self.wave.update()

            # Draw the game
            self.superDraw(frame_count)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(FPS)

            frame_count += 1
        
        print(f"Game over! Dictionary: {self.bridge.getGameOverDic()}")


    def superDraw(self, frame_count):
        """
            Draw the game in the right order
        """
        # Fill the window with white
        self.window.fill((255, 255, 255))

        # Draw the board game
        self.board_game.draw()

        # Draw the creatures and objects beginning on the top of the window, then the ones on the bottom, to create a depth effect
        # We give priority to the creatures in "catch" state
        creatures_to_draw = [creature for creature in self.creatures if creature.isInCatchState()]
        others = [creature for creature in self.creatures if not creature.isInCatchState()] + self.objects
        others.sort(key=lambda c: c.getYToDraw()) 
        creatures_to_draw =  others + creatures_to_draw

        for creature in creatures_to_draw:
            creature.draw(frame_count)

        # Draw the wave simulation
        self.wave.draw()

        # Add infos
        self.creatures[0].drawInfo(frame_count)






if __name__ == "__main__":
    # Initialize pygame
    pygame.init()

    # Create the window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Echo-step")

    # Create the game
    game = Game(window, debug=True)

    # Quit pygame
    pygame.quit()