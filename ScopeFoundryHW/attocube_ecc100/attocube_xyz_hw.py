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
        self.pro = True        
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        # Created logged quantities
        
        for axis in self.ax_names:          
            self.settings.New(axis + "_position", 
                               dtype=float,
                               ro=True,
                               unit='mm',
                               si=False
                               )
            
            #self.settings.New(axis + "_ref_position", dtype=float, ro=True, unit='nm')
            
            self.settings.New(axis + "_target_position",
                                dtype=float,
                                ro=False,
                                vmin=-20,
                                vmax=20,
                                unit='mm',
                                si=False)
        
            self.settings.New(axis + "_enable_closedloop", dtype=bool,
                                                                 ro=False)
            self.settings.New(axis + "_enable_output", dtype=bool, initial=True)
            self.settings.New(axis + "_electrically_connected", dtype=bool,
                                                               ro=True)
            self.settings.New(axis + "_reference_found", dtype=bool,
                                                               ro=True)
           
            if self.pro:
                self.settings.New(axis + "_auto_reference_update", dtype=bool,
                                                               ro=False)
                self.settings.New(axis + "_auto_reference_reset", dtype=bool,
                                                               ro=False)
                self.settings.New(axis + "_eot_stop", dtype=bool,
                                                               ro=False)
                self.settings.New(axis + "_eot_forward", dtype=bool,
                                                               ro=True)
                self.settings.New(axis + "_eot_back", dtype=bool,
                                                               ro=True)
       
            self.settings.New(axis + "_step_voltage",
                                dtype=float, vmin=0, vmax = 45, unit='V',
                                ro=False)
            if self.pro:
                self.settings.New(axis + "_openloop_voltage", unit = 'V',
                                        dtype=float, si=False, ro=False)
            
            
                self.settings.New(axis + "_frequency", unit = 'Hz',
                                        dtype=float, vmin = 1, vmax = 2000, si=False, ro=False)
                
            self.settings.New(axis + "_actor_type", dtype=str, ro=True)
            self.settings.New(axis + "_actor_name", dtype=str, ro=True)
        
        
            
            # Target Status is NCB_FeatureNotAvailable
            #self.settings.New(axis + "_target_status", dtype=bool, ro=True)
                
        
        self.settings.New('device_num', dtype=int, initial=0)
        self.settings.New('device_id', dtype=int, initial=0)
        self.settings.New('connect_by', dtype=str, initial='device_num', choices=('device_num', 'device_id'))
        #self.settings.New('axis_map', dtype=str, initial='xyz')
        # need enable boolean lq's
        
        # connect GUI
        # no custom gui yet
        
    def connect(self):
        if self.settings['debug_mode']: print("connecting to attocube_xy_stage")
                
        self.settings.device_num.change_readonly(True)
        self.settings.device_id.change_readonly(True)
        #self.settings.axis_map.change_readonly(True)
        
        
        # Open connection to hardware
        if self.settings['connect_by'] == 'device_num':
            self.ecc100 = AttoCubeECC100(device_num=self.settings['device_num'], debug=self.settings['debug_mode'])
            self.settings['device_id'] = self.ecc100.device_id
        if self.settings['connect_by'] == 'device_id':
            self.ecc100 = AttoCubeECC100(device_id=self.settings['device_id'], debug=self.settings['debug_mode'])
            self.settings['device_num'] = self.ecc100.device_num
        
        for axis_num, axis_name in enumerate(self.ax_names):
            print(axis_num, axis_name)
            if axis_name != "_":
                # Enable Axes
                self.ecc100.enable_axis(axis_num, enable=True)

                # connect logged quantities
                
                self.settings.get_lq(axis_name + "_position").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_position_axis(a))
        
                self.settings.get_lq(axis_name + "_target_position").connect_to_hardware(
                    read_func = lambda a=axis_num: self.ecc100.read_target_position_axis(a),
                    write_func = lambda new_pos, a=axis_num: self.ecc100.write_target_position_axis(a, new_pos))
                
                self.settings.get_lq(axis_name + "_step_voltage").connect_to_hardware(
                    read_func = lambda a=axis_num: self.ecc100.read_step_voltage(a),
                    write_func = lambda volts, a=axis_num: self.ecc100.write_step_voltage(a,volts))
                    
                self.settings.get_lq(axis_name + "_electrically_connected").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.is_electrically_connected(a))
                
                self.settings.get_lq(axis_name + "_reference_found").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_reference_status(a))
                
                self.settings.get_lq(axis_name + "_enable_output").connect_to_hardware(
                    read_func  = lambda a=axis_num: self.ecc100.read_enable_axis(a),
                    write_func = lambda enable, a=axis_num: self.ecc100.enable_axis(a, enable))
                    
                self.settings.get_lq(axis_name + "_enable_closedloop").connect_to_hardware(
                    read_func = lambda a=axis_num: self.ecc100.read_enable_closedloop_axis(a),
                    write_func = lambda enable, a=axis_num: self.ecc100.enable_closedloop_axis(a, enable)
                    )
                    
                # Target Status is NCB_FeatureNotAvailable
                #self.settings.get_lq(axis_name + "_target_status").connect_to_hardware(
                #    read_func = lambda a=axis_num: self.ecc100.read_target_status(a) 
                #    )

                if self.pro:
#                     self.x_openloop_voltage.hardware_read_func = lambda: self.ecc100.read_openloop_voltage(X_AXIS)
#                     self.x_openloop_voltage.hardware_set_func = lambda x: self.ecc100.write_openloop_voltage(X_AXIS, x)
                                    
                    self.settings.get_lq(axis_name + "_eot_stop").connect_to_hardware(
                        read_func = lambda a=axis_num: self.ecc100.read_enable_eot_stop(a),
                        write_func = lambda enable, a=axis_num: self.ecc100.enable_eot_stop(a,enable))
                    self.settings.get_lq(axis_name + "_eot_forward").connect_to_hardware(
                        lambda a=axis_num: self.ecc100.read_eot_forward_status(a))
                    self.settings.get_lq(axis_name + "_eot_back").connect_to_hardware(
                        lambda a=axis_num: self.ecc100.read_eot_back_status(a))
                    self.settings.get_lq(axis_name + "_frequency").connect_to_hardware(
                        read_func = lambda a=axis_num: self.ecc100.read_frequency(a),
                        write_func = lambda freq, a=axis_num: self.ecc100.write_frequency(a,freq))
                    self.settings.get_lq(axis_name + "_auto_reference_update").connect_to_hardware(
                        read_func = lambda a=axis_num: self.ecc100.read_enable_auto_update_reference(a),
                        write_func = lambda enable, a=axis_num: self.ecc100.enable_auto_update_reference(a,enable))
                    self.settings.get_lq(axis_name + "_auto_reference_reset").connect_to_hardware(
                        read_func = lambda a=axis_num: self.ecc100.read_enable_auto_reset_reference(a),
                        write_func = lambda enable, a=axis_num: self.ecc100.enable_auto_reset_reference(a,enable))
                        
                self.settings.get_lq(axis_name + "_actor_type").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_actor_type(a))
                self.settings.get_lq(axis_name + "_actor_name").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_actor_name(a))

    
        self.read_from_hardware()
        
        
        # update units based on Actor type
        for axis_num, axis_name in enumerate(self.ax_names):
            if axis_name != "_":
                actor_type = self.settings[axis_name + "_actor_type"]
                if actor_type == 'ECC_actorLinear':
                    self.settings.get_lq(axis_name + "_position").change_unit("mm")
                    self.settings.get_lq(axis_name + "_target_position").change_unit("mm")
                elif actor_type in ['ECC_actorGonio', 'ECC_actorRot']:
                    self.settings.get_lq(axis_name + "_position").change_unit("deg")
                    self.settings.get_lq(axis_name + "_target_position").change_unit("deg")

    def disconnect(self):
        
        self.settings.device_num.change_readonly(False)
        self.settings.device_id.change_readonly(False)
        #self.settings.axis_map.change_readonly(False)
        
        
        #disconnect logged quantities from device
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        if hasattr(self, 'ecc100'):
            #disconnect device
            self.ecc100.close()
            
            # clean up device object
            del self.ecc100
        
        