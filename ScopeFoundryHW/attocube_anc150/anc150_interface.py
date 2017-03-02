'''
Created on Feb 23, 2017

@author: Alan Buckley
Helpful feedback from Ed Barnard and Frank Ogletree
'''
from __future__ import division, absolute_import, print_function
import serial
import logging

logger = logging.getLogger(__name__)

class ANC_Interface(object):
    
    name="anc_interface"
    timeout = 0.1
    
    def __init__(self, port="COM6", debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("ANC_Interface.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, baudrate=38400, bytesize=8, parity='N', stopbits=1, timeout = self.timeout)
        
        self.ser.timeout = 0.1
        self.ser.writeTimeout = 0.1
        
        self.ser.flush()
        
    def ask_cmd(self, cmd):
        """
        Issues a command to the Attocube device.
        :returns: a value extracted from the Attocube device.
        """
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd+b'\r\n'
        self.ser.write(message)
        resp = self.ser.readlines()
        
        if len(resp) < 2:
            raise IOError( "No response from ANC 150, power off? {}".format(resp))
        
        if resp[-2] != b"OK\r\n":
            # example error string list [b'getc 1\r\n', b'Axis in wrong mode\r\n', b'ERROR\r\n', b'> ']
            err_msg = "ANC Error {} --> {}".format(cmd, resp)
            logger.error(err_msg)
            raise IOError(err_msg)
        # example success string list [b'getf 1\r\n', b'frequency = 2 Hz\r\n', b'OK\r\n', b'> '   ]
        if self.debug:
            print("ANC ask command resp:", resp)
        resp = resp[1:-2]   #trim command echo and OK/prompt
        return resp         

    def extract_value(self, resp):
        """
        Strips entry prior to terminating characters,
        Seeks out "=" sign and picks the value thereafter.        
        """
        entry = resp[0].strip().decode().split()
        for i in enumerate(entry):
            if i[1] == "=":
                sub_index = i[0]
                equals = i[1]
        value_index = sub_index+1
        value = entry[value_index]
        return(value)
    
    def get_version(self):
        """
        :returns: Prints the version number and the manufacturer.
        """
        message = b'ver'
        resp = self.ask_cmd(message)
        return resp
    
    def set_axis_mode(self, axis_id, axis_mode):
        """
        Set axis <AID> to mode <AMODE>. Be sure to switch to the right mode
        whenever you are measuring capacitance or attempting to move the
        positioner. For sensitive, low noise measurements switch to "gnd".
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        axis_mode     ext, stp, gnd, cap   Axis mode of the selected axis.
        ============  ===================  ========================================
        """
        message = "setm {} {}".format(axis_id, axis_mode).encode()
        resp = self.ask_cmd(message)
        if self.debug:
            logger.debug(resp)
        
    
    def get_axis_mode(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================
        
        :returns: The mode the corresponding axis is in.
        """
        message = "getm {}".format(axis_id).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def stop(self, axis_id):
        """
        Stop any motion on the given axis.
        
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================
        
        """
        message = "stop {}".format(axis_id).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def step(self, axis_id, dir, c):
        """
        Move <C> steps or continuously upwards (outwards) or downwards (inwards). An error occurs when
        the axis is not in "stp" mode.
        
        ============  ===================  ============================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        dir           'u' or 'd'           Up or down direction flag
        c             'c' or (1,N)         'c' for continuous run or N number of steps.
        ============  ===================  ============================================
        
        """
        message = "step{} {} {}".format(dir, axis_id, c).encode()
        resp = self.ask_cmd(message)
        return resp
        
    def set_frequency(self, axis_id, frequency):
        """
        Set the frequency on axis <AID> to <FRQ>.
        
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        frequency     (1,8000)             An integer frequency up to 8000 Hz.
        ============  ===================  ========================================

        """
        message = "setf {} {}".format(axis_id, frequency).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def set_voltage(self, axis_id, voltage):
        """
        Set the voltage on axis <AID> to <VOL>.
        
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        voltage       (1,70)               An integer voltage up to 70 V.
        ============  ===================  ========================================

        """
        message = "setv {} {}".format(axis_id, voltage).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def get_frequency(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================

        :returns: The frequency for axis <AID>.
        """
        message = "getf {}".format(axis_id).encode()
        resp = self.ask_cmd(message)
        return int(resp)
    
    def get_voltage(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================

        :returns: The voltage for axis <AID>.
        """
        message = "getv {}".format(axis_id).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def get_capacity(self, axis_id):
        """
        ============  ===================  ========================================
        **Argument**  **Range of values**  **Description**
        axis_id       1,2,3                One of the 3 axes offered on the ANC150.
        ============  ===================  ========================================

        **Note:** You have to be in "cap" mode, otherwise an error message is given.

        :returns: The measured capacity for axis <AID>.
        """
        message = "getc {}".format(axis_id).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def set_pattern(self, axis_id, dir, pattern_number):
        """
        Set pattern number <PNUM> for upward movement or downward movement on axis <AID>.
        
        ==============  ===================  ===============================================
        **Argument**    **Range of values**  **Description**
        axis_id         1,2,3                One of the 3 axes offered on the ANC150.
        dir             'u' or 'd'           Up or down direction flag.
        pattern_number  (0,19)               Pattern number for upward or downward movement.
        ==============  ===================  ===============================================

        """
        message = "setp{} {} {}".format(dir, axis_id, pattern_number).encode()
        resp = self.ask_cmd(message)
        return resp
        

    
    def get_pattern(self, axis_id, dir):
        """
        ==============  ===================  ========================================
        **Argument**    **Range of values**  **Description**
        axis_id         1,2,3                One of the 3 axes offered on the ANC150.
        dir             'u' or 'd'           Up or down direction flag.
        ==============  ===================  ========================================
        
        :returns: Pattern number <PNUM> for upward or downward movement on axis <AID>.
        
        """
        message = "getp{} {}".format(dir, axis_id).encode()
        resp = self.ask_cmd(message)
        return resp

    
    def set_pattern_value(self, pattern_index, pattern_val):
        """
        Set value no. <PIDX> to value <PVAL> in the user curve.
        
        =============  ===================  ======================================================
        **Argument**   **Range of values**  **Description**
        pattern_index  (0,255)              Pattern index of choice (x-axis)
        pattern_value  (0,255)              Pattern value as a function of pattern index. (y-axis)
        =============  ===================  ======================================================
        
        """
        message = "setp {} {}".format(pattern_index, pattern_val).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def get_pattern_value(self, pattern_index):
        """
        Read value no. <PIDX> from the user curve.
        
        =============  ===================  ======================================================
        **Argument**   **Range of values**  **Description**
        pattern_index  (0,255)              Pattern index of choice (x-axis)
        pattern_value  (0,255)              Pattern value as a function of pattern index. (y-axis)
        =============  ===================  ======================================================
        
        """
        message = "getp {}".format(pattern_index).encode()
        resp = self.ask_cmd(message)
        return resp
    
    def reset_patterns(self):
        """
        Reset all patterns to factory defaults.
        """
        message = b"Resetp"
        resp = self.ask_cmd(message)
        return resp
    
    def close(self):
        self.ser.close()
        del self.ser
        
    def __del__(self):
        self.close()
        
        
        
        
        
        