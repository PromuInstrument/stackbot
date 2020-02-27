"""Xbox ScopeFoundry demonstration module written by Alan Buckley with suggestions for improvement 
from Ed Barnard and Lev Lozhkin"""
from __future__ import absolute_import
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import Measurement

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