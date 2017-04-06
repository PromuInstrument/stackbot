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

        self.controller = self.app.hardware['xbox_controller']

        self.set_universal_key_map()
        
    def setup_ui(self):
        self.gui
        
        self.ui_filename = sibling_path(__file__, "Controller.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
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

    def set_universal_key_map(self):
        self.controller.settings.LB.add_listener(self.prev_tab)
        self.controller.settings.RB.add_listener(self.next_tab)
        self.controller.settings.Start.add_listener(self.start_measure)
        self.controller.settings.Back.add_listener(self.interrupt_measure)
    
    def prev_tab(self):
        if self.controller.settings['LB'] == True:
            self.app.ui.mdiArea.activatePreviousSubWindow()
        else:
            pass
            
    def next_tab(self):
        if self.controller.settings['RB'] == True:
            self.app.ui.mdiArea.activateNextSubWindow()
        else:
            pass
        
    def start_measure(self):
        if self.controller.settings['Start'] == True:
            window = self.app.ui.mdiArea.activeSubWindow().widget().windowTitle()
            self.app.measurements['{}'.format(window)].start()
            print(window)
        else:
            pass
    
    def interrupt_measure(self):
        if self.controller.settings['Back'] == True:
            window = self.app.ui.mdiArea.activeSubWindow().widget().windowTitle()
            self.app.measurements['{}'.format(window)].interrupt()
            print(window)
        else: pass
    
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
                    self.log.error("Unknown event type: {}".format(event.type))

