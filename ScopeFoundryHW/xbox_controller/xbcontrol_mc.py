"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin"""
from __future__ import absolute_import
from ScopeFoundry.measurement import Measurement
import time
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pygame.event
from pygame.constants import JOYAXISMOTION, JOYHATMOTION, JOYBUTTONDOWN, JOYBUTTONUP

class XboxControlMeasure(Measurement):
    """This class contains connections to logged quantities and ui elements. 
    Dicts included under class header are referenced by functions and are used as a kind of 
    directory to interpret different signals emitted by the Pygame module."""
    name = "xbcontrol_mc"
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

    def setup(self):
        """Update interval and connections to subordinate classes 
        (hardware and equipment level) are established here.
        Controller name logged quantity referenced below is meant to
        tell the user the name of the connected device as a sanity check."""
        self.dt = 0.05
        self.gui
        
        self.ui_filename = sibling_path(__file__, "Controller.ui")
        # UI
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        self.hw = self.app.hardware['xbox_controller']

        
        # Buttons
        self.hw.A.connect_bidir_to_widget(self.ui.a_radio)
        self.hw.B.connect_bidir_to_widget(self.ui.b_radio)
        self.hw.X.connect_bidir_to_widget(self.ui.x_radio)
        self.hw.Y.connect_bidir_to_widget(self.ui.y_radio)
        self.hw.LB.connect_bidir_to_widget(self.ui.LB_radio)
        self.hw.RB.connect_bidir_to_widget(self.ui.RB_radio)
        self.hw.ls_lr.connect_bidir_to_widget(self.ui.ls_hdsb)
        self.hw.ls_ud.connect_bidir_to_widget(self.ui.ls_vdsb)
        self.hw.rs_lr.connect_bidir_to_widget(self.ui.rs_hdsb)
        self.hw.rs_ud.connect_bidir_to_widget(self.ui.rs_vdsb)
        self.hw.triggers.connect_bidir_to_widget(self.ui.trig_dsb)
        self.hw.Back.connect_bidir_to_widget(self.ui.back_radio)
        self.hw.Start.connect_bidir_to_widget(self.ui.start_radio)
        self.hw.LP.connect_bidir_to_widget(self.ui.lpress)
        self.hw.RP.connect_bidir_to_widget(self.ui.rpress)
        
        # Dpad positions
        self.hw.N.connect_bidir_to_widget(self.ui.north)
        self.hw.NW.connect_bidir_to_widget(self.ui.northwest)
        self.hw.W.connect_bidir_to_widget(self.ui.west)
        self.hw.SW.connect_bidir_to_widget(self.ui.southwest)
        self.hw.S.connect_bidir_to_widget(self.ui.south)
        self.hw.SE.connect_bidir_to_widget(self.ui.southeast)
        self.hw.E.connect_bidir_to_widget(self.ui.east)
        self.hw.NE.connect_bidir_to_widget(self.ui.northeast)
        self.hw.origin.connect_bidir_to_widget(self.ui.origin)
        
        # Controller name readout in ui element
        self.hw.controller_name.connect_bidir_to_widget(self.ui.control_name_field)

    def run(self):
        """This function is run after having clicked "start" in the ScopeFoundry GUI.
        It essentially runs and listens for Pygame event signals and updates the status
        of every button in a specific category (such as hats, sticks, or buttons) in
        intervals of self.dt seconds."""
        self.log.debug("run")
        
        #Access equipment class:
        self.hw.connect()
        self.xb_dev = self.hw.xb_dev 
        self.joystick = self.xb_dev.joystick
        
        self.log.debug("ran")
        
        self.hw.settings['Controller_Name'] = self.joystick.get_name()
        
        while not self.interrupt_measurement_called:  
            time.sleep(self.dt)
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.JOYAXISMOTION:
                    for i in range(self.xb_dev.num_axes):
                        self.hw.settings['Axis_' + str(i)] = self.joystick.get_axis(i)

                elif event.type == pygame.JOYHATMOTION:
                    for i in range(self.xb_dev.num_hats):
                        # Clear Directional Pad values
                        for k in set(self.direction_map.values()):
                            self.hw.settings[k] = False

                        # Check button status and record it
                        resp = self.joystick.get_hat(i)
                        try:
                            self.hw.settings[self.direction_map[resp]] = True
                        except KeyError:
                            self.log.error("Unknown dpad hat: "+ repr(resp))

                elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
                    button_state = (event.type == pygame.JOYBUTTONDOWN)

                    for i in range(self.xb_dev.num_buttons):
                        if self.joystick.get_button(i) == button_state:
                            try:
                                self.hw.settings[self.button_map[i]] = button_state
                            except KeyError:
                                self.log.error("Unknown button: %i (target state: %s)" % (i,
                                    'down' if button_state else 'up'))

                else:
                    self.log.error("Unknown event type: {}".format(event.type))

