"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin"""
from __future__ import absolute_import
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import Measurement
import time
import pygame.event
from pygame.constants import JOYAXISMOTION, JOYHATMOTION, JOYBUTTONDOWN, JOYBUTTONUP
from _pylief import NONE


class XboxControllerTestMeasure(Measurement):

    name = 'xbox_controller_test_measure'
    
    def __init__(self, app, name=None, hw_name="xbox_controller"):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)
        
    def setup(self):
        self.controller = self.app.hardware[self.hw_name]
        
    def setup_figure(self):
        
        self.ui_filename = sibling_path(__file__, "Controller.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        #self.ui.setWindowTitle(self.name)
        
        # Buttons
        self.controller.A.connect_bidir_to_widget(self.ui.a_radio)
        self.controller.B.connect_bidir_to_widget(self.ui.b_radio)
        self.controller.X.connect_bidir_to_widget(self.ui.x_radio)
        self.controller.Y.connect_bidir_to_widget(self.ui.y_radio)
        self.controller.LB.connect_bidir_to_widget(self.ui.LB_radio)
        self.controller.RB.connect_bidir_to_widget(self.ui.RB_radio)
        self.controller.ls_lr.connect_bidir_to_widget(self.ui.ls_hdsb)
        self.controller.ls_ud.connect_bidir_to_widget(self.ui.ls_vdsb)
        self.controller.rs_lr.connect_bidir_to_widget(self.ui.rs_hdsb)
        self.controller.rs_ud.connect_bidir_to_widget(self.ui.rs_vdsb)
        self.controller.triggers.connect_bidir_to_widget(self.ui.trig_dsb)
        self.controller.Back.connect_bidir_to_widget(self.ui.back_radio)
        self.controller.Start.connect_bidir_to_widget(self.ui.start_radio)
        self.controller.LP.connect_bidir_to_widget(self.ui.lpress)
        self.controller.RP.connect_bidir_to_widget(self.ui.rpress)
        
        # Dpad positions
        self.controller.N.connect_bidir_to_widget(self.ui.north)
        self.controller.NW.connect_bidir_to_widget(self.ui.northwest)
        self.controller.W.connect_bidir_to_widget(self.ui.west)
        self.controller.SW.connect_bidir_to_widget(self.ui.southwest)
        self.controller.S.connect_bidir_to_widget(self.ui.south)
        self.controller.SE.connect_bidir_to_widget(self.ui.southeast)
        self.controller.E.connect_bidir_to_widget(self.ui.east)
        self.controller.NE.connect_bidir_to_widget(self.ui.northeast)
        self.controller.origin.connect_bidir_to_widget(self.ui.origin)
        
        # Controller name readout in ui element
        self.controller.controller_name.connect_bidir_to_widget(self.ui.control_name_field)
        
    def run(self):
            """This function is run after having clicked "start" in the ScopeFoundry GUI.
            It essentially runs and listens for Pygame event signals and updates the status
            of every button in a specific category (such as hats, sticks, or buttons) in
            intervals of self.dt seconds."""
            self.log.debug("run")
            
            #Access equipment class:
            self.controller.connect()
            self.xb_dev = self.controller.xb_dev 
            self.joystick = self.xb_dev.joystick
            
            self.log.debug("ran")
            
            self.controller.settings['Controller_Name'] = self.joystick.get_name()
            
            while not self.interrupt_measurement_called:  
                time.sleep(self.dt)
                event_list = pygame.event.get()
                for event in event_list:
                    if event.type == pygame.JOYAXISMOTION:
                        for i in range(self.xb_dev.num_axes):
                            self.controller.settings['Axis_' + str(i)] = self.joystick.get_axis(i)
    
                    elif event.type == pygame.JOYHATMOTION:
                        for i in range(self.xb_dev.num_hats):
                            # Clear Directional Pad values
                            for k in set(self.direction_map.values()):
                                self.controller.settings[k] = False
    
                            # Check button status and record it
                            resp = self.joystick.get_hat(i)
                            try:
                                self.controller.settings[self.direction_map[resp]] = True
                            except KeyError:
                                self.log.error("Unknown dpad hat: "+ repr(resp))
    
                    elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
                        button_state = (event.type == pygame.JOYBUTTONDOWN)
    
                        for i in range(self.xb_dev.num_buttons):
                            if self.joystick.get_button(i) == button_state:
                                try:
                                    self.controller.settings[self.button_map[i]] = button_state
                                except KeyError:
                                    self.log.error("Unknown button: %i (target state: %s)" % (i,
                                        'down' if button_state else 'up'))
    
                    else:
                        self.log.error("Unknown event type: {} {}".format(event, event.type))