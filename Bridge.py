
# Local imports
from Constants import *
from BoardGame import BoardGame
from WaveManager import WaveManager
from Creature import *
from Objects import *


class Bridge:
    """
        A class to allow creature to send or receive information from other creatures or to interact with objects
    """
    def __init__(self, window, debug=False):

        self.window = window
        self.debug = debug
        self.reset()


    def reset(self):
        """
            Reset the bridge, by clearing the lists of creatures and objects, and resetting the game over flag and message
        """
        self.creatures = {}
        self.objects = {}
        self.game_over = False
        self.game_over_message = ""

    def clear(self):
        """
            Clear the window and reset the creatures id (to avoid bugs if we play several times)
        """
        self.window.fill((255, 255, 255))
        Creature.clear()
        Star.clear()


    def register_creature(self, creature):
        """
            Register a creature to the bridge, so that it can send or receive information from other creatures
        """
        self.creatures[creature.name] = creature


    def register_object(self, object):
        """
            Register an object to the bridge, so that creatures can interact with it
        """
        self.objects[object.name] = object

    
    def isRegistered(self, name):
        """
            Check if a creature or object is registered in the bridge
        """
        return name in self.creatures or name in self.objects


    def getPosition(self, name):
        """
            Get the position of a creature or object
        """
        if name in self.creatures:
            return self.creatures[name].x, self.creatures[name].y, self.creatures[name].z
        elif name in self.objects:
            return self.objects[name].x, self.objects[name].y, self.objects[name].z
        else:
            raise ValueError(f"Creature or object {name} not found in the bridge")
        

    def sendEvent(self, receiver_name, event, sender_name=None):
        """
            Send an event from a creature to another creature through the bridge
        """
        if receiver_name in self.creatures:
            self.creatures[receiver_name].receiveEvent(event, sender_name)
        elif receiver_name in self.objects:
            self.objects[receiver_name].receiveEvent(event, sender_name)
        else:
            raise ValueError(f"Creature or object {receiver_name} not found in the bridge")
        
    
    def gameOver(self, dic = {}):
        """
            End the game
        """
        self.game_over = True
        self.game_over_dic = dic

    
    def isGameOver(self):
        """
            Check if the game is over
        """
        return self.game_over
    

    def getGameOverDic(self):
        """
            Get the game over dictionary
        """
        return self.game_over_dic
    

    def getNbStars(self):
        """
            Get the number of stars
        """
        return len(Star.stars_list)
    

    def game(self, map_name=DEFAULT_MAP):
        """
            Run the game
        """

        # Reset the bridge and clear the window
        self.reset()
        self.clear()

        # Create the board game
        board_game = BoardGame(self.window, map_name, debug=self.debug)

        # Create wave simulation
        if self.debug:
            wave = WaveManager(self.window, board_game, offset_transparency=100)
        else:
            wave = WaveManager(self.window, board_game)

        # Create the creatures and the objects
        objects = []
        creatures = []
        init_character_positions = board_game.getCharacterInitialPositions()
        
        assert "MainCharacter" in init_character_positions, "The map must contain a MainCharacter with its initial position(s) defined."
        x, y = init_character_positions["MainCharacter"][0]
        creatures.append(MainCharacter(self.window, board_game, wave, self, x, y, display_hitbox=self.debug))

        for character_name, positions in init_character_positions.items():
            if character_name != "MainCharacter":
                if character_name in CREATURE_CLASSES:
                    CreatureClass = CREATURE_CLASSES[character_name]
                    for x, y in positions:
                        creatures.append(CreatureClass(self.window, board_game, wave, self, x, y, display_hitbox=self.debug))
                elif character_name in OBJECT_CLASSES:
                    ObjectClass = OBJECT_CLASSES[character_name]
                    for x, y in positions:
                        objects.append(ObjectClass(self.window, board_game, wave, self, x, y))
                else:
                    raise ValueError(f"Unknown character name '{character_name}' in the map. It should be either 'MainCharacter' or one of the following: {list(CREATURE_CLASSES.keys()) + list(OBJECT_CLASSES.keys())}.")

        # Main loop
        frame_count = 0
        running = True
        clock = pygame.time.Clock()
        while not(self.isGameOver()) and running:

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update the game state
            keys = pygame.key.get_pressed()

            # Update the creatures
            for creature in creatures:
                creature.update(keys, frame_count)

            # Update the wave simulation
            wave.update()

            # ----------------- Draw the game (SuperDraw function) -----------------
            # Fill the window with white
            self.window.fill((255, 255, 255))

            # Draw the board game
            board_game.draw()

            # Draw the creatures and objects beginning on the top of the window, then the ones on the bottom, to create a depth effect
            # We give priority to the creatures in "catch" state
            creatures_to_draw = [creature for creature in creatures if creature.isInCatchState()]
            others = [creature for creature in creatures if not creature.isInCatchState()] + objects
            others.sort(key=lambda c: c.getYToDraw()) 
            creatures_to_draw =  others + creatures_to_draw

            for creature in creatures_to_draw:
                creature.draw(frame_count)

            # Draw the wave simulation
            wave.draw()

            # Add infos
            creatures[0].drawInfo(frame_count)

            # Update the display
            pygame.display.flip()

            # ------------------------------------------------------------------------

            # Cap the frame rate
            clock.tick(FPS)

            frame_count += 1
        
        return self.getGameOverDic()



if __name__ == "__main__":
    import main