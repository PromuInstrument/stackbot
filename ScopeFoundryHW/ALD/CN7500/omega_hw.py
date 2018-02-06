'''
Created on Feb 2, 2018

@author: Alan Buckley     <alanbuckley@lbl.gov>
                            <alanbuckley@berkeley.edu>
                            
'''

from ScopeFoundryHW.ALD.CN7500.omega_pid_controller import OmegaPIDController
from ScopeFoundry import HardwareComponent

class OmegaHW(HardwareComponent):
    
    name = 'omega'
    
    CTRL_METHODS = ("PID", "ON/OFF", "Manual", "PID Program Ctrl")
    HEAT_COOL_CTRLS = ("Heating", "Cooling", "Heating/Cooling", "Cooling/Heating")

    def setup(self):
        self.settings.New(name='port', initial='COM1', dtype=str, ro=False)
        self.settings.New(name='control_method', initial='PID', dtype=str, choices=self.CTRL_METHODS, ro=False)
        self.settings.New(name='heat_cool_control', initial='Heating', dtype=str, choices=self.HEAT_COOL_CTRLS, ro=False)
        self.settings.New(name='pv_temp', initial=0.0, dtype=float, spinbox_decimals=1, ro=True)
        self.settings.New(name='sv_setpoint', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        self.settings.New(name='output1', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        self.settings.New(name='output2', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        
#         lq.change_ro(True)
        
    def connect(self):
        self.omega = OmegaPIDController(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
        self.settings.get_lq('control_method').connect_to_hardware(
                                                    write_func=self.set_control_method,
                                                    read_func=self.omega.read_ctrl_method)
        self.settings.get_lq('heat_cool_control').connect_to_hardware(
                                                    write_func=self.set_heat_cool_control,
                                                    read_func=self.omega.read_heat_cool_ctrl)
        
        self.settings.get_lq('sv_setpoint').connect_to_hardware(
                                                    write_func=self.omega.set_setpoint,
                                                    read_func=self.omega.read_setpoint)
        
        self.settings.get_lq('pv_temp').connect_to_hardware(
                                                    read_func=self.omega.read_temp)
        
        self.settings.get_lq('output1').connect_to_hardware(
                                                    write_func=self.omega.set_output1,
                                                    read_func=self.omega.read_output1)
        self.settings.get_lq('output2').connect_to_hardware(
                                                    write_func=self.omega.set_output2,
                                                    read_func=self.omega.read_output2)
        
        
    def set_control_method(self, control):
        select = self.CTRL_METHODS.index(control)
        self.omega.set_ctrl_method(select)
        
    def set_heat_cool_control(self, control):
        select = self.HEAT_COOL_CTRLS.index(control)
        self.omega.set_heat_cool_ctrl(select)
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'omega'):
            self.omega.close()
            del self.omega
        