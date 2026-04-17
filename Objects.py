# Generic imports
import pygame
from math import sin


# Local imports
from Constants import *


class Object:

    id = 0

    def __init__(self, 
                 window, 
                 board_game, 
                 wave, bridge, 
                 x, y, 
                 name="Star",
                 path_to_image=PATH_TO_STAR_IMAGE):
        
        self.window = window
        self.board_game = board_game
        self.wave = wave
        self.bridge = bridge
        self.name = f"{name}_{Object.id}" if self.bridge.isRegistered(name) else name
        self.bridge.register_object(self)
        Object.id += 1

        self.x = x
        self.y = y
        self.z = self.board_game.getMicroAltitude(x, y) 
        self.ground_z = self.board_game.getMacroAltitude(self.x, self.y)

        self.y_to_draw = self.y

        self.image = pygame.image.load(path_to_image).convert_alpha()
        self.WIDTH = self.image.get_width()
        self.HEIGHT = self.image.get_height()


    def draw(self, frame_count):
        """
            Draw the object on the window
        """
        pos_x = self.x - self.WIDTH // 2
        self.getYToDraw()

        self.window.blit(self.image, (pos_x, self.y_to_draw))

    
    def getYToDraw(self):
        """
            Get the y coordinate to draw the object, taking into account its z coordinate and the ground altitude
        """
        ground_z = self.board_game.getMacroAltitude(self.x, self.y)
        jump_height = self.z - ground_z
        self.y_to_draw = self.y - self.HEIGHT - int(jump_height * TILE_SIZE // 2)
        return self.y_to_draw




    



class Star(Object):

    stars_list = []

    def __init__(self, window, board_game, wave, bridge, x, y, debug = False):
        super().__init__(window, board_game, wave, bridge, x, y, name="Star", path_to_image=PATH_TO_STAR_IMAGE)
        Star.stars_list.append(self.name)
        self.debug = debug


    def clear():
        Star.stars_list = []
        
    
    def _actualiseZ(self, frame_count):
        """
            Actualise the z coordinate of the star
        """
        self.z = self.ground_z + 0.5 * sin(frame_count * 0.075)


    def draw(self, frame_count):
        """
            Draw the star on the window
        """
        self._actualiseZ(frame_count)
        super().draw(frame_count)

        if self.debug:
            # Draw the Anchor point
            pygame.draw.circle(self.window, (255, 0, 0), (self.x, self.y), 5)


    def receiveEvent(self, event, sender_name):
        """
            Receive an event from a creature
        """
        if event == "collected":
            Star.stars_list.remove(self.name)
            self.image = pygame.image.load(PATH_TO_EMPTY_STAR_IMAGE).convert_alpha() # Replace with collected star image



OBJECT_CLASSES = {
    "Star": Star
}




if __name__ == "__main__":
    import main