'''
Created on Feb 2, 2018

@author: Alan Buckley     <alanbuckley@lbl.gov>
                            <alanbuckley@berkeley.edu>
                            
'''

from ScopeFoundryHW.ALD.Lovebox.pid_controller import PIDController
from ScopeFoundry import HardwareComponent

class LoveboxHW(HardwareComponent):
    
    name = 'lovebox'
    CTRL_METHODS = ("PID", "ON/OFF", "Manual")
    
    initial_PID_defaults = (30.0, 28, 7)
    desired_PID_profile = (50.0, 30, 10)
#     CTRL_METHODS = ("PID", "ON/OFF", "Manual", "PID Program Ctrl")
#     HEAT_COOL_CTRLS = ("Heating")

    def setup(self):
        self.active_profile = self.initial_PID_defaults
        self.settings.New(name='port', initial='COM4', dtype=str, ro=False)
        self.settings.New(name='control_method', initial='PID', dtype=str, choices=self.CTRL_METHODS, ro=False)
        self.settings.New(name='heat_cool_control', initial='Heating', dtype=str, ro=True)
        self.settings.New(name='pv_temp', initial=0.0, dtype=float, spinbox_decimals=1, ro=True)
        self.settings.New(name='sv_setpoint', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        self.settings.New(name='output1', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        self.settings.New(name='Proportional_band', initial=self.active_profile[0], dtype=float, spinbox_decimals=1, ro=False, vmin=0.1, vmax=999.9)
        self.settings.New(name='Integral_time', initial=self.active_profile[1], dtype=int, ro=False, vmin=0, vmax=9999)
        self.settings.New(name='Derivative_time', initial=self.active_profile[2], dtype=int, ro=False, vmin=0, vmax=9999)
        self.settings.New(name='PID_preset', initial=1, dtype=int, ro=False, vmin=0, vmax=4)
        self.settings.New(name='PID_SV', initial=0.0, dtype=float, ro=False)
        
#         self.settings.New(name='Run', initial=True, dtype=bool, ro=False)
#         self.settings.New(name='Run PID', initial=False, dtype=bool, ro=False)
         
#         lq.change_ro(True)
        
    def connect(self):
        self.lovebox = PIDController(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
        self.settings.get_lq('control_method').connect_to_hardware(
                                                    write_func=self.set_control_method,
                                                    read_func=self.lovebox.read_ctrl_method)
        self.settings.get_lq('heat_cool_control').connect_to_hardware(
                                                    write_func=self.set_heat_cool_control,
                                                    read_func=self.lovebox.read_heat_cool_ctrl)
        
        self.settings.get_lq('sv_setpoint').connect_to_hardware(
                                                    write_func=self.lovebox.set_setpoint,
                                                    read_func=self.lovebox.read_setpoint)
        
        self.settings.get_lq('pv_temp').connect_to_hardware(
                                                    read_func=self.lovebox.read_temp)
        
        self.settings.get_lq('output1').connect_to_hardware(
                                                    write_func=self.lovebox.set_output1,
                                                    read_func=self.lovebox.read_output1)

        self.settings.get_lq('Proportional_band').connect_to_hardware(
                                                    write_func=self.lovebox.set_prop_band,
                                                    read_func=self.lovebox.read_prop_band)
        
        self.settings.get_lq('Integral_time').connect_to_hardware(
                                                    write_func=self.lovebox.set_integral_time,
                                                    read_func=self.lovebox.read_integral_time)
        
        self.settings.get_lq('Derivative_time').connect_to_hardware(
                                                    write_func=self.lovebox.set_derivative_time,
                                                    read_func=self.lovebox.read_derivative_time)
        
        self.settings.get_lq('PID_preset').connect_to_hardware(
                                                    write_func=self.lovebox.set_pid_preset,
                                                    read_func=self.lovebox.read_pid_preset)
        
        self.settings.get_lq('PID_SV').connect_to_hardware(
                                                    write_func=self.lovebox.set_pid_sv,
                                                    read_func=self.lovebox.read_pid_sv)

#         self.settings.get_lq('Run').connect_to_hardware(
#                                                     write_func=self.lovebox.set_ctrl_run,
#                                                     read_func=self.lovebox.read_ctrl_run)
#         
#         self.settings.get_lq('Run PID').connect_to_hardware(
#                                                     write_func=self.lovebox.set_pid_ctrl_run,
#                                                     read_func=self.lovebox.read_pid_ctrl_run)


        self.set_control_method(self.settings['control_method'])

               
        if self.lovebox.read_ctrl_method()[1] == 'PID':
            '''Force update of LQs since direct update does not work.'''
            p, i, d = self.active_profile
            self.lovebox.set_prop_band(p)
            self.lovebox.set_integral_time(i)
            self.lovebox.set_derivative_time(d)

            

    def set_control_method(self, control):
        select = self.CTRL_METHODS.index(control)
        self.lovebox.set_ctrl_method(select)
        
    def set_heat_cool_control(self, control):
        select = self.HEAT_COOL_CTRLS.index(control)
        self.lovebox.set_heat_cool_ctrl(select)
        

        
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'lovebox'):
            self.lovebox.close()
            del self.lovebox
        