'''
Created on Oct 27, 2014

@author: Edward Barnard
'''
import serial
import time

class ShutterServoArduino(object):

    CLOSE_POSITION = 0
    OPEN_POSITION = 45

    def __init__(self, port="COM22", debug = False):
        self.port = port
        self.debug = debug
        
        if self.debug: print "ShutterServoArduino init, port=%s" % self.port
        
        self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
                                 
                                 #baudrate=9600, 
                                 #bytesize=8, parity='N', stopbits=1, 
                                 #xonxoff=0, rtscts=0, timeout=1.0)
        self.ser.flush()
        time.sleep(0.1)
        #self.write_posititon(1)
        #self.read_position()
        self.position=0
        
    def send_cmd(self, cmd):
        if self.debug: print "send_cmd:", repr(cmd)
        self.ser.write(cmd + "\n")
    
    def ask(self, cmd):
        if self.debug: print "ask:", repr(cmd)
        self.send_cmd(cmd)
        resp = self.ser.readline()
        if self.debug: print "resp:", repr(resp)
        return resp 
    
    
    def write_posititon(self, pos):
        pos = int(pos)
        assert 0 <=  pos <= 180
        self.send_cmd(str(pos))
        self.position = pos
        return self.position

    def read_position(self):
        resp = self.ask("?")
        self.position = int(resp)
        return self.position
        
    def move_open(self, open=True):
        if open:
            self.write_posititon(self.OPEN_POSITION)
        else:
            self.move_close()

    def move_close(self):
        return self.write_posititon(self.CLOSE_POSITION)

    def read_open(self):
        pos = self.read_position()
        assert pos in (self.OPEN_POSITION, self.CLOSE_POSITION)
        if pos == self.OPEN_POSITION:
            return True
        if pos == self.CLOSE_POSITION:
            return False
        else:
            raise ValueError()
        
    def close(self):
        self.ser.close()        