'''
Created on Jul 24, 2014

@author: Edward Barnard
'''
from __future__ import absolute_import
from ScopeFoundry import HardwareComponent
try:
    from .attocube_ecc100 import AttoCubeECC100
except Exception as err:
    print("could not load modules needed for AttoCubeECC100: {}".format(err))
    

class AttoCubeXYZStageHW(HardwareComponent):

    name = 'attocube_xyz_stage'

    def __init__(self, app, debug=False, name=None, ax_names='xyz'):
        self.ax_names = ax_names
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        

    def setup(self):
        # if attocube pro is activated
        self.pro = False
        
        # Created logged quantities
        
        for axis in self.ax_names:          
            self.settings.New(axis + "_position", 
                               dtype=float,
                               ro=True,
                               vmin=-10e3,
                               vmax=10e3,
                               unit='um',
                               si=False
                               )
            
            #self.settings.New(axis + "_ref_position", dtype=float, ro=True, unit='nm')
            
            self.settings.New(axis + "_target_position",
                                dtype=float,
                                ro=False,
                                vmin=-10e3,
                                vmax=10e3,
                                unit='um',
                                si=False)
        
            self.settings.New(axis + "_step_voltage",
                                dtype=float, unit='V',
                                ro=True)
            
            self.settings.New(axis + "_enable_output", dtype=bool, initial=True)
        
            if self.pro:
                self.settings.New(axis + "_openloop_voltage",
                                        dtype=float, si=True, ro=False)
            
            
                self.settings.New(axis + "_frequency",
                                        dtype=float, si=True, ro=False)
        
            self.settings.New(axis + "_electrically_connected", dtype=bool,
                                                               ro=True)
        
            self.settings.New(axis + "_enable_closedloop", dtype=bool,
                                                                 ro=False)
            
            # Target Status is NCB_FeatureNotAvailable
            #self.settings.New(axis + "_target_status", dtype=bool, ro=True)
                
        
        self.settings.New('device_num', dtype=int, initial=0)
        self.settings.New('axis_map', dtype=str, initial='xyz')
        # need enable boolean lq's
        
        # connect GUI
        # no custom gui yet
        
    def connect(self):
        if self.settings['debug_mode']: print("connecting to attocube_xy_stage")
                
        self.settings.device_num.change_readonly(True)
        self.settings.axis_map.change_readonly(True)
        
        # Open connection to hardware
        self.ecc100 = AttoCubeECC100(device_num=self.settings['device_num'], debug=self.settings['debug_mode'])
        
        for axis_num, axis_name in enumerate(self.settings['axis_map']):
            print(axis_num, axis_name)
            if axis_name in 'xyz':

                # Enable Axes
                self.ecc100.enable_axis(axis_num, enable=True)

                # connect logged quantities
                
                self.settings.get_lq(axis_name + "_position").hardware_read_func = \
                    lambda a=axis_num: 1e-3*self.ecc100.read_position_axis(a)
        
                self.settings.get_lq(axis_name + "_target_position").hardware_read_func = \
                    lambda a=axis_num: 1e-3*self.ecc100.read_target_position_axis(a)
                self.settings.get_lq(axis_name + "_target_position").hardware_set_func  = \
                    lambda new_pos, a=axis_num: self.ecc100.write_target_position_axis(a, 1e3*new_pos)
                    
                
                self.settings.get_lq(axis_name + "_step_voltage").hardware_read_func = \
                    lambda a=axis_num: 1e-3*self.ecc100.read_step_voltage(a)
                    
                self.settings.get_lq(axis_name + "_electrically_connected").hardware_read_func = \
                    lambda a=axis_num: self.ecc100.is_electrically_connected(a)
                
                self.settings.get_lq(axis_name + "_enable_output").hardware_read_func = \
                    lambda a=axis_num: self.ecc100.read_enable_axis(a)
                self.settings.get_lq(axis_name + "_enable_output").hardware_set_func = \
                    lambda enable, a=axis_num: self.ecc100.enable_axis(a, enable)
                    
                self.settings.get_lq(axis_name + "_enable_closedloop").connect_to_hardware(
                    read_func = lambda a=axis_num: self.ecc100.read_enable_closedloop_axis(a),
                    write_func = lambda enable, a=axis_num: self.ecc100.enable_closedloop_axis(a, enable)
                    )
                    
                # Target Status is NCB_FeatureNotAvailable
                #self.settings.get_lq(axis_name + "_target_status").connect_to_hardware(
                #    read_func = lambda a=axis_num: self.ecc100.read_target_status(a) 
                #    )




                if self.pro:
                    self.x_openloop_voltage.hardware_read_func = lambda: self.ecc100.read_openloop_voltage(X_AXIS)
                    self.x_openloop_voltage.hardware_set_func = lambda x: self.ecc100.write_openloop_voltage(X_AXIS, x)
                                    
                    self.settings.get_lq(axis_name + "_frequency").hardware_read_func = \
                        lambda a=axis_num: self.ecc100.read_frequency(a)
                    self.settings.get_lq(axis_name + "_frequency").hardware_set_func = \
                        lambda x, a=axis_num: self.ecc100.write_frequency(a, x)
        
    
        self.read_from_hardware()
        
    def disconnect(self):
        
        #disconnect logged quantities from device
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        if hasattr(self, 'ecc100'):
            #disconnect device
            self.ecc100.close()
            
            # clean up device object
            del self.ecc100
        
        