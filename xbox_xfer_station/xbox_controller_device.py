"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin"""
import pygame
import time
#from pygame.constants import JOYAXISMOTION, JOYHATMOTION, JOYBUTTONDOWN, JOYBUTTONUP
import logging

logger = logging.getLogger(__name__)
class XboxControllerDevice(object):
    
    """
    Creates initializes pygame objects needed to interface with hardware 
    and autodetects hardware characteristics such as the number of buttons, hats, or sticks.
    """
    
    def __init__(self):
        """Creates and initializes 
        :attr:`pygame.joystick` object and creates subordinate 
        :attr:`pygame.joystick.Joystick` module.
        
        Initializes joystick hardware.
        Autodetects controller inputs such as hats, sticks and buttons."""
        
        
        self.debug = True
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_init():
            logger.debug("Joystick module initialized!")
            logger.debug("%s joysticks detected." % pygame.joystick.get_count())

        self.joystick = pygame.joystick.Joystick(0)
        logger.debug("Joystick instance created.")
        

        self.joystick.init()
        if self.joystick.get_init():
            print("Joystick initialized:", self.joystick.get_name())
        self.num_buttons = self.joystick.get_numbuttons()
        self.num_hats = self.joystick.get_numhats()
        self.num_axes = self.joystick.get_numaxes()
        
    def close(self):
        """Disconnects and removes modules upon closing application.
        Included in the list of modules to be removed are the 
        :attr:`pygame.joystick` and 
        :attr:`pygame.joystick.Joystick` modules."""
        self.joystick.quit()
        del self.joystick
        pygame.joystick.quit()
        #del pygame.joystick
        pygame.quit()
    
