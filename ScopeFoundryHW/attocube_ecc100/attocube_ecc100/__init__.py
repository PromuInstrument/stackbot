from __future__ import division, print_function
import ctypes
from ctypes import (c_int, c_int32, c_int16, c_uint32, c_int64, 
                    c_byte, c_ubyte, c_short, c_double, cdll, pointer, 
                    byref)
import os
import time
import numpy as np

ecc = cdll.LoadLibrary(
        os.path.abspath(os.path.join(
                         os.path.dirname(__file__),
                         r"Win64\lib\ecc.dll")))


# /** Return values of functions */
#define NCB_Ok                   0              /**< No error                              */
#define NCB_Error              (-1)             /**< Unspecified error                     */
#define NCB_Timeout              1              /**< Communication timeout                 */
#define NCB_NotConnected         2              /**< No active connection to device        */
#define NCB_DriverError          3              /**< Error in comunication with driver     */
#define NCB_DeviceLocked         7              /**< Device is already in use by other     */
#define NCB_InvalidParam         9              /**< Parameter out of range                */
#define NCB_FeatureNotAvailable 10              /**< Feature only available in pro version */

NCB_ERROR_CODES = {
                   0: "NCB_Ok",
                   -1:"NCB_Error",
                   1: "NCB_Timeout",
                   2: "NCB_NotConnected",
                   3: "NCB_DriverError",
                   7: "NCB_DeviceLocked",
                   9: "NCB_InvalidParam",
                   10:"NCB_FeatureNotAvailable"
                   }

ECC_ACTOR_TYPES = [
     "ECC_actorLinear",                           
     "ECC_actorGonio",                            
     "ECC_actorRot"]

def handle_err(retcode):
    if retcode != 0:
        raise IOError(NCB_ERROR_CODES[retcode])
    return retcode



class EccInfo(ctypes.Structure):
    _fields_ = [
                ("id", c_int32),
                ("locked", c_int32),]
    _pack_ = 1 # Important for field alignment, might be wrong


class AttoCubeECC100(object):
    
    def __init__(self, device_num=0, debug=False):
        self.debug = debug
        self.device_num = device_num
        
        if self.debug:
            print("Initializing AttoCubeECC100", device_num)
        
        self.num_devices = ecc.ECC_Check()
        
        assert 0 <= self.device_num < self.num_devices
        
        # TODO check if device is locked

        self.devhandle = c_uint32(0)

        handle_err(ecc.ECC_Connect(0,byref(self.devhandle)))
        
        
    def close(self):
        handle_err(ecc.ECC_Close(self.devhandle))


    def read_actor_info(self, axis):
        actor_name = ctypes.create_string_buffer(20)
        handle_err(ecc.ECC_getActorName(
                            self.devhandle,
                            axis, # Int32 axis
                            byref(actor_name), # char * name
                            ))
        actor_type_id = c_int32()
        handle_err(ecc.ECC_getActorType(
                            self.devhandle,
                            axis, # Int32 axis
                            byref(actor_type_id) #ECC_actorType * type (enum)
                            ))
        return actor_name.value.strip(), ECC_ACTOR_TYPES[actor_type_id.value]



    def read_enable_axis(self, axis):
        cenable = c_int32()
        handle_err(ecc.ECC_controlOutput(self.devhandle,
                                 axis, #axis
                                 byref(cenable), #Bln32 * enable,
                                 0, # read
                                 ))
        return cenable.value
        
    def enable_axis(self, axis, enable=True):
        cenable = c_int32(int(enable))
        handle_err(ecc.ECC_controlOutput(self.devhandle,
                                 axis, #axis
                                 byref(cenable), #Bln32 * enable,
                                 1, # set
                                 ))
        
    def read_enable_closedloop_axis(self, axis):
        cenable = c_int32()
        handle_err(ecc.ECC_controlMove(self.devhandle,
                                 axis, #axis
                                 byref(cenable), #Bln32 * enable,
                                 0, # read
                                 ))
        return cenable.value
        
    def enable_closedloop_axis(self, axis, enable=True):
        cenable = c_int32(int(enable))
        handle_err(ecc.ECC_controlMove(self.devhandle,
                                 axis, #axis
                                 byref(cenable), #Bln32 * enable,
                                 1, # set
                                 ))


    def single_step(self, axis, backward=False):
        handle_err(ecc.ECC_setSingleStep(self.devhandle, # device handle
                                 axis,  # axis
                                 int(backward))) #backward (direction control)

    def single_step_forward(self, axis):
        self.single_step(axis, False)
    def single_step_backward(self, axis):
        self.single_step(axis, True)


    def read_position_axis(self, axis):
        pos = c_int32()
        handle_err(ecc.ECC_getPosition( 
                                self.devhandle, #Int32 deviceHandle,
                                axis, #Int32 axis,
                                byref(pos))) #Int32* position );
        return pos.value


    def is_electrically_connected(self, axis):
        """Connected status.

        Retrieves the connected status. Indicates whether an actor is eletrically connected to the controller.
        """
        connected = c_int32()
        handle_err(ecc.ECC_getStatusConnected(
                                self.devhandle,
                                axis,
                                byref(connected)))
        return bool(connected.value)

    def read_reference_position(self, axis):
        refpos = c_int32()
        handle_err(ecc.ECC_getReferencePosition(
                                self.devhandle,
                                axis, #Int32 axis
                                byref(refpos), #Int32* reference
                                ))
        return refpos.value

    def read_reference_status(self, axis):
        """
        Reference status.

        Retrieves the status of the reference position. It may be valid or invalid.
        """
        valid = c_int32()
        handle_err(ecc.ECC_getStatusReference(
                                  self.devhandle,
                                  axis,
                                  byref(valid)))
        return bool(valid.value)
    
    def read_target_range_axis(self, axis):
        raise NotImplementedError()
    
    def write_target_position_axis(self, axis, target_pos):
        tpos = c_int32(int(target_pos))
        handle_err(ecc.ECC_controlTargetPosition(
                            self.devhandle,
                            axis, #Int32 axis
                            byref(tpos), # Int32* target
                            1, #Bln32 set
                            ))
                   
    def read_target_position_axis(self, axis):
        tpos = c_int32()
        handle_err(ecc.ECC_controlTargetPosition(
                            self.devhandle,
                            axis, #Int32 axis
                            byref(tpos), # Int32* target
                            0, #Bln32 set
                            ))
        if self.debug: print('ecc100 read_target_position_axis', axis, tpos.value)

        return tpos.value
    
    def read_target_status(self, axis):
        """
        Target status. 

        Retrieves the target status. Indicates whether the actual 
        position is within the target range.
        """
        target_status = c_uint32()
        handle_err(ecc.ECC_getStatusTargetRange(
                            self.devhandle,
                            axis, #Int32 axis
                            byref(target_status), # Bln32* target                            
                            ))
        return bool(target_status.value)

    def read_frequency(self, axis):
        """returns Frequency in mHz"""
        freq = c_int32()
        handle_err(ecc.ECC_controlFrequency(
                            self.devhandle,
                            axis, #Int32 axis
                            byref(freq), #Int32* frequency
                            0, # Bln32 set
                            ))
        return freq.value
    
    def write_frequency(self,axis, freq):
        """freq: Frequency in mHz"""
        freq = c_int32(freq)
        handle_err(ecc.ECC_controlFrequency(
                            self.devhandle,
                            axis, #Int32 axis
                            byref(freq), #Int32* frequency
                            1, # Bln32 set
                            ))
        
    def read_openloop_voltage(self, axis):
        """ Read open loop analog voltage adjustment
        
        returns voltage in uV
        
        requires Pro version
        """
        ol_volt = c_int32()
        handle_err(ecc.ECC_controlFixOutputVoltage(
                            self.devhandle,
                            axis,
                            byref(ol_volt),# Int32 * voltage
                            0, #set
                            ))
        return ol_volt.value
    
    def write_openloop_voltage(self, axis, voltage):
        """ Write open loop analog voltage adjustment
            voltage in uV
        """
        ol_volt = c_int32(voltage)
        handle_err(ecc.ECC_controlFixOutputVoltage(
                            self.devhandle,
                            axis,
                            byref(ol_volt),# Int32 * voltage
                            1, #set
                            ))

    def enable_ext_trigger(self, axis):
        raise NotImplementedError()

    def enable_continous_motion(self, axis, direction, enable=True ):
        raise NotImplementedError()
    
    def stop_continous_motion(self, axis):
        raise NotImplementedError()
    
    def enable_auto_reset_reference(self, axis):
        raise NotImplementedError()
    
    def read_step_voltage(self, axis):
        """
        Control amplitude.

        Read the amplitude of the actuator signal.

        """
        ampl = c_int32()
        handle_err(ecc.ECC_controlAmplitude(
                            self.devhandle,
                            axis, # Int32 axis
                            byref(ampl), #Int32* amplitude
                            0, #set
                            ))
        return ampl.value
        
    
    def reset_axis(self,axis):
        """
        Reset position.

        Resets the actual position to zero and marks the reference position as invalid.
        
        """
        handle_err(ecc.ECC_setReset(self.devhandle, axis))
    
    
#ecc_infos = np.ones(10, dtype=c_uint32)
#num_devices = ecc.ECC_Check(ecc_infos.ctypes)

#print repr(num_devices)
#print ecc_infos



if __name__ == '__main__':
    
    e = AttoCubeECC100(device_num=0, debug=True)

    for ax in [0,1,2]:
        print(ax, e.read_actor_info(ax))
        print(ax, "electrical", e.is_electrically_connected(ax))
        print(ax, "reference_status", e.read_reference_status(ax))
        print(ax, "reference_pos", e.read_reference_position(ax))
        print(ax, "step_voltage", e.read_step_voltage(ax))
        ##print ax, "dc_voltage", e.read_openloop_voltage(ax)
        #needs pro version
        print(ax, "frequency", e.read_frequency(ax))
        print(ax, "enable_axis", e.enable_axis(ax))
        print(ax, "position", e.read_position_axis(ax))
        for i in range(10):
            e.single_step(ax, backward=False)
            print(ax, "position", e.read_position_axis(ax))
            time.sleep(0.05)

        print(ax, "enable_closedloop_axis", e.enable_closedloop_axis(ax, enable=True))
        print(ax, "moving", e.write_target_position_axis(ax, 3e6))
        for i in range(10):
            print(ax, "position", e.read_position_axis(ax))
            time.sleep(0.05)
        
    e.close()
    
    print("done")
