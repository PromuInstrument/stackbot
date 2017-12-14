'''
Created on Nov 16, 2017

@author: Edward Barnard
'''

from ScopeFoundry.measurement import Measurement
import time
from qtpy import QtWidgets


class CLMirrorMotionMeasure(Measurement):

    def move_and_wait(self, hw_name, axis_name, new_pos, target_range=50e-3, timeout=10):
        print("move_and_wait", hw_name, axis_name, new_pos)
        
        hw = self.app.hardware[hw_name]
        hw.settings[axis_name + "_target_position"] = new_pos
        hw.settings[axis_name + "_enable_closedloop"] = True
        
        t0 = time.time()
        
        # Wait until stage has moved to target
        while True:
            if self.interrupt_measurement_called:
                raise ValueError('interrupt move_and_wait')
            pos = hw.settings.get_lq(axis_name + "_position").read_from_hardware()
            distance_from_target = abs(pos - new_pos)
            if distance_from_target < target_range:
                #print("settle time {}".format(time.time() - t0))
                break
            if (time.time() - t0) > timeout:
                hw.settings[axis_name + "_enable_closedloop"] = False
                raise IOError("AttoCube ECC100 took too long to reach position")
            time.sleep(0.005)
            
    def pre_run(self):
        
        self.stage_safe = False
        
        ### SEM Stage must be down, ask user
        reply = QtWidgets.QMessageBox.question(None,"SEM Stage Down?", 
                                               """{}<p>
                                               <b>WARNING</b> SEM stage must be down before proceeding!
                                               <p>
                                               Is SEM Stage Down?
                                               """.format(self.name),
                                               QtWidgets.QMessageBox.Yes, 
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.stage_safe = True
        else:
            self.stage_safe = False

#     def move_until_stopped(self, hw_name, axis_name, new_pos, target_range=50e-3):
#         # NOT YET IMPLEMENTED
#         print("move_until_stopped", hw_name, axis_name, new_pos)
#         
#         hw = self.app.hardware[hw_name]
#         pos = hw.settings.get_lq(axis_name + "_position").read_from_hardware()
#         hw.settings[axis_name + "_target_position"] = new_pos
#         
#         t0 = time.time()
#         
#         # Wait until stage has moved to target
#         while True:
#             pos = hw.settings.get_lq(axis_name + "_position").read_from_hardware()
#             distance_from_target = abs(pos - new_pos)
#             if distance_from_target < target_range:
#                 #print("settle time {}".format(time.time() - t0))
#                 break
#             if (time.time() - t0) > timeout:
#                 raise IOError("AttoCube ECC100 took too long to reach position")
#             time.sleep(0.005)


class CLMirrorHomeAxesMeasure(CLMirrorMotionMeasure):
    
    name = 'cl_mirror_home_axes'
    
    def pre_run(self):
        
        self.stage_safe = False
        
        ### SEM Stage must be down, ask user
        reply = QtWidgets.QMessageBox.question(None,"SEM Stage Down?", 
                                               """{}<p>
                                               <b>WARNING</b> SEM stage must be down below 30mm before proceeding!
                                               <p>
                                               Is SEM Stage Down <b>below 30mm</b>?
                                               """.format(self.name),
                                               QtWidgets.QMessageBox.Yes, 
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.stage_safe = True
        else:
            self.stage_safe = False

    
    def run(self):
        
        ## Verify SEM stage down
        if not self.stage_safe:
            return
        
        
        # Drive Z  + to EOT
        print("Drive Z to + EOT")
        
        hw = self.app.hardware['attocube_cl_xyz']
        
        hw.settings['z_enable_closedloop'] = False
        hw.settings["z_eot_stop"] = True

        hw.settings['z_continuous_motion'] = +1
        
        while not hw.settings['z_eot_forward']:
            hw.read_from_hardware()
            if self.interrupt_measurement_called:
                hw.settings['z_continuous_motion'] = 0        
                return
        
        hw.settings['z_continuous_motion'] = 0
        print("Stop Z motion")
        
        
        # Home Y ( - safe)        
        success = self.home_and_wait('attocube_cl_xyz', 'y', -1)
        if not success:
            print("Failed to Home Y")
            return
        
        # Home X ( + or - safe)
        success = self.home_and_wait('attocube_cl_xyz', 'x', +1)
        if not success:
            print("Failed to Home X")
            return

        # Home Pitch ( + or - safe)
        success = self.home_and_wait('attocube_cl_angle', 'pitch', +1)
        if not success:
            print("Failed to Home Pitch")
            return

        # Home Yaw ( + or - safe)
        success = self.home_and_wait('attocube_cl_angle', 'yaw', +1)
        if not success:
            print("Failed to Home Yaw")
            return
        
        ## Move XY to Park position (-4.5, -10.4)
        self.move_and_wait('attocube_cl_xyz', 'x', self.app.hardware['cl_mirror'].settings['park_x'], timeout=10)
        self.move_and_wait('attocube_cl_xyz', 'y', self.app.hardware['cl_mirror'].settings['park_y'], timeout=20)

        # Home Z (+ safe)
        success = self.home_and_wait('attocube_cl_xyz', 'z', +1)
        if not success:
            print("Failed to Home Z")
            return
        
        # Move Z to Park position
        self.move_and_wait('attocube_cl_xyz', 'z', self.app.hardware['cl_mirror'].settings['park_z'], timeout=20)
        
        # Success!
        print('Successfully Home all 5 attocube axes')
        
    def home_and_wait(self, hw_name, axis_name, safe_travel_dir):
        print("home_and_wait", hw_name, axis_name, safe_travel_dir)
        home_meas = self.app.measurements['attocube_home_axis']
        home_meas.settings['hw_name'] = hw_name
        home_meas.settings['axis_name'] = axis_name
        home_meas.settings['safe_travel_dir'] = safe_travel_dir
        
        ## run home_meas, wait for completion
        home_meas.start()
        time.sleep(0.010)
        
        while home_meas.is_measuring():
            if self.interrupt_measurement_called:
                home_meas.interrupt()
                return False
            
        time.sleep(0.1)
            
        #check to verify homing
        return self.app.hardware[hw_name].settings[axis_name + "_reference_found"]


        

class CLMirrorParkMeasure(CLMirrorMotionMeasure):
    
    name = 'cl_mirror_park'
    
    def run(self):
        cl_mirror_hw = self.app.hardware['cl_mirror']
        
        if not self.stage_safe:
            self.log.error("Can't park, stage not safe")
            return
                
        ### Must be homed
        for ax_name, hw_name in cl_mirror_hw.axes_hw.items():
            if not self.app.hardware[hw_name].settings[ax_name + "_reference_found"]:
                self.log.error("Failed to Park, need to home axis {} {}".format(hw_name, ax_name))
                return

        # record 5 axes positions        
        
        # Move to park XY
        self.move_and_wait('attocube_cl_xyz', 'x',
                           cl_mirror_hw.settings['park_x'],
                           timeout=100)
        self.move_and_wait('attocube_cl_xyz', 'y',
                           cl_mirror_hw.settings['park_y'],
                           timeout=100)
        
        # Move Z to -4
        # TODO
        
        # Pitch and Yaw to zero
        self.move_and_wait('attocube_cl_angle', 'pitch', 
                           cl_mirror_hw.settings['park_pitch'],
                           timeout=100)
        self.move_and_wait('attocube_cl_angle', 'yaw',
                           cl_mirror_hw.settings['park_yaw'],
                           timeout=100)
        
        # Z to park z 
        self.move_and_wait('attocube_cl_xyz', 'z',
                           cl_mirror_hw.settings['park_z'],
                           timeout=100)


class CLMirrorInsertMeasure(CLMirrorMotionMeasure):

    name = 'cl_mirror_insert'

    def pre_run(self):
        
        self.stage_safe = False
        
        ### SEM Stage must be down, ask user
        reply = QtWidgets.QMessageBox.question(None,"Sample Safe?", 
                                               """{}<p>
                                               <b>WARNING</b> Are you sure sample does not obstruct mirror movement?
                                               For Safety move sample 500um down (or more)
                                               <p>
                                               Safe to move mirror?
                                               """.format(self.name),
                                               QtWidgets.QMessageBox.Yes, 
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.stage_safe = True
        else:
            self.stage_safe = False


    def run(self):

        cl_mirror_hw = self.app.hardware['cl_mirror']
        
        if not self.stage_safe:
            return
        
        ### Must be homed
        for ax_name, hw_name in cl_mirror_hw.axes_hw.items():
            if not self.app.hardware[hw_name].settings[ax_name + "_reference_found"]:
                print("Failed to insert, need to home axis", hw_name, ax_name)
                return
        
        # Pitch and Yaw to position
        self.move_and_wait('attocube_cl_angle', 'pitch', 
                           cl_mirror_hw.settings['ref_pitch'],
                           timeout=5)
        self.move_and_wait('attocube_cl_angle', 'yaw',
                           cl_mirror_hw.settings['ref_yaw'],
                           timeout=5)
        
        # Move Z into place
        self.move_and_wait('attocube_cl_xyz', 'z',
                           cl_mirror_hw.settings['ref_z'],
                           timeout=100)

        # Move XY into place
        self.move_and_wait('attocube_cl_xyz', 'y',
                           cl_mirror_hw.settings['ref_y'],
                           timeout=100)
        self.move_and_wait('attocube_cl_xyz', 'x',
                           cl_mirror_hw.settings['ref_x'],
                           timeout=100)

        



