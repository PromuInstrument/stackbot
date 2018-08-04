'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

import serial
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class MKS_600_Interface(object):
        
    name = 'mks_600_interface'
    
    def __init__(self, port="COM5", debug=False):
        self.port = port
        self.debug = debug
        
        self.lock = Lock()
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=serial.EIGHTBITS, timeout=1,
                                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.ser.flush()
        
        time.sleep(1)
    
        #Below variables store values temporarily in order to account for serial timing issues.
    
        self.channels = {'A': 1, 
                    'B': 2, 
                    'C': 3,
                    'D': 4,
                    'E': 5}
    
        self.units = None 
        self.float = None
        self.prtemp = None
        self.valve_open = None
        self.sensor_range = None
        self.error_count = 0
        
    def ask_cmd(self, cmd):
        """
        Sends serial command to MKS 600 unit with proper formatting. 
        Retrieves response from the unit.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        cmd            str         Command or query to be sent to MKS 600 unit.
        =============  ==========  ==========================================================

        :returns: String containing unit's response to query.
        """
        with self.lock:
            self.ser.flush()
            message = cmd+'\r\n'
            self.ser.write(message)
            resp = self.ser.readline()
        return resp
    
    def read_sensor_range(self):
        """
        Reads range of attached capacitance manometer.
        
        :returns: Manometer full range value in Torr as a float
        """
        resp = self.ask_cmd("R33")[1:-2]
        if resp != b'':
            value = int(resp)
            ranges = {0: 0.1, 1: 0.2, 2: 0.5, 3: 1,
                      4: 2, 5: 5, 6: 10, 7: 50, 8: 100,
                      9: 500, 10: 1000, 11: 5000, 12:10000,
                      13: 1.33, 14: 2.66, 15: 13.33, 16: 133.3,
                      17: 1333, 18: 6666, 19: 13332
                    }
            resp = ranges[value]
            ## Store successfully retrieved value
            self.sensor_range = resp
            return float(resp)
        else:            
            self.error_count += 1
            ## Read failed, return last stored value
            return self.sensor_range
        

    def read_pressure(self):
        """
        Reads system pressure as detected by the attached capacitance manometer.
        Queries the full scale range percentage and converts this to a pressure value.
        
        :returns: Pressure value as a float
        """
        resp = self.ask_cmd("R5")[1:-2]
        if resp != b'':
            pct = float(resp)
            dec = pct/100
            fs = self.read_sensor_range()
            self.prtemp = dec*fs
            return self.prtemp
        else:
            print("Pressure misread, using last stored temp value.")
            self.error_count += 1
            self.ser.flush()
            ## Read failed, return last stored value
            return self.prtemp

        
    def switch_sp(self, ch):
        """
        Switches preset channels. Each channel has a set point value set by the controller's user.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        ch             int         Preset channel to mark as active. 
                                   Accepts values in the range (1,6)
        =============  ==========  ==========================================================
        
        """
        assert 1 <= ch < 6
        self.ask_cmd("D{:d}".format(ch))

    
    def enable_position_mode(self, ch):
        """
        Enable position mode on targeted preset channel.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        ch             int         Preset channel to mark as active. 
                                   Accepts values in the range (1,6)
        =============  ==========  ==========================================================
        
        """
        cmd = "T{} 0".format(self.channels[ch])
        self.ask_cmd(cmd)
    
    def enable_pressure_mode(self, ch):
        """
        Enable pressure regulation mode on targeted preset channel.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        ch             int         Preset channel to mark as active. 
                                   Accepts values in the range (1,6)
        =============  ==========  ==========================================================
        """
        cmd = "T{} 1".format(self.channels[ch])
        self.ask_cmd(cmd)

    
    def read_control_mode(self, ch):
        """
        Reads the control mode of selected preset channel
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        ch             int         Preset channel to mark as active. 
                                   Accepts values in the range (1,6)
        =============  ==========  ==========================================================
        
        :returns: control mode in form of a boolean integer. 
        
         * 0 indicates control by position
         * 1 indicates control by pressure set point
        """
        channels = {1: 26,
                    2: 27,
                    3: 28,
                    4: 29,
                    5: 30}
        cmd = "R{}".format(channels[ch])
        resp = int(self.ask_cmd(cmd).strip().decode()[-1])
        return resp
    
    def write_set_point(self, ch, pct):
        """
        Writes set point value of selected preset channel.
        Writes percentage of full scale pressure value or percentage position to selected preset channel.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        ch             int         Preset channel to read set point from. 
                                   Accepts values in the range (1,6)
        pct            int         Percentage open to write to set point preset
        =============  ==========  ==========================================================
        
        """
        cmd = "S{} {}".format(ch, int(pct))
        self.ask_cmd(cmd)
    
    def read_set_point(self, ch):
        """
        Reads set point value of selected preset channel.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        ch             int         Preset channel to read set point from. 
                                   Accepts values in the range (1,6)
        =============  ==========  ==========================================================
        
        :returns: Percentage of full scale pressure value or position percentage of selected preset channel as a float
        """
        channels = {1: 1,
                     2: 2,
                     3: 3,
                     4: 4,
                     5: 10}
        resp = self.ask_cmd("R{}".format(channels[ch]))[3:].strip()
        return float(resp)
    
    def read_valve_position(self):
        """
        Reads valve position
        :returns: Valve percentage open as float
        """
        resp = self.ask_cmd("R6")[2:-2]
        return float(resp)
        
    def valve_full_open(self, open_valve):
        """
        Fully opens or closes valve.
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        open           bool        Valve opens to 100% if True,
                                   Closes to 0% if False.
        =============  ==========  ==========================================================
        
        """
        assign = {True: "O",
                  False: "C"}
        self.ask_cmd(assign[open_valve])
    
    def halt_valve(self):
        """Halt valve at current position"""
        self.ask_cmd("H")
        
    
    def close(self):
        """Properly closes serial connection to throttle valve controller."""
        self.ser.close()
        del self.ser