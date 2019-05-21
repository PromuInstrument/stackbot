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
import time



class NI_MFC2(HardwareComponent):
    
    """
    Hardware component for use with National Instruments USB-6001 DAQ device.
    
    * Sets hardware addresses
        * Addresses must mirror those listed in NI MAX utility.
    * Creates Logged Quantities 
    * Connects with National Instruments USB-6001 DAQ device through python \
        wrapped NI DAQmx drivers. 
    * Establishes software level and hardware dependent settings and limits \
        in :meth:`setup`
    * Defines functions needed to read and write flow rates to connected Mass \
        Flow Controller. 
    """
    
    name = 'ni_mfc2'
    
    def __init__(self, app, debug=False):
        self.mfc_assignments = [3,]
        self.line_names = []
        for i in self.mfc_assignments:
            self.line_names.append('valve{}_close'.format(i))
            self.line_names.append('valve{}_open'.format(i))

        HardwareComponent.__init__(self, app, debug)
        
    def setup(self):
        """
        * Defines I/O port addresses.
        * Establishes *LoggedQuantities*
        * Creates buffers to store MFC flow data.
        * Establishes :attr:`dict` relating pin numbers \
            and the labels used to refer to said pins.
        * Full scale (fs) and limit (lim) values are defined \
            here as :attr:`self.mfc3_fs` and :attr:`self.mfc3_lim` 
            respectively.
        """        
        self.daq_name = '/Dev2/'
        self.dio_port = self.daq_name+'port0/line0:7'
        
        self.set_voltage_channel = self.daq_name+'ao0:1'
        
        self.flow_voltage_range = 5.0
        self.flow_voltage_channel = self.daq_name+'ai0:1'
        
        self.adc_config = 'diff'
        
        ## Set up buffer arrays to store I/O data (flow rate read/write).
        self.ai_buffer = np.zeros(2)
        self.ao_buffer = np.zeros(2)
        
        self.line_pins = dict()
        for pin_i, line_name in enumerate(self.line_names):
            if line_name == '_':
                continue
            self.line_pins[line_name] = pin_i
            
            self.settings.New(name=line_name, dtype=bool)

        ## Set full scale values
        self.mfc3_fs = 200
        self.mfc3_lim = 25
        self.mfc4_fs = 20
        self.mfc4_lim = 20
        
        ## Define flow related logged quantities
        for i in self.mfc_assignments:
            limit = getattr(self, 'mfc{}_lim'.format(i))
            self.settings.New(name='write_mfc{}'.format(i), dtype=float, initial=0.0, vmin=0.0, vmax = limit, ro=False)
            self.settings.New(name='read_mfc{}'.format(i), dtype=float, initial=0.0, ro=True)

        
    def connect(self):
        """
        Creates and instantiates NI task objects thereby creating a connection to the NI ADC/DAC controller
        Connects logged quantities to their respective functions.
        
        :attr:`self.settings.valve_open` and :attr:`self.settings.valve_closed` serve as override settings.
        If neither are active, the Mass Flow Controller opens to a degree defined by the setpoint.

        
        """
        self.dio_task = mx.Task()
        self.dio_task.CreateDOChan(self.dio_port, "", mx.DAQmx_Val_ChanForAllLines)
        
        self.dac_task = NI_DacTask(channel=self.set_voltage_channel, name='ni_dac2')
        self.dac_task.set_single()
        self.dac_task.start()
        
        self.adc_task = NI_AdcTask(channel=self.flow_voltage_channel, 
                                   range=self.flow_voltage_range, name='ni_adc2',
                                   terminalConfig=self.adc_config)
        self.adc_task.set_single()
        self.adc_task.start()
        
        
        for line_name, _ in self.line_pins.items():
            self.settings.get_lq(line_name).connect_to_hardware(
                write_func=self.write_digital_lines)
        
        for i in self.mfc_assignments:
            self.settings.get_lq('write_mfc{}'.format(i)).connect_to_hardware(
                                                write_func=getattr(self, 'write_flow{}'.format(i)))
            self.settings.get_lq('read_mfc{}'.format(i)).connect_to_hardware(
                                                read_func=getattr(self, 'read_flow{}'.format(i)))
        
        time.sleep(1)
        
        for i in self.mfc_assignments:
            self.settings['write_mfc{}'.format(i)] = 0.0
       

    def write_flow3(self, flow):
        """
        Converts user supplied flow value and scales it to a voltage, \
        which is then written to its slot in :attr:`self.ao_buffer` \
        and sent to the National Instruments card.
        The card then utilizes an analog signal to change the set point on MFC 3.

        Each MFC has a manufacturer specified full scale flow rate, which is scaled to a signal of +5V.
        
        =============  ==========  =========================  ====================
        **Arguments**  **type**    **Description**            **Valid Range**
        flow           float       Desired flow rate in MFC.  (0.0, Full Scale)
        =============  ==========  =========================  ====================
        
        """
        full_scale = self.mfc3_fs
        assert 0.0 <= flow <= self.mfc3_lim
        sf = full_scale/5.0
        voltage = (1/sf)*flow
        self.ao_buffer[0] = voltage
        self.dac_task.set(self.ao_buffer)
    
    def write_flow4(self, flow):
        """
        Converts user supplied flow value and scales it to a voltage, \
        which is then written to its slot in :attr:`self.ao_buffer` \
        and sent to the National Instruments card.
        The card then utilizes an analog signal to change the set point on MFC 4.

        Each MFC has a manufacturer specified full scale flow rate, which is scaled to a signal of +5V.
        
        =============  ==========  =========================  ====================
        **Arguments**  **type**    **Description**            **Valid Range**
        flow           float       Desired flow rate in MFC.  (0.0, Full Scale)
        =============  ==========  =========================  ====================
        
        """
        full_scale = self.mfc4_fs
        assert 0.0 <= flow <= self.mfc4_lim
        sf = full_scale/5.0
        voltage = (1/sf)*flow
        self.ao_buffer[1] = voltage
        self.dac_task.set(self.ao_buffer)
    
    
    def read_flow3(self):
        """
        Reads voltages from all channels of National Instruments card which may or may not \
        have a connected Mass Flow Controller. 
        Stores voltages to :attr:`self.ai_buffer` array. Scales read voltage to flow value.
        Connected MFC has a manufacturer specified full scale flow rate, which is scaled to a signal of up to +5V.
                
        :returns: (float) Flow rate detected in MFC 3 in units of sccm.
        """
        full_scale = self.mfc3_fs
        sf = full_scale/5.0
        readout = self.adc_task.get()
        voltage = np.asarray(readout, dtype=np.float16)
        self.ai_buffer = sf*voltage
        return self.ai_buffer[0]
    
    def read_flow4(self):
        """
        Reads voltages from all channels of National Instruments card which may or may not \
        have a connected Mass Flow Controller. 
        Stores voltages to :attr:`self.ai_buffer` array. Scales read voltage to flow value.
        Connected MFC has a manufacturer specified full scale flow rate, which is scaled to a signal of up to +5V.
                
        :returns: (float) Flow rate detected in MFC 4 in units of sccm.
        """
        full_scale = self.mfc4_fs
        sf = full_scale/5.0
        readout = self.adc_task.get()
        voltage = np.asarray(readout, dtype=np.float16)
        self.ai_buffer = sf*voltage
        return self.ai_buffer[1]

            
    def write_digital_lines(self, x=None):
        """Writes boolean array to digital in/out (DIO) channels. """
        self.writeArray = np.zeros(8, dtype=mx.c_uint8)
        for line_name, pin in self.line_pins.items():
            pin_bool = int(not self.settings[line_name])
            self.writeArray[pin] = pin_bool        
        sampsPerChanWritten = mx.c_int32()
        self.dio_task.WriteDigitalLines(numSampsPerChan=1, autoStart=True, timeout=0,
                                    dataLayout=mx.DAQmx_Val_GroupByChannel, 
                                    writeArray=self.writeArray, sampsPerChanWritten=mx.byref(sampsPerChanWritten), reserved=None)

        
    def read_adc_single(self):
        """
        Deprecated. Call :meth:`read_flow1` or :meth:`read_flow2`
        Reads voltage off analog in channel 1 (AI 0). In the case of this module, 
        this channel reads the value of our MFC's Flow Signal Output.
        
        :returns: (float) Analog In voltage.
        """
        resp = self.adc_task.get()
        if self.debug_mode.val:
            self.log.debug('read_adc_single resp: {}'.format(resp))
        return float(resp[0])
    
    
    def disconnect(self):
        """Disconnects logged quantities from their respective functions
        Stops NI Tasks and removes Task objects (a proper means of disconnecting \
        from National Instruments hardware.)
        """
        for i in self.mfc_assignments:
            self.settings['write_mfc{}'.format(i)] = 0.0
        time.sleep(1)
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
            
    