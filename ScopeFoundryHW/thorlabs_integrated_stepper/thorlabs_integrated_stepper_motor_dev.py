import time
import logging
import ctypes
from threading import Lock
from numpy import real

logger = logging.getLogger(__name__)


_ERRORS = {
    ## FTDI and Communication errors
    
    # The following errors are generated from the FTDI communications module or supporting code. 
    0: ("FT_OK", "Success"),
    1: ("FT_InvalidHandle","The FTDI functions have not been initialized."),
    2: ("FT_DeviceNotFound", "The Device could not be found: This can be generated if the function TLI_BuildDeviceList() has not been called."),  
    3: ("FT_DeviceNotOpened","The Device must be opened before it can be accessed. See the appropriate Open function for your device."),  
    4: ("FT_IOError", "An I/O Error has occured in the FTDI chip."),
    5: ("FT_InsufficientResources" , "There are Insufficient resources to run this application."),
    6: ("FT_InvalidParameter" , "An invalid parameter has been supplied to the device."), 
    7: ("FT_DeviceNotPresent" , """The Device is no longer present. The device may have been disconnected since the last TLI_BuildDeviceList() call."""),  
    8: ("FT_IncorrectDevice" , "The device detected does not match that expected"),
    # The following errors are generated by the device libraries. 
    16: ("FT_NoDLLLoaded", "The library for this device could not be found"),  
#     17 (0x11) FT_NoFunctionsAvailable - No functions available for this device./term>  
#     18 (0x12) FT_FunctionNotAvailable - The function is not available for this device./term>  
#     19 (0x13) FT_BadFunctionPointer - Bad function pointer detected./term>  
     20: ("FT_GenericFunctionFail - The function failed to complete succesfully"), 
#     21 (0x15) FT_SpecificFunctionFail - The function failed to complete succesfully./term>  

    ## General DLL control errors
    
    #The following errors are general errors generated by all DLLs. 
    
    # 32 (0x20) TL_ALREADY_OPEN - Attempt to open a device that was already open.  
    # 33 (0x21) TL_NO_RESPONSE - The device has stopped responding.  
    # 34 (0x22) TL_NOT_IMPLEMENTED - This function has not been implemented.  
    # 35 (0x23) TL_FAULT_REPORTED - The device has reported a fault.  
    # 36 (0x24) TL_INVALID_OPERATION - The function could not be completed at this time.  
    # 36 (0x28) TL_DISCONNECTING - The function could not be completed because the device is disconnected.  
    # 41 (0x29) TL_FIRMWARE_BUG - The firmware has thrown an error  
    # 42 (0x2A) TL_INITIALIZATION_FAILURE - The device has failed to initialize  
    # 43 (0x2B) TL_INVALID_CHANNEL - An Invalid channel address was supplied  
    
    
    ## Motor specific errors
    # 
    # The following errors are motor specific errors generated by the Motor DLLs. 
    # 
    # 37 (0x25) TL_UNHOMED - The device cannot perform this function until it has been Homed.  
    # 38 (0x26) TL_INVALID_POSITION - The function cannot be performed as it would result in an illegal position.  
    # 39 (0x27) TL_INVALID_VELOCITY_PARAMETER - An invalid velocity parameter was supplied
    #  The velocity must be greater than zero.  
    # 44 (0x2C) TL_CANNOT_HOME_DEVICE - This device does not support Homing 
    #  Check the Limit switch parameters are correct.  
    # 45 (0x2D) TL_JOG_CONTINOUS_MODE - An invalid jog mode was supplied for the jog function.  
    # 46 (0x2E) TL_NO_MOTOR_INFO - There is no Motor Parameters available to convert Real World Units.  

    }

def _err(retval):
    if retval == 0:
        return retval
    else:
        err_name, description = _ERRORS.get(retval, ("UNKNOWN", "Unknown error code."))
        raise IOError("Thorlabs Kinesis Error [{}] {}: {} ".format(retval, err_name, description))
    
class ThorlabsIntegratedStepperMotorDev(object):
    
    " Use Thorlabs kinesis software to control Integrated Stepper motor "
    
    
    def __init__(self, dev_num=0, serial_num=None, debug=False):
        """
        serial_num if defined should be a string or integer
        """
        
        #self.poll_time = poll_time # polling period in seconds
        
        self.debug = debug
        if self.debug:
            logger.debug("ThorlabsIntegratedStepperDev.__init__")
            
        logger.setLevel('DEBUG')
        
        # Load DLL libraries, note DeviceManager.dll must be loaded first    
        D = self.devman_dll = ctypes.windll.LoadLibrary("C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DeviceManager.dll")
        self.isc_dll = ctypes.windll.LoadLibrary("C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.IntegratedStepperMotors.dll")

        
        err_msg = _err(D.TLI_BuildDeviceList())
        if self.debug:
            logger.debug("DeviceManager.dll TLI_BuildDeviceList response message: {}".format(err_msg))
        
        #print('size',D.TLI_GetDeviceListSize())
        
        serialNos = ctypes.create_string_buffer(100)
        err_msg = _err(D.TLI_GetDeviceListByTypeExt(serialNos, 100, 70))
        if self.debug:
            logger.debug("DeviceManager.dll TLI_GetDeviceListByTypeExt response message: {}".format(err_msg))
            
        # byte arrays for the serial numbers
        self._serial_numbers = [x for x in serialNos.value.split(b',') if x]

        if debug:
            logger.debug("serial_numbers available {} --> {}".format(serialNos.value, self._serial_numbers))
            logger.debug("serial_number requested {}".format(repr(serial_num)))

        
        # _id is byte string representing serial number, like b'37874816'
        if serial_num:
            self._id = str(serial_num).encode() # _id must be a bytes array
            if debug:
                logger.debug("using serial number {}".format(self._id))
        else:
            if debug:
                logger.debug("using device number {}".format(dev_num))
            self._id = self._serial_numbers[dev_num]

        self.lock = Lock()

        self.open_device()
    

    
    def open_device(self):
        S = self.isc_dll
        with self.lock:
            err_msg = _err(S.ISC_Open(self._id))
            if self.debug:
                logger.debug("{} ISC_Open response message: {}".format( self._id, err_msg))
                
            err_msg = _err(S.ISC_ClearMessageQueue(self._id))
            if self.debug:
                logger.debug("{} ISC_ClearMessageQueue response message: {}".format( self._id, err_msg))
            
            # polling required to update device status, otherwise must use request functions before reads
            '''
            err_msg = _err(S.ISC_StartPolling(self._id,200))
            if self.debug:
                logger.debug("{} ISC_StartPolling response message: {}".format( self._id, err_msg))
            '''
            err_msg = _err(S.ISC_ResetStageToDefaults(self._id))
            if self.debug:
                logger.debug("{} ISC_ResetStageToDefaults response message: {}".format( self._id, err_msg))

        time.sleep(0.1)    
    
    def close_device(self):
        with self.lock:
            '''
            err_msg = _err(self.isc_dll.ISC_StopPolling(self._id))
            if self.debug:
                logger.debug("{} ISC_StopPolling response message: {}".format( self._id, err_msg))
            '''
            err_msg = _err(self.isc_dll.ISC_Close(self._id))
            if self.debug:
                logger.debug("{} ISC_Close response message: {}".format( self._id, err_msg))
        
    def get_serial_num(self):
        return self._id.decode()

    def read_position(self):
        with self.lock:
            _err(self.isc_dll.ISC_RequestPosition(self._id))
            pos = self.isc_dll.ISC_GetPosition(self._id)
        return pos
            
    def write_move_to_position(self, pos):
        """
        Move the device to the specified position (angle). 
        Returns immediately (non-blocking)
        motor will move until position is reached, or stopped
        pos is an integer in device units ()
        """
        self.isc_dll.ISC_ClearMessageQueue(self._id);
        with self.lock: _err(self.isc_dll.ISC_MoveToPosition(self._id, int(pos)))
        
    def move_and_wait(self, pos, timeout=100):
        self.write_move_to_position(pos)
        t0 = time.time()
        while(self.read_position() != pos):
            time.sleep(0.1)
            if (time.time() - t0) > timeout:
                self.stop_profiled()
                raise( IOError("Failed to move"))

    def stop_profiled(self):
        with self.lock:
            _err(self.isc_dll.ISC_StopProfiled(self._id))
            
    def print_min_max(self):
        print('maximum writable position (device_units):',repr(self.isc_dll.ISC_GetStageAxisMaxPos(self._id)))
        print('minimum writable position (device_units):',self.isc_dll.ISC_GetStageAxisMinPos(self._id))
        
    def is_connected(self):
        with self.lock:
            resp = self.isc_dll.ISC_CheckConnection(self._id)
            print(self._id, 'is_connected=',resp)
            return resp
        
    def start_home(self):
        """
        Homing the device will set the device to a known state and determine the home position,
        Returns immediately (non-blocking)
        motor will home until position is reached, or stopped
        will be in position 0 when done
        """
        with self.lock:
            _err(self.isc_dll.ISC_Home(self._id))

    def home_and_wait(self, timeout=100):
        self.start_home()
        t0 = time.time()
        while(self.read_position() != 0):
            time.sleep(0.1)
            if (time.time() - t0) > timeout:
                self.stop_profiled()
                raise( IOError("Failed to home"))   
    
    def move_relative(self, delta):
        self.isc_dll.ISC_SetMoveRelativeDistance(self._id, delta)
        self.isc_dll.ISC_MoveRelativeDistance(self._id)

    def get_real_value(self, device_unit, unit_type=0):
        """
        FAILS
        """
        real_unit = ctypes.c_double()
        print(type(real_unit), ctypes.pointer(real_unit))
        print('error msg convertion unit',(self.isc_dll.ISC_GetRealValueFromDeviceUnit(self._id, int(device_unit), ctypes.byref(real_unit),
                                                                                       unit_type)))
        print('the real value is ',real_unit.value)
        return real_unit.value
        
        
if __name__=='__main__':
   
    A=ThorlabsIntegratedStepperMotorDev( dev_num=0, serial_num=55000231, debug=True)
    
    A.is_connected()
    A.print_min_max()
    
    print("The start position is ", A.read_position())

    #12288000/90. # steps / deg
    print("1. position is ", A.read_position(), sep='')
    A.move_and_wait(0,100  )# moves to 0 deg with a timeout of 100 sec
    print("2. position is ", A.read_position(), sep='')
    A.move_and_wait(12288000, 100) # moves to 90 deg with a timeout of 100 sec
    print("3. position is ", A.read_position(), sep='')
    A.close_device()
    
    
    