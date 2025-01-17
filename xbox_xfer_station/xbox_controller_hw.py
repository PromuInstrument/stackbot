"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin


Updated by Edward Barnard 2019-09-25
"""
from __future__ import absolute_import
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.xbox_controller.xbox_controller_device import XboxControllerDevice
import pygame


class XboxControllerHW(HardwareComponent):

    """Defines button maps and *LoggedQuantities* used to 
    interpret signals received by Pygame module from controller."""

    name = "xbox_controller"

    direction_map = {
        (0,1): 'N', 
        (-1,1): 'NW',
        (-1,0): 'W',
        (-1,-1): 'SW',
        (0,-1): 'S',
        (1,-1): 'SE',
        (1,0): 'E',
        (1,1): 'NE',
        (0,0): 'Origin'}
    button_map = {
        0: 'A',
        1: 'B',
        2: 'X',
        3: 'Y',
        4: 'LB',
        5: 'RB',
        6: 'Back',
        7: 'Start',
        8: 'LP',
        9: 'RP'}
    
    def __init__(self, app, debug=False, name=None):
        self.xb_dev = XboxControllerDevice()
        
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    def setup(self):
        """Create logged quantities for each HID object including all hats, 
        sticks and buttons specific to the Xbox controller."""
        self.ls_lr = self.settings.New(name='Axis_0', initial=0,
                                            dtype=float, fmt="%.3f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.ls_ud = self.settings.New(name='Axis_1', initial=0,
                                            dtype=float, fmt="%.3f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.triggers = self.settings.New(name='Axis_2', initial=0,
                                            dtype=float, fmt="%.3f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.rs_ud = self.settings.New(name='Axis_3', initial=0,
                                            dtype=float, fmt="%.3f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.rs_lr = self.settings.New(name='Axis_4', initial=0,
                                            dtype=float, fmt="%.3f", 
                                            ro=True, vmin=-1.0, vmax=1.0)

        self.axis5 = self.settings.New(name='Axis_5', initial=0,
                                            dtype=float, fmt="%.3f", 
                                            ro=True, vmin=-1.0, vmax=1.0)

        self.settings.New(name="sensitivity", initial=1.0, dtype=float, fmt="%.3f", ro=False, vmin=-5.0, vmax=5.0)
        
        self.A = self.settings.New(name='A', initial=0,
                                            dtype=bool, ro=True)
        self.B = self.settings.New(name='B', initial=0,
                                            dtype=bool, ro=True)
        self.X = self.settings.New(name='X', initial=0,
                                            dtype=bool, ro=True)
        self.Y = self.settings.New(name='Y', initial=0,
                                            dtype=bool, ro=True)
        self.LB = self.settings.New(name='LB', initial=0,
                                            dtype=bool, ro=True)
        self.RB = self.settings.New(name='RB', initial=0,
                                    dtype=bool, ro=True)
        self.Back = self.settings.New(name='Back', initial=0,
                                    dtype=bool, ro=True)
        self.Start = self.settings.New(name="Start", initial=0,
                                    dtype=bool, ro=True)
        self.LP = self.settings.New(name="LP", initial=0,
                                    dtype=bool, ro=True)
        self.RP = self.settings.New(name="RP", initial=0,
                                    dtype=bool, ro=True)
        
        self.N = self.settings.New(name='N', initial=0,
                                    dtype=bool, ro=True)
        self.NW = self.settings.New(name='NW', initial=0,
                                    dtype=bool, ro=True)
        self.W = self.settings.New(name='W', initial=0,
                                    dtype=bool, ro=True)
        self.SW = self.settings.New(name='SW', initial=0,
                                    dtype=bool, ro=True)
        self.S = self.settings.New(name='S', initial=0,
                                    dtype=bool, ro=True)
        self.SE = self.settings.New(name='SE', initial=0,
                                    dtype=bool, ro=True)
        self.E = self.settings.New(name='E', initial=0,
                                    dtype=bool, ro=True)
        self.NE = self.settings.New(name='NE', initial=0, 
                                    dtype=bool, ro=True)
        self.origin = self.settings.New(name='Origin', initial=0,
                                    dtype=bool, ro=True)
        
        ## This logged quantity is meant to display the name of the connected controller.
        self.controller_name = self.settings.New(name="Controller_Name", initial="None",
                                    dtype=str, ro=True)
        self.settings.New("joystick_id", dtype=int, initial=0)
        
    def connect(self):
        """Creates joystick object and connects to controller upon clicking "connect" in ScopeFoundry app."""
        # Reference to equipment level joystick object
        #self.xb_dev = XboxControllerDevice()
        #self.joystick = self.xb_interface.joystick
        
        
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_init():
            self.log.debug("Joystick module initialized!")
            self.log.debug("%s joysticks detected." % pygame.joystick.get_count())

        self.joystick = pygame.joystick.Joystick(self.settings['joystick_id'])
        self.log.debug("Joystick instance created.")
        

        self.joystick.init()
        if self.joystick.get_init():
            print("Joystick initialized:", self.joystick.get_name())
        self.num_buttons = self.joystick.get_numbuttons()
        self.num_hats = self.joystick.get_numhats()
        self.num_axes = self.joystick.get_numaxes()
        
        self.settings['Controller_Name'] = self.joystick.get_name()
        
        
    def disconnect(self):
        """Disconnects and removes modules when no longer needed by the application."""
        
        """Disconnects and removes modules upon closing.
        Included in the list of modules to be removed are the 
        :attr:`pygame.joystick` and 
        :attr:`pygame.joystick.Joystick` modules."""
        
        if hasattr(self, "joystick"):
            self.joystick.quit()
            del self.joystick
        pygame.joystick.quit()
        #del pygame.joystick
        pygame.quit()
        
    
    def threaded_update(self): 
        #event_list = pygame.event.get()
        #for event in event_list:
        
        event = pygame.event.wait()
        
        if event.type == pygame.JOYAXISMOTION:
            for i in range(self.num_axes):
                self.settings['Axis_' + str(i)] = self.joystick.get_axis(i)

        elif event.type == pygame.JOYHATMOTION:
            for i in range(self.num_hats):
                # Clear Directional Pad values
                for k in set(self.direction_map.values()):
                    self.settings[k] = False

                # Check button status and record it
                resp = self.joystick.get_hat(i)
                try:
                    self.settings[self.direction_map[resp]] = True
                except KeyError:
                    self.log.error("Unknown dpad hat: "+ repr(resp))

        elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
            button_state = (event.type == pygame.JOYBUTTONDOWN)

            for i in range(self.num_buttons):
                if self.joystick.get_button(i) == button_state:
                    try:
                        self.settings[self.button_map[i]] = button_state
                    except KeyError:
                        self.log.error("Unknown button: %i (target state: %s)" % (i,
                            'down' if button_state else 'up'))

        else:
            self.log.debug("Unknown event type: {} {}".format(event, event.type))



        