'''
Created on Jan 30, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                         <alanbuckley@berkeley.edu>
                         
'''

import numpy as np
import serial
import time
from threading import Lock

class ALDRelayInterface(object):
    
    name = "ALD_relay_interface"
    
    def __init__(self, port="COM4", debug=False):
        """Sets initial parameters and sets up a blank integer array [size (4,4)] for storing relay states."""
        self.port = port
        self.debug = debug
        self.lock = Lock()
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=0.5, write_timeout=0.5)
        self.ser.flush()
        time.sleep(1)
        ## Create array representing current relay state:
        self.relay_array = np.zeros((4,4), dtype=np.int16)
        
        # Array column assigments:
        self.relay_num = 0
        self.state = 1
        self.pulse_width = 2
        self.pulse_running = 3
        
    def write_cmd(self, cmd):
        """
        Sends serial command to the Arduino with proper formatting. 
        Retrieves response from the unit.
        
        =============  ==========  ==========================================================
        **Arguments**  **Type**    **Description**
        cmd            str         Command or query to be sent to the Arduino.
        =============  ==========  ==========================================================

        :returns: (str) Arduino's response to query.

        """
        self.ser.flush()
        message = cmd+'\n'
        with self.lock:
#             self.ser.write(message)
            self.ser.write(message.encode())
            resp = self.ser.readline().decode()
        return resp
    
    def resp_loop(self):
        """Read multi-line output of polling function and fill out self.relay_array"""
        self.ser.flush()
        message = '1?\n'
        with self.lock:
            self.ser.write(message)
            attempts = 4
            row = 0
            while attempts > 0:
                resp = self.ser.readline().decode()
                output = np.array(resp.strip().split("|")[1:], np.int32)
                if output.shape[0] != 0:
                    asint = output.reshape(1,4)
                    self.relay_array[row] = asint
                    row += 1
                else:
                    print('pass')
                    pass
                attempts -= 1

        
    def write_state(self, pin, value):
        """
        Manually toggle a relay
        
        ================  ==============  ================================  ===============
        **Arguments**     **Type**        **Description**                   **Valid Range**
        pin               int             Boolean integer which tells the   (0, 1)
                                          controller whether or not to run
                                          its PID control mode.
                                          See table below.
        value             bool or int     State to be written to pulse      * (0, 1)
                                          valve                             * True/False
        ================  ==============  ================================  ===============
        
        =============  ===============
        **Argument**   **Description**
        True (1)       Close
        False (0)      Open           
        =============  ===============
        """
        assert pin in (0,1,2,3)
        state = int(value)
        choices = {0: 'o',
                   1: 'c'}
        cmd = "{}{}".format(pin, choices[state])
        self.write_cmd(cmd)
        
    def send_pulse(self, pin, duration):
        """
        Order a relay to send a pulse.
        
        =============  ==========  ==================================================  =================
        **Arguments**  **Type**    **Description**                                     **Valid Range**
        pin            int         Relay channel to actuate                            (1,4)
 
        width          int         Duration pulse should remain open in milliseconds   (10,)
        =============  ==========  ==================================================  =================

        """
        cmd = "{}t={}".format(pin, int(duration))
        self.write_cmd(cmd)
        
    def poll(self):
        """
        Ask Arduino to report on relay states by running self.resp_loop()
        :returns: self.relay_array
        """
        self.resp_loop()
        return self.relay_array

    
    def close(self):
        """Closes serial connection and throws out serial object."""
        self.ser.close()
        del self.ser       