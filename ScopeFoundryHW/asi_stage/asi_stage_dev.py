import serial
import time
import threading

class ASIXYStage(object):
    
    def __init__(self, port='COM5', debug=False):
        self.port = port
        self.debug = debug
        self.ser = serial.Serial(port=self.port,
                         baudrate=115200,
                         # waiting time for response [s]
                         timeout=0.1,
                         bytesize=8, parity='N', 
                         stopbits=1, xonxoff=0, rtscts=0)

        self.ser.write(b'\b') # <del>  or  <bs>- Abort current command and flush input buffer
        #self.ser.flush() # flush output buffer
        self.ser.read(100)
        
        # Stage Info:
        # lead screw pitch: 6.35mm
        # achievable speed: 7mm/s
        # encoder resolution: 22nm
        
        self.unit_scale = 1e4 # convert internal units 1/10um to mm

        # threading lock
        self.lock = threading.Lock()
        
    def close(self):
        self.ser.close()
        
    def send_cmd(self, cmd):
        cmd_bytes = (cmd + '\r').encode()
        if self.debug: print("ASI XY cmd:", repr(cmd), repr(cmd_bytes))
        self.ser.write(cmd_bytes)
        if self.debug: print ("ASI XY done sending cmd")
        
    def ask(self, cmd): # format: '2HW X' -> ':A 355'
        with self.lock:
            self.send_cmd(cmd)
            resp1 = self.ser.readline()
            if self.debug: print("ASI XY ask resp1:", repr(resp1))
            resp2 = self.ser.read(1)
            if self.debug: print("ASI XY ask resp2:", repr(resp2))

        
        assert resp2 == b'\x03' # End of text (Escape sequence)
        
        resp1 = resp1.decode()

        assert resp1.startswith(":A")
        
        if resp1.startswith(":AERR0"):
            print("ASI-stage communication error: ERR0")
        else:
            return resp1[2:].strip() # remove whitespace


    def read_pos_x(self):
        x = self.ask("2HW X")
        return float(x)/self.unit_scale
    
    def read_pos_y(self):
        y = self.ask("2HW Y")
        return float(y)/self.unit_scale
    
    def is_busy_xy(self):
        with self.lock:
            self.send_cmd("2H/")  # status command has a different reply structure
            resp1 = self.ser.readline().decode()
            resp2 = self.ser.read(1)
        if self.debug: print("ASI isBusy resp1", repr(resp1))
        if self.debug: print("ASI isBusy resp2", repr(resp2))
        assert resp1[0] in 'NB'
        
        if resp1[0]=='N':   return False
        elif resp1[0]=='B': return True
    
    def wait_until_not_busy_xy(self, timeout=10):    
        t0 = time.time()
        while self.is_busy_xy():
            time.sleep(0.010)
            if time.time() - t0 > timeout:
                raise IOError("ASI stage took too long during wait")
            
    def move_x(self, target):
        self.ask("2HM X= {:d}".format(int(target*self.unit_scale)))
            
    def move_y(self, target):
        self.ask("2HM Y= {:d}".format(int(target*self.unit_scale)))
        
    def move_x_and_wait(self, target,timeout=10):
        if int(self.read_pos_x()*self.unit_scale) == int(target*self.unit_scale):
            return # avoid overriding with same value 
        self.move_x(target)
        self.wait_until_not_busy_xy(timeout)

    def move_y_and_wait(self, target,timeout=10):
        if int(self.read_pos_y()*self.unit_scale) == int(target*self.unit_scale):
            return # avoid overriding with same value 
        self.move_y(target)
        self.wait_until_not_busy_xy(timeout)

    def home_xy(self):
        self.ask("2HHOME X Y")
        
    def halt_xy(self):
        self.ask("2HHALT")
        
    def set_limits_xy(self, xl, xu, yl, yu): # x in [xl, xu], y in [yl, yu]
        self.ask("2HSL X= {:f} Y= {:f}".format(xl, yl))
        self.ask("2HSU X=" + str(xu) + " Y=" + str(yu))        


    