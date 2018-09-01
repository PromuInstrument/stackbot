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
        self.line_names = "01234567"
        HardwareComponent.__init__(self, app, debug)
        
        
        
    def setup(self):
        self.settings.New('DIO_port', dtype=str, initial='Dev1/port0/line0:7')
        self.settings.New('dac_sp', dtype=float, ro=False, unit='V')
        self.settings.New('dac_channel', dtype=str, initial='/Dev1/ao0')
        self.settings.New('adcV', dtype=float, ro=True, unit='V')
        self.settings.New('adc_channel', dtype=str, initial='/Dev1/ai0')
        self.settings.New('adc_range', dtype=float, initial=10, unit='V')
        self.settings.New('adc_config', dtype=str, initial='default', 
                          choices=['default', 'rse', 'nrse', 'diff', 'pdiff'])
        
        self.line_pins = dict()
        for pin_i, line_name in enumerate(self.line_names):
            if line_name == '_':
                continue
            self.line_pins[line_name] = pin_i
            self.settings.New(name=line_name, dtype=bool)
            
    def connect(self):
        self.dio_task = mx.Task()
        self.dio_task.CreateDOChan(self.settings['DIO_port'], "", mx.DAQmx_Val_ChanForAllLines)
        
        self.dac_task = NI_DacTask(channel=self.settings['dac_channel'], name='ni_dac')
        self.dac_task.set_single()
        self.dac_task.start()
        
        self.adc_task = NI_AdcTask(channel=self.settings['adc_channel'], 
                                   range=self.settings['adc_range'], name='ni_adc',
                                   terminalConfig=self.settings['adc_config'])
        self.adc_task.set_single()
        self.adc_task.start()
        
        
        for line_name, pin in self.line_pins.items():
            self.settings.get_lq(line_name).connect_to_hardware(
                write_func=self.write_digital_lines)
        self.settings.get_lq('dac_sp').connect_to_hardware(
                                        write_func=self.dac_task.set)
        self.settings.get_lq('adcV').connect_to_hardware(
                                        read_func=self.read_adc_single)
        
    def write_digital_lines(self, x=None):
        writeArray = np.zeros(8, dtype=mx.c_uint8)
        for line_name, pin in self.line_pins.items():
            pin_bool = int(self.settings[line_name])
            writeArray[pin] = pin_bool
        
        sampsPerChanWritten = mx.c_int32()
        
        self.dio_task.WriteDigitalLines(numSampsPerChan=1, autoStart=True, timeout=0,
                                    dataLayout=mx.DAQmx_Val_GroupByChannel, 
                                    writeArray=writeArray, sampsPerChanWritten=mx.byref(sampsPerChanWritten), reserved=None)
        
    def read_adc_single(self):
        resp = self.adc_task.get()
        if self.debug_mode.val:
            self.log.debug('read_adc_single resp: {}'.format(resp))
        return float(resp[0])
    
    
    def disconnect(self):
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
            
    