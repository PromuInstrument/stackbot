'''
Created on Feb 2, 2018

@author: Alan Buckley     <alanbuckley@lbl.gov>
                            <alanbuckley@berkeley.edu>
Updated  Edward Barnard 2019-01-14
'''

from .omega_pid_controller import PIDController
from ScopeFoundry import HardwareComponent

class OmegaPIDHW(HardwareComponent):
    """
    Hardware component wrapper for use with Dwyer Love Controls Series 4B 
    PID Temperature controller.
    In theory, this hardware component should be compatible with other 
    commonly available temperature controllers such as the Omega Engineering CN7600 
    since they use the same command library.
    """
    name = 'omega_pid'
    CTRL_METHODS = ("PID", "ON/OFF", "Manual", "PID_Program")
    HEAT_COOL_CTRLS = ("Heating")
    
    #initial_PID_defaults = (30.0, 28, 7)
    #desired_PID_profile = (7.7, 53, 13)

    def setup(self):
        #self.active_profile = self.desired_PID_profile
        self.settings.New(name='port', initial='COM1', dtype=str, ro=False)
        self.settings.New(name='address', dtype=int, initial=1)
        self.settings.New(name='control_method', initial='ON/OFF', dtype=str, choices=self.CTRL_METHODS, ro=False)
        self.settings.New(name='heat_cool_control', initial='Heating', dtype=str, ro=True)
        self.settings.New(name='pv_temp', initial=0.0, dtype=float, spinbox_decimals=1, ro=True)
        self.settings.New(name='sv_setpoint', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        self.settings.New(name='output1', initial=0.0, dtype=float, spinbox_decimals=1, ro=False)
        self.settings.New(name='Proportional_band',  dtype=float, spinbox_decimals=1, ro=False, vmin=0.1, vmax=999.9)
        self.settings.New(name='Integral_time',  dtype=int, ro=False, vmin=0, vmax=9999)
        self.settings.New(name='Derivative_time',  dtype=int, ro=False, vmin=0, vmax=9999)
        self.settings.New(name='PID_preset', initial=1, dtype=int, ro=False, vmin=0, vmax=4)
        self.settings.New(name='PID_SV', initial=0.0, dtype=float, ro=False)
        
        self.shared_port_controller_hw = None
        
    def connect(self):
        S = self.settings
        
        if S['port'].startswith('hw:'):
            self.shared_port_controller_hw = self.app.hardware[S['port'].split(':')[-1]]
            self.shared_port_controller_hw.settings['connected'] = True

            self.dev = PIDController(port=S['port'], address = S['address'],
                                     debug=S['debug_mode'], 
                                     shared_port_controller=self.shared_port_controller_hw.dev)
        
        else:
            self.shared_port_controller_hw = None
            self.dev = PIDController(port=S['port'], address = S['address'],
                                     debug=S['debug_mode'])
    
        S.get_lq('control_method').connect_to_hardware(
                                                    write_func=self.set_control_method,
                                                    read_func=self.dev.read_ctrl_method)
        S.get_lq('heat_cool_control').connect_to_hardware(
                                                    write_func=self.set_heat_cool_control,
                                                    read_func=self.dev.read_heat_cool_ctrl)
        
        S.get_lq('sv_setpoint').connect_to_hardware(
                                                    write_func=self.dev.set_setpoint,
                                                    read_func=self.dev.read_setpoint)
        
        S.get_lq('pv_temp').connect_to_hardware(
                                                    read_func=self.dev.read_temp)
        
        S.get_lq('output1').connect_to_hardware(
                                                    write_func=self.dev.set_output1,
                                                    read_func=self.dev.read_output1)

        S.get_lq('Proportional_band').connect_to_hardware(
                                                    write_func=self.dev.set_prop_band,
                                                    read_func=self.dev.read_prop_band)
        
        S.get_lq('Integral_time').connect_to_hardware(
                                                    write_func=self.dev.set_integral_time,
                                                    read_func=self.dev.read_integral_time)
        
        S.get_lq('Derivative_time').connect_to_hardware(
                                                    write_func=self.dev.set_derivative_time,
                                                    read_func=self.dev.read_derivative_time)
        
        S.get_lq('PID_preset').connect_to_hardware(
                                                    write_func=self.dev.set_pid_preset,
                                                    read_func=self.dev.read_pid_preset)
        
#         S.get_lq('PID_SV').connect_to_hardware(
#                                                     write_func=self.dev.set_pid_sv,
#                                                     read_func=self.dev.read_pid_sv)

#         S.get_lq('Run').connect_to_hardware(
#                                                     write_func=self.dev.set_ctrl_run,
#                                                     read_func=self.dev.read_ctrl_run)
#         
#         S.get_lq('Run PID').connect_to_hardware(
#                                                     write_func=self.dev.set_pid_ctrl_run,
#                                                     read_func=self.dev.read_pid_ctrl_run)


        self.set_control_method(self.settings['control_method'])
        #self.settings['PID_SV'] = 0
               
#         if self.dev.read_ctrl_method()[1] == 'PID':
#             '''Force update of LQs since direct update does not work.'''
#             p, i, d = self.active_profile
#             self.dev.set_prop_band(p)
#             self.dev.set_integral_time(i)
#             self.dev.set_derivative_time(d)
        self.read_from_hardware()
            

    def set_control_method(self, control):
        """
        Sets currently active control mode.
        
        =============  ==========  ==========================
        **Arguments**  **Type**    **Description**        
        control        str         Temperature Control Method
                                    (see table below)
        =============  ==========  ========================== 
        
        ====================  ===================
        **Control Method**    **String Entry**
        PID                   "PID"
        ON/OFF                "ON/OFF"
        Manual tuning         "Manual"
        PID program control   "PID_Program"
        ====================  ===================
        
        """
        select = self.CTRL_METHODS.index(control)
        self.dev.set_ctrl_method(select)
        
    def set_heat_cool_control(self, control):
        """
        ================  ==========  ================================
        **Arguments**     **Type**    **Description**                 
        control           str         Heating control mode. Other 
                                      modes are currently disabled.
        ================  ==========  ================================        
        
        ==================  ==================
        **Control Method**  **String Entry**
        Heating             "Heating"
        ==================  ==================  
        """
        select = self.HEAT_COOL_CTRLS.index(control)
        self.dev.set_heat_cool_ctrl(select)
        

        
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
        