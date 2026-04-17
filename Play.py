# Generic imports
import pygame
import pygwidgets
import os

# Local imports
from Constants import *
from Bridge import Bridge


class Play:

    def __init__(self, debug=False):

        self.debug = debug
        self.level = 1

        # Initialize pygame
        pygame.init()

        # Create the window
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Echo-step")

        # Background images
        menu_image = pygame.image.load(PATH_TO_MENU + "menu.png").convert()

        # Buttons
        play_button = pygwidgets.CustomButton(self.window, (407, 393), 
                                                   up=PATH_TO_MENU + 'play_button.png', 
                                                   down=PATH_TO_MENU + 'play_button_clicked.png')

        rules_button = pygwidgets.CustomButton(self.window, (430, 556), 
                                                     up=PATH_TO_MENU + 'rules_button.png', 
                                                     down=PATH_TO_MENU + 'rules_button_clicked.png')
        
        quit_button = pygwidgets.CustomButton(self.window, (428, 678), 
                                                    up=PATH_TO_MENU + 'quit.png', 
                                                    down=PATH_TO_MENU + 'quit_clicked.png')

        running = True
        message = "Welcome!"
        map_name = f"Level{self.level}"
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif play_button.handleEvent(event):

                    bridge = Bridge(self.window, debug=self.debug)
                    result = bridge.game(map_name=map_name)

                    if result["final_state"] == "quit":
                        running = False
                    elif result["final_state"] == "win":
                        self.level += 1      
                        message = f"You win !"

                        map_name = f"Level{self.level}"

                        if not os.path.exists(PATH_TO_MAPS + map_name + ".txt"):
                            congratulations_image = pygame.image.load(PATH_TO_MENU + "congratulations.png").convert()
                            quit_congratulations_button = pygwidgets.CustomButton(self.window, (430, 559), 
                                                                        up=PATH_TO_MENU + 'quit_congratulations.png', 
                                                                        down=PATH_TO_MENU + 'quit_congratulations_clicked.png')
                            
                            running2 = True
                            while running2:

                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        running2 = False
                                        running = False
                                        break

                                    if quit_congratulations_button.handleEvent(event):
                                        running2 = False
                                        running = False
                                        break

                                self.window.blit(congratulations_image, (0, 0))

                                quit_congratulations_button.draw()

                                pygame.display.flip()

                    elif result["final_state"] == "lose":
                        message = f"Score : {result['collected_nb_stars']}/{result['total_nb_stars']}"
                    else:
                        raise ValueError(f"Unknown final state '{result['final_state']}'")

                elif rules_button.handleEvent(event):

                    rules_image = pygame.image.load(PATH_TO_MENU + "rules.png").convert()

                    back_button = pygwidgets.CustomButton(self.window, (403, 535), 
                                                                up=PATH_TO_MENU + 'back.png', 
                                                                down=PATH_TO_MENU + 'back_clicked.png')
                    
                    running2 = True
                    while running2:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                running2 = False
                                running = False
                                break

                            if back_button.handleEvent(event):
                                running2 = False

                        self.window.blit(rules_image, (0, 0))

                        back_button.draw()

                        pygame.display.flip()
                
                elif quit_button.handleEvent(event):
                    running = False

            # Draw the menu
            self.window.blit(menu_image, (0, 0))

            play_button.draw()
            rules_button.draw()
            quit_button.draw()
            
            font = pygame.font.Font(PATH_TO_FONTS + "PressStart2P-Regular.ttf", 16)
            color = (40, 42, 46)
            if message:
                text = font.render(message, True, color)
                text_rect = text.get_rect(center=(512, 243))
                self.window.blit(text, text_rect)

            text = font.render("Next level : " + str(self.level), True, color)
            text_rect = text.get_rect(center=(512, 307))
            self.window.blit(text, text_rect)

            pygame.display.flip()

        # Quit pygame
        pygame.quit()


    """def game(self, map_name=DEFAULT_MAP):

        # Create the board game
        board_game = BoardGame(self.window, map_name, debug=self.debug)

        # Bridge
        bridge = Bridge()

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
        creatures.append(MainCharacter(self.window, board_game, wave, bridge, x, y, display_hitbox=self.debug))

        for character_name, positions in init_character_positions.items():
            if character_name != "MainCharacter":
                if character_name in CREATURE_CLASSES:
                    CreatureClass = CREATURE_CLASSES[character_name]
                    for x, y in positions:
                        creatures.append(CreatureClass(self.window, board_game, wave, bridge, x, y, display_hitbox=self.debug))
                elif character_name in OBJECT_CLASSES:
                    ObjectClass = OBJECT_CLASSES[character_name]
                    for x, y in positions:
                        objects.append(ObjectClass(self.window, board_game, wave, bridge, x, y))
                else:
                    raise ValueError(f"Unknown character name '{character_name}' in the map. It should be either 'MainCharacter' or one of the following: {list(CREATURE_CLASSES.keys()) + list(OBJECT_CLASSES.keys())}.")

        # Main loop
        frame_count = 0
        running = True
        clock = pygame.time.Clock()
        result = {"final_state":None, "total_nb_stars": None, "collected_nb_stars": None}
        while not(bridge.isGameOver()) and running:

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    result["final_state"] = "quit"
                    result["total_nb_stars"] = creatures[0].nb_stars_total
                    result["collected_nb_stars"] = creatures[0].nb_stars_collected

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
        
        dic = bridge.getGameOverDic()
        if dic["final_state"] != "quit":
            result["final_state"] = dic["final_state"]
            result["total_nb_stars"] = dic["total_nb_stars"]
            result["collected_nb_stars"] = dic["collected_nb_stars"]
        return result"""

        





if __name__ == "__main__":
    Play(debug=True)
