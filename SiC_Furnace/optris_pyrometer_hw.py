from ScopeFoundry import HardwareComponent
import threading
import serial
import time

class OptrisPyrometerHW(HardwareComponent):
    
    name = 'optris_pyrometer'
    
    def setup(self):
        
        self.settings.New('port', dtype=str, initial='COM1', )
        self.settings.New('temp', dtype=float, unit='C')
        
    def connect(self):
        
        self.lock = threading.Lock()
        
        self.ser = serial.Serial(self.settings['port'], 
                                 115200, bytesize=8, parity='N', stopbits=1,timeout=0.1)
        
        
        self.settings.temp.connect_to_hardware(
            read_func = self.read_temp)
        
        
        # read thread
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        self.update_thread.start()
        
        
    def read_temp(self):
        with self.lock:
            self.ser.write(b"\x01")
            x = self.ser.read(2)
        temp = 0.1*(x[0]*0xFF + x[1] - 1000)
        if self.settings['debug_mode']:
            self.log.debug("read_temp {}".format(temp))
        return temp
    
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread

        
        if hasattr(self, 'ser'):
            self.ser.close()
            del self.ser
            
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            self.settings.temp.read_from_hardware()
            time.sleep(1.0)
