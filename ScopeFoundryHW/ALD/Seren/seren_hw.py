'''
Created on Jan 26, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''
from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ALD.Seren.seren_interface import Seren_Interface

class Seren_HW(HardwareComponent):
    
    """
    This interface level module is responsible for \
    establishing serial communication with the Seren RX01/LX01 \
    Series Radio Frequency Power Supply, and defining the basic \
    commands to be sent to the Power Supply Unit.
    """
    
    name = 'seren_hw'
    
    def setup(self):
        self.settings.New(name="port", initial="COM6", dtype=str, ro=False)
        self.settings.New(name="enable_serial", initial=True, dtype=bool, ro=False)
        self.settings.New(name="set_forward_power", initial=0, dtype=int, ro=False)
        self.settings.New(name="forward_power_readout", initial=0, dtype=int, ro=True)
        self.settings.New(name="reflected_power", initial=0, dtype=int, ro=True)
        self.settings.New(name="RF_enable", initial=False, dtype=bool, ro=False)
        
        self.seren = None
        
    def connect(self):
        self.seren = Seren_Interface(port=self.settings.port.val, debug=self.settings['debug_mode'])
        
        self.settings.enable_serial.connect_to_hardware(write_func=lambda x: self.serial_toggle(x))
        
        self.settings.RF_enable.connect_to_hardware(write_func=lambda x: self.RF_state(x))
        
        self.settings.set_forward_power.connect_to_hardware(write_func=lambda x: self.write_fp(x))
        
        self.settings.forward_power_readout.connect_to_hardware(read_func=self.read_fp)

        self.settings.reflected_power.connect_to_hardware(read_func=self.read_rp)

        self.settings.set_forward_power.add_listener(self.read_from_hardware)

        self.settings.RF_enable.add_listener(self.read_from_hardware)

        self.serial_toggle(True)

    def serial_toggle(self, status):
        """Sets serial or front panel control.
        
        Connected to *LoggedQuantity*   
        :attr:`self.settings.enable_serial`
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        status         bool        Serial enabled/disabled
        =============  ==========  ==========================================================
        """
        if status:
            self.seren.set_serial_control()
        else:
            self.seren.set_front_panel_control()
    
    def RF_state(self, status):
        """
        Enables or disables RF source.
        
        Connected to *LoggedQuantity*   
        :attr:`self.settings.RF_enable`
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        status         bool        RF emitter enabled/disbaled
        =============  ==========  ==========================================================
        """
        if status:
            self.seren.emitter_on()
        else:
            self.seren.emitter_off()

    def RF_toggle(self):
        """Toggles RF enable with each call by negating the value of
        *LoggedQuantity*
        :attr:`self.settings.RF_enable`
        """
        self.settings['RF_enable'] = not self.settings['RF_enable']

    
    def write_fp(self, power):
        """
        Writes forward power setting to Seren PSU.
        
        Connected to *LoggedQuantity*   
        :attr:`self.settings.set_forward_power`
        
        =============  ==========  ==========================================================
        **Arguments**  **type**    **Description**
        power          int         RF power setpoint in Watts
        =============  ==========  ==========================================================
        """
        self.seren.write_forward(int(power))
        
    def read_fp(self):
        """
        Reads set forward power from Seren PSU.
        
        Connected to *LoggedQuantity*   
        :attr:`self.settings.forward_power_readout`
        
        :returns: int. Forward power in Watts.
        """
        return self.seren.read_forward()
    
    def read_rp(self):
        """
        Reads reflected power from Seren PSU.
        
        Connected to *LoggedQuantity*   
        :attr:`self.settings.reflected_power`
        
        :returns: int. Reflected power in Watts.
        """
        resp = self.seren.read_reflected()
        return resp
    
    def disconnect(self):
        """
        Properly disconnects logged quantities from module functions.
        Closes serial connection to Seren PSU.
        """
        self.settings.disconnect_all_from_hardware()
        if self.seren is not None:
            self.seren.close()
        del self.seren
    