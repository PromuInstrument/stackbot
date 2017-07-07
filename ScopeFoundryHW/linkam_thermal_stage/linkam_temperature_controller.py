from ScopeFoundry import HardwareComponent
from equipment.linkam_controller import LinkamController
from PySide import QtCore

class LinkamControllerHC(HardwareComponent):
    
    name = 'LinkamController'
    
    def setup(self):
        
        self.temperature = self.add_logged_quantity('temperature', dtype=float, si=False, unit='C', 
                                                    ro=True)
        self.limit = self.add_logged_quantity('limit', dtype=float, si=False, unit='C', ro=False, 
                                              vmin=-196, vmax=500)
        self.rate = self.add_logged_quantity('rate', dtype=float, si=False, unit='C/min', ro=False,
                                             vmin=0.01)
        self.pump_speed = self.add_logged_quantity('pump_speed', dtype=int, unit='', ro=False,
                                                   vmin=0, vmax=30, si=False)
        self.pump_manual_mode = self.add_logged_quantity('pump_manual_mode', dtype=bool, ro=False)
        self.port = self.add_logged_quantity('port', dtype=str, initial='COM7')
        
        self.status = self.add_logged_quantity('status', dtype=str, ro=True)
        self.error = self.add_logged_quantity('error', dtype=str, ro=True)
        
        self.add_operation('Refresh', self.read_linkam_state)
        self.add_operation('Start', self.start_profile)
        self.add_operation('Stop', self.stop_profile)
        self.add_operation('Hold', self.hold_current)
        
        
    def connect(self):
        
        # Open connection to hardware
        self.port.change_readonly(True)

        self.linkam = LinkamController(port=self.port.val, 
                                           debug=self.debug_mode.val)

        # connect logged quantities       
        self.temperature.hardware_read_func = self.linkam.read_temperature
        
        self.limit.hardware_read_func = self.linkam.read_limit
        self.limit.hardware_set_func = self.linkam.write_limit
        
        self.rate.hardware_read_func = self.linkam.read_rate
        self.rate.hardware_set_func = self.linkam.write_rate
        
        self.pump_speed.hardware_read_func = self.linkam.read_pump_speed
        self.pump_speed.hardware_set_func = self.linkam.write_pump_speed
        
        self.pump_manual_mode.hardware_read_func = self.linkam.read_pump_mode
        self.pump_manual_mode.hardware_set_func = self.linkam.write_pump_mode
        
        self.status.hardware_read_func = self.linkam.read_status
        
        self.error.hardware_read_func = self.linkam.read_error
        
         
    def disconnect(self):
        self.port.change_readonly(False)

        #disconnect hardware
        self.linkam.close()
        
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        del self.linkam
    
    @QtCore.Slot()
    def read_linkam_state(self):
        self.linkam.update_status()
        for lq in self.logged_quantities.values():
            lq.read_from_hardware()
    
    @QtCore.Slot()
    def start_profile(self):
        self.linkam.start()
    
    @QtCore.Slot()
    def stop_profile(self):
        self.linkam.stop()
    
    @QtCore.Slot()
    def hold_current(self):
        self.linkam.hold()