from ScopeFoundry import HardwareComponent
import threading
import time

try: 
    from .lakeshore_interface import Lakeshore331Interface, HEATER_RANGE_CHOICES, SENSOR_TYPES, CONTROL_MODES, SENSOR_CURVES
except Exception as ex:
    print("Cannot load required module for Lakeshore 331 T Controller", ex)
    

class Lakeshore331HW(HardwareComponent):
    
    name = 'lakeshore331'
    
    def __init__(self,app,name=None,debug=False,port='COM6'):
        HardwareComponent.__init__(self,app,debug=debug,name=name)
        self.debug=debug
        S = self.settings
        S.New('port',ro=False,initial=port,dtype=str)
        
        # Temperature readings
        S.New('T_A',ro=True,initial=0.0,unit='K')
        S.New('T_B',ro=True,initial=0.0,unit='K')
        
        # Analog out settings
        S.New('analog_out_enable',ro=False,initial=False,dtype=bool)
        S.New('analog_out_channel',ro=False,initial='B',dtype=str,choices=['A','B'])
        S.New('T_at_10V',ro=False,initial=1000.0,dtype=float,unit='K')
        S.New('T_at_0V',ro=False,initial=0.0,dtype=float,unit='K')
        
        # T control setpoint settings
        S.New('setpoint_T',ro=False,initial=20.0,dtype=float,unit='K')
        
        S.New('heater_output',ro=True,dtype=float,unit='%')
        S.New('heater_range',ro=False,dtype=str,initial=HEATER_RANGE_CHOICES[0],choices=HEATER_RANGE_CHOICES)
        S.New('control_mode',ro=False,dtype=str,initial=CONTROL_MODES[0],choices=CONTROL_MODES)
        
        S.New('ramp_onoff',ro=False,dtype=bool,initial=False)
        S.New('ramp_rate',ro=False,dtype=float,initial=10.0)
        S.New('is_ramping',ro=True,dtype=bool,initial=False)
        
        # Sensor settings
        S.New('type_A', ro=False, dtype=str, choices=SENSOR_TYPES)
        S.New('comp_A', ro=False, dtype=bool, initial=False)
        S.New('curve_A', ro=False, dtype=str, choices=SENSOR_CURVES)
        S.New('type_B', ro=False, dtype=str, choices=SENSOR_TYPES)
        S.New('comp_B', ro=False, dtype=bool, initial=False)
        S.New('curve_B', ro=False, dtype=str, choices=SENSOR_CURVES)
        
        self.add_operation("Reset", self.reset)
        
    def setup(self):
        pass
    
    def reset(self):
        self.face.reset()
    
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
            
        S.setpoint_T.connect_to_hardware(
            read_func=self.face.get_setpoint,
            write_func=self.face.set_setpoint)
        S.setpoint_T.read_from_hardware()
        
        S.heater_output.connect_to_hardware(
            read_func=self.face.get_heater_output)
        S.heater_output.read_from_hardware()
        
        S.heater_range.connect_to_hardware(
            read_func=self.face.get_heater_range,
            write_func=self.face.set_heater_range)
        S.heater_range.read_from_hardware()
        
        S.control_mode.connect_to_hardware(
            read_func=self.face.get_cmode,
            write_func=self.face.set_cmode)
        S.control_mode.read_from_hardware()
        
        def set_sensor_A_type(val):
            self.face.set_sensor_type(val,inp='A')
        def get_sensor_A_type():
            return self.face.get_sensor_type(inp='A')
        S.type_A.connect_to_hardware(
            read_func=get_sensor_A_type,
            write_func=set_sensor_A_type)
        S.type_A.read_from_hardware()
        
        def set_sensor_A_comp(val):
            self.face.set_sensor_comp(val,inp='A')
        def get_sensor_A_comp():
            return self.face.get_sensor_comp(inp='A')
        S.comp_A.connect_to_hardware(
            read_func=get_sensor_A_comp,
            write_func=set_sensor_A_comp)
        S.comp_A.read_from_hardware()
        
        def set_sensor_A_curve(val):
            self.face.set_input_curve(val, inp='A')
        def get_sensor_A_curve():
            self.face.get_input_curve(inp='A')
        S.curve_A.connect_to_hardware(
            read_func=get_sensor_A_curve,
            write_func=set_sensor_A_curve)
        
        def set_sensor_B_type(val):
            self.face.set_sensor_type(val,inp='B')
        def get_sensor_B_type():
            return self.face.get_sensor_type(inp='B')
        S.type_B.connect_to_hardware(
            read_func=get_sensor_B_type,
            write_func=set_sensor_B_type)
        S.type_B.read_from_hardware()
        
        def set_sensor_B_comp(val):
            self.face.set_sensor_comp(val,inp='B')
        def get_sensor_B_comp():
            return self.face.get_sensor_comp(inp='B')
        S.comp_B.connect_to_hardware(
            read_func=get_sensor_B_comp,
            write_func=set_sensor_B_comp)
        S.comp_B.read_from_hardware()
        
        def set_sensor_B_curve(val):
            self.face.set_input_curve(val, inp='B')
        def get_sensor_B_curve(val):
            self.face.get_input_curve(inp='B')
        S.curve_B.connect_to_hardware(
            read_func=get_sensor_B_curve,
            write_func=set_sensor_B_curve)
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread
    
        if hasattr(self,'face'):
            self.face.set_heater_range('off')
            self.face.set_cmode('Manual PID')
            self.face.set_output_enabled(False)        
            self.face.ask('*CLS')
            self.face.close()
            del self.face
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            self.settings.T_A.update_value(self.face.read_T(chan='A'))
            self.settings.T_B.update_value(self.face.read_T(chan='B'))
            self.settings.heater_output.read_from_hardware()
            time.sleep(1.0)