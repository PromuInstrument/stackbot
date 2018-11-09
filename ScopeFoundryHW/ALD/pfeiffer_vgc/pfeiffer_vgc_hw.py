'''
Created on Nov 20, 2017

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.ALD.pfeiffer_vgc.pfeiffer_vgc_interface import Pfeiffer_VGC_Interface

class Pfeiffer_VGC_Hardware(HardwareComponent):
    
    """
    This hardware component module establishes a connection with the Pfeiffer MaxiGauge TPG 256A 
    and connects its *LoggedQuantities* to their respective functions.
    
    **IMPORTANT:** Call functions defined in this Hardware module to retrieve data 
    as opposed to calling lower level functions. These functions account for the way data is structured
    when returned at the lower level.
    """
    
    name = "pfeiffer_vgc_hw"
    
    def setup(self):
        self.settings.New(name="port", initial="COM3", dtype=str, ro=False)
        self.ch1 = self.settings.New(name="ch1_pressure", initial=0.0, si=True, unit='bar', fmt='%e', dtype=float, spinbox_decimals=6,  ro=True)
        self.ch2 = self.settings.New(name="ch2_pressure", initial=0.0, si=True, unit='bar', fmt='%e', dtype=float, spinbox_decimals=6, ro=True)
        self.ch3 = self.settings.New(name="ch3_pressure", initial=0.0, si=True, unit='bar', fmt='%e', dtype=float, spinbox_decimals=6, ro=True)
        
        self.ch1s = self.settings.New(name="ch1_pressure_scaled", initial=0.0, si=True, unit='torr', fmt='%.4e', spinbox_decimals=6, ro=True) 
        self.ch2s = self.settings.New(name="ch2_pressure_scaled", initial=0.0, si=True, unit='torr', fmt='%.4e', spinbox_decimals=6, ro=True)
        self.ch3s = self.settings.New(name="ch3_pressure_scaled", initial=0.0, si=True, unit='torr', fmt='%.4e', spinbox_decimals=6, ro=True)
        
        self.settings.New(name="ch1_sensor_type", initial="None", dtype=str,  ro=True)
        self.settings.New(name="ch2_sensor_type", initial="None", dtype=str,  ro=True)
        self.settings.New(name="ch3_sensor_type", initial="None", dtype=str,  ro=True)

        self.ch1s.connect_lq_scale(self.ch1, (76000/101325))
        self.ch2s.connect_lq_scale(self.ch2, (76000/101325))
        self.ch3s.connect_lq_scale(self.ch3, (76000/101325))
        
        self.vgc = None
        
        # Constants
        self.ch1_index, self.ch2_index, self.ch3_index = (0,1,2)
        
    def connect(self):
        """
        Establishes connections between *LoggedQuantities* and their readout functions.
        
        Automatically updates *LoggedQuantities* once to reflect system state at time of established connection.
        """
        self.vgc = Pfeiffer_VGC_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])

        self.settings.ch1_pressure.connect_to_hardware(read_func=getattr(self,'read_ch1_pressure'))
        
        self.settings.ch1_sensor_type.connect_to_hardware(read_func=getattr(self, 'read_ch1_sensor_type'))
        
        self.settings.ch2_pressure.connect_to_hardware(read_func=getattr(self,'read_ch2_pressure'))
        
        self.settings.ch2_sensor_type.connect_to_hardware(read_func=getattr(self, 'read_ch2_sensor_type'))
        
        self.settings.ch3_pressure.connect_to_hardware(read_func=getattr(self, 'read_ch3_pressure'))
        
        self.settings.ch3_sensor_type.connect_to_hardware(read_func=getattr(self, 'read_ch3_sensor_type'))
        
        self.settings.ch1_sensor_type.read_from_hardware()
        self.settings.ch2_sensor_type.read_from_hardware()
        self.settings.ch3_sensor_type.read_from_hardware()
        
    def read_ch1_pressure(self):
        """
        Reads pressure value off sensor installed on 
        pressure gauge controller's channel 1.
        
        :returns: float. Pressure value in units of bar.
        """
        sensor = self.ch1_index + 1
        return self.vgc.read_sensor(sensor)
    
    def read_ch1_sensor_type(self):
        """
        :returns: string. Sensor code representing the type of sensor \
        installed on pressure gauge controller's channel 1.
        """
        channel = self.ch1_index
        return self.vgc.sensor_type()[channel]
    
    def read_ch2_pressure(self):
        """
        Reads pressure value off sensor installed on 
        pressure gauge controller's channel 2.
        
        :returns: float. Pressure value in units of bar.
        """
        sensor = self.ch2_index + 1
        return self.vgc.read_sensor(sensor)
    
    def read_ch2_sensor_type(self):
        """
        :returns: string. Sensor code representing the type of sensor \
        installed on pressure gauge controller's channel 2.
        """
        channel = self.ch2_index
        return self.vgc.sensor_type()[channel]
    
    def read_ch3_pressure(self):
        """
        Reads pressure value off sensor installed on 
        pressure gauge controller's channel 3.
        
        :returns: float. Pressure value in units of bar.
        """
        sensor = self.ch3_index + 1
        return self.vgc.read_sensor(sensor)
        
    def read_ch3_sensor_type(self):
        """
        :returns: string. Sensor code representing the type of sensor \
        installed on pressure gauge controller's channel 3.
        """
        channel = self.ch3_index
        return self.vgc.sensor_type()[channel]
    
    def disconnect(self):
        """
        * Disconnects hardware module connections. 
        * Closes interface level serial connection.
        """
        self.settings.disconnect_all_from_hardware()
        if self.vgc is not None:
            self.vgc.close()
        del self.vgc
        