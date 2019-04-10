from ScopeFoundry import HardwareComponent
import threading
import time

try: 
    from .lakeshore_interface import Lakeshore331Interface
except Exception as ex:
    print("Cannot load required module for Lakeshore 331 T Controller", ex)
    
class Lakeshore331HW(HardwareComponent):
    
    name = 'lakeshore331'
    
    def __init__(self,app,name=None,debug=False,port='COM7'):
        HardwareComponent.__init__(self,app,debug=debug,name=name)
        self.debug=debug
        S = self.settings
        S.New('port',ro=False,initial=port,dtype=str)
        S.New('T_A',ro=True,initial=0.0,unit='K')
        S.New('T_B',ro=True,initial=0.0,unit='K')
        S.New('analog_out_enable',ro=False,initial=False,dtype=bool)
        S.New('analog_out_channel',ro=False,initial='B',dtype=str,choices=['A','B'])
        S.New('T_at_10V',ro=False,initial=1000.0,dtype=float,unit='K')
        S.New('T_at_0V',ro=False,initial=0.0,dtype=float,unit='K')
    
    def setup(self):
        pass
    
    def connect(self):
        self.face = Lakeshore331Interface(debug = self.debug, port=self.settings.port.value)
        S = self.settings
        print(self.face.info())
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        self.update_thread.start()
        resp_dict = self.face.get_output()

        S.analog_out_enable.connect_to_hardware(
            read_func=self.face.get_output_enabled,
            write_func=self.face.set_output_enabled)
        S.analog_out_enable.read_from_hardware()
        
        S.analog_out_channel.connect_to_hardware(
            read_func=self.face.get_output_channel,
            write_func=self.face.set_output_channel)
        S.analog_out_channel.read_from_hardware()
        
        S.T_at_10V.connect_to_hardware(
            read_func=self.face.get_output_vmax,
            write_func=self.face.set_output_vmax)
        S.T_at_10V.read_from_hardware()
        
        S.T_at_0V.connect_to_hardware(
            read_func=self.face.get_output_vmin,
            write_func=self.face.set_output_vmin)
        S.T_at_0V.read_from_hardware()
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread
    
        if hasattr(self,'face'):        
            self.face.send_cmd('*CLS')
            self.face.read_resp()
            self.face.close()
            del self.face
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            self.settings.T_A.update_value(self.face.read_T(chan='A'))
            self.settings.T_B.update_value(self.face.read_T(chan='B'))
            time.sleep(1.0)