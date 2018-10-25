'''
Created on Aug 31, 2018

@author: Alan Buckley    <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''
from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ni_daq.devices.ni_dac_task import NI_DacTask
from ScopeFoundryHW.ni_daq.devices.NI_Daq import NI_AdcTask

import PyDAQmx as mx
import numpy as np



class NI_MFC(HardwareComponent):
    
    name = 'ni_mfc'
    
    def __init__(self, app, debug=False):
        self.line_names = ['valve_close', 'valve_open']
        HardwareComponent.__init__(self, app, debug)
        
    def setup(self):
        """
        * Defines I/O port addresses. 
        * Establishes *LoggedQuantities*
        * Establishes :attr:`dict` relating pin numbers \
            and the labels used to refer to said pins.
        """        
        self.dio_port = 'Dev1/port0/line0:7'
        
        self.set_voltage_channel = '/Dev1/ao0'
        
        self.flow_voltage_range = 5.0
        self.flow_voltage_channel = '/Dev1/ai0'
        
        self.adc_config = 'diff'
        
        self.line_pins = dict()
        for pin_i, line_name in enumerate(self.line_names):
            if line_name == '_':
                continue
            self.line_pins[line_name] = pin_i
            self.settings.New(name=line_name, dtype=bool)
            self.settings.get_lq(line_name).add_listener(self.override)
            
        self.settings.New(name='write_flow', dtype=float, initial=0.0, vmin=0.0, vmax = 20.0, ro=False)
        self.settings.New(name='read_flow', dtype=float, initial=0.0, ro=False)

        
    def connect(self):
        """
        Creates and instantiates NI task objects thereby creating a connection to the NI ADC/DAC controller
        Connects logged quantities to their respective functions.
        
        :attr:`self.settings.valve_open` and :attr:`self.settings.valve_closed` serve as override functions.
        If neither are active, the Mass Flow Controller opens to a degree defined by the setpoint.

        
        """
        self.dio_task = mx.Task()
        self.dio_task.CreateDOChan(self.dio_port, "", mx.DAQmx_Val_ChanForAllLines)
        
        self.dac_task = NI_DacTask(channel=self.set_voltage_channel, name='ni_dac')
        self.dac_task.set_single()
        self.dac_task.start()
        
        self.adc_task = NI_AdcTask(channel=self.flow_voltage_channel, 
                                   range=self.flow_voltage_range, name='ni_adc',
                                   terminalConfig=self.adc_config)
        self.adc_task.set_single()
        self.adc_task.start()
        
        
        for line_name, _ in self.line_pins.items():
            self.settings.get_lq(line_name).connect_to_hardware(
                write_func=self.write_digital_lines)
        
        self.settings.get_lq('write_flow').connect_to_hardware(
                                            write_func=self.write_flow)
        self.settings.get_lq('read_flow').connect_to_hardware(
                                            read_func=self.read_flow)

    def override(self):
        """
        Function ensures that both overrides are unable \
        to be simultaneously activated.
        
        This function is set as the listener function for 
        :attr:`self.settings.valve_open` and :attr:`self.settings.valve_closed`
        """
        if self.settings['valve_open']:
            self.settings['valve_close'] = False
        elif self.settings['valve_close']:
            self.settings['valve_open'] = False
        else:
            pass

    def write_flow(self, flow):
        """
        Converts user supplied flow value and scales it to a voltage 
        read by the MFC analog interface.
        Our particular MFC has a flow rate of 20 sccm, which corresponds to a signal of +5V.
        
        =============  ==========  =========================  ====================
        **Arguments**  **type**    **Description**            **Valid Range**
        flow           float       Desired flow rate in MFC.  (0.0, 20.0)
        =============  ==========  =========================  ====================
        
        """
        assert 0.0 <= flow <= 20.0
        voltage = (1/4)*flow
#         voltage = 1*flow
        self.dac_task.set(voltage)
    
    def read_flow(self):
        """
        Reads voltage from MFC analog interface. Scales voltage to flow value.
        Our particular MFC has a flow rate of 20 sccm, which corresponds to a signal of +5V.
        
        :returns: (float) Flow rate detected in MFC in units of sccm.
        """
        voltage = self.read_adc_single()
        flow = 4*voltage
#         flow = voltage
        return flow

            
    def write_digital_lines(self, x=None):
        """Writes boolean values to digital in/out channels."""
        self.writeArray = np.zeros(8, dtype=mx.c_uint8)
        for line_name, pin in self.line_pins.items():
            pin_bool = int(self.settings[line_name])
            self.writeArray[pin] = pin_bool        
        sampsPerChanWritten = mx.c_int32()
        self.dio_task.WriteDigitalLines(numSampsPerChan=1, autoStart=True, timeout=0,
                                    dataLayout=mx.DAQmx_Val_GroupByChannel, 
                                    writeArray=self.writeArray, sampsPerChanWritten=mx.byref(sampsPerChanWritten), reserved=None)

        
    def read_adc_single(self):
        """
        Reads voltage off analog to digital converter. In the case of this module, 
        this channel reads the value of our MFC's Flow Signal Output.
        
        :returns: (float) Analog In voltage.
        """
        resp = self.adc_task.get()
        if self.debug_mode.val:
            self.log.debug('read_adc_single resp: {}'.format(resp))
        return float(resp[0])
    
    
    def disconnect(self):
        """Disconnects logged quantities from their respective functions
        Stops NI Tasks and removes Task objects.
        """
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'task'):
            self.dio_task.StopTask()
            del self.dio_task
        if hasattr(self, 'dac_task'):
            self.dac_task.close()
            del self.dac_task
        if hasattr(self, 'adc_task'):
            self.adc_task.close()
            del self.adc_task
            
    