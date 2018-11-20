from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryHW.linkam_thermal_stage.linkam_controller import LinkamController
except Exception as err:
    print("Could not load modules needed for AndorCCD:", err)


class LinkamControllerHC(HardwareComponent):
    
    name = 'LinkamController'
    
    def setup(self):
        self.debug = True
        
        self.settings.New('temperature', dtype=float, si=False, unit='C', ro=True)
               
        #self.temperature = self.add_logged_quantity('temperature', dtype=float, si=False, unit='C', 
        #                                            ro=True)
        
        self.settings.New('limit', dtype=float, si=False, unit='C', ro=False, 
                                              vmin=-196, vmax=500)
        #self.limit = self.add_logged_quantity('limit', dtype=float, si=False, unit='C', ro=False, 
        #                                      vmin=-196, vmax=500)
        
        self.settings.New('rate', dtype=float, si=False, unit='C/min', ro=False,
                                             vmin=0.01)
        #self.rate = self.add_logged_quantity('rate', dtype=float, si=False, unit='C/min', ro=False,
        #                                     vmin=0.01)
        
        self.settings.New('pump_speed', dtype=int, unit='', ro=False,
                                                   vmin=0, vmax=30, si=False)
        #self.pump_speed = self.add_logged_quantity('pump_speed', dtype=int, unit='', ro=False,
        #                                           vmin=0, vmax=30, si=False)
        
        self.settings.New('pump_manual_mode', dtype=bool, ro=False)
        #self.pump_manual_mode = self.add_logged_quantity('pump_manual_mode', dtype=bool, ro=False)
        
        self.settings.New('port', dtype=str, initial='COM1')
        #self.port = self.add_logged_quantity('port', dtype=str, initial='COM7')
        
        self.settings.New('status', dtype=str, ro=True)
        #self.status = self.add_logged_quantity('status', dtype=str, ro=True)
        
        self.settings.New('error', dtype=str, ro=True)
        #self.error = self.add_logged_quantity('error', dtype=str, ro=True)
        
        self.add_operation('Refresh', self.read_linkam_state)
        self.add_operation('Start', self.start_profile)
        self.add_operation('Stop', self.stop_profile)
        self.add_operation('Hold', self.hold_current)
        
        
    def connect(self):
        
        # Open connection to hardware
        self.settings.port.change_readonly(True)

        self.linkam = LinkamController(port=self.settings.port.val, 
                                           debug=self.debug_mode.val)

        # connect logged quantities       
        self.settings.temperature.connect_to_hardware(
            read_func = self.linkam.read_temperature
            )
        
        self.settings.limit.connect_to_hardware(
            read_func = self.linkam.read_limit,
            write_func = self.linkam.write_limit
            )
        
        self.settings.rate.connect_to_hardware(
            read_func = self.linkam.read_rate,
            write_func = self.linkam.write_rate
            )
        
        self.settings.pump_speed.connect_to_hardware(
            read_func = self.linkam.read_pump_speed,
            write_func = self.linkam.write_pump_speed
            )
        
        self.settings.pump_manual_mode.connect_to_hardware(
            read_func = self.linkam.read_pump_mode,
            write_func = self.linkam.write_pump_mode
            )
        
        self.settings.status.connect_to_hardware(
            read_func = self.linkam.read_status
            )
        
        self.settings.error.connect_to_hardware(
            read_func = self.linkam.read_error
            )
        
         
    def disconnect(self):
        self.settings.port.change_readonly(False)

        
        
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        # clean up hardware object
        if hasattr(self, 'linkam'):
            self.linkam.close()
            del self.linkam
    
    #@QtCore.Slot()
    def read_linkam_state(self):
        self.linkam.update_status()
        keys_to_update = ['temperature', 'limit', 'rate', 'pump_speed',
                          'pump_manual_mode', 'status', 'error']
        for key in keys_to_update:
            self.settings.get_lq(key).read_from_hardware()
    
    #@QtCore.Slot()
    def start_profile(self):
        self.linkam.start()
    
    #@QtCore.Slot()
    def stop_profile(self):
        self.linkam.stop()
    
    #@QtCore.Slot()
    def hold_current(self):
        self.linkam.hold()