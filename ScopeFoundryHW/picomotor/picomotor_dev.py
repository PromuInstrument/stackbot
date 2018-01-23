'''
Created on Jun 28, 2017

@author: Alan Buckley
'''

from __future__ import division, absolute_import, print_function
import serial
import time
import logging

logger = logging.getLogger(__name__)

class PicomotorDev(object):
    
    name="picomotor_dev"
    
    def __init__(self, serial_port=None, ip=None, ip_port=None, debug=False):
        self.debug = debug
        self.serial_port = serial_port
        self.ip = ip
        self.ip_port = ip_port    
        
        if self.serial_port is not None:
            self.ser = serial.Serial(port=self.port, baudrate=9600, timeout = 0.1)
        
        elif self.ip and self.ip_port:
            self.ser = serial.serial_for_url(url="socket://{}:{}".format(self.ip, self.ip_port))
       
        else:
            raise IOError("Please provide either ip & ip_port, or local serial port")
        
        if self.ser:
            self.ser.flush()
        
        time.sleep(0.2)

        
    def ask_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd.encode()+b'\r'
        self.ser.write(message)
        resp = self.ser.readline()[6::]
        print(resp)
        response = resp.strip().decode()
        if self.debug:
            logger.debug("readout: {}".format(response))
        self.ser.flush()
        return resp

    def send_cmd(self, cmd):
        if self.debug: 
            logger.debug("ask_cmd: {}".format(cmd))
        message = cmd.encode()+b'\r'
        self.ser.write(message)
        self.ser.flush()
    
    def abort(self):
        """For use with velocity command. Does not use deceleration."""
        message = "AB".encode()
        self.send_cmd(message)
    
    def read_pos(self, axis):
        assert  (1 <= int(axis) <= 4)
        message = "{:02d}PA?".format(int(axis))
        self.ask_cmd(message)
    
    def write_pos(self, axis, steps):
        assert (1 <= int(axis) <= 4)
        assert (-2147483648 <= steps <= 2147483647)
        message = "{:02d}PA{}".format(int(axis), int(steps))
        self.send_cmd(message)
    
    def read_rel_pos(self, axis):
        assert  (1 <= int(axis) <= 4)
        message = "{:02d}PR?".format(int(axis))
        self.ask_cmd(message)
    
    def write_rel_pos(self, axis, steps):
        assert (1 <= int(axis) <= 4)
        assert (-2147483648 <= steps <= 2147483647)
        message = "{:02d}PR{}".format(int(axis), int(steps))
        self.send_cmd(message)
        
        
    def read_velocity(self, axis):
        assert (1 <= int(axis) <= 4)
        assert (1 <= int(axis) <= 2000)
        message = "{:02d}VA?".format(int(axis))
        self.ask_cmd(message)
    
    def write_velocity(self, axis, step_rate):
        assert (1 <= int(axis) <= 4)
        assert (1 <= int(axis) <= 2000)
        message = "{:02d}VA{}".format(int(axis), int(step_rate))
        self.send_cmd(message)
    
    def stop(self):
        """For use with acceleration motion of the motor. Uses deceleration."""
        assert (1 <= int(axis) <= 4)
        message = "{:02d}ST".format(int(axis))
        self.send_cmd(message)
        
    def close(self):
        self.ser.close()
    