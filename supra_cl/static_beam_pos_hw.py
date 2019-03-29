from ScopeFoundry.hardware import HardwareComponent
import PyDAQmx as mx
import numpy as np

class StaticBeamPositionHW(HardwareComponent):
    
    name = 'static_beam_pos'
    
    def setup(self):
        
        self.settings.New("ao_chan", dtype=str, initial="/X-6368/ao0:1")
        self.settings.New("x", dtype=float, unit='V')
        self.settings.New("y", dtype=float, unit='V')
        
    def connect(self):
        
        
        # Create Task
        self.task = mx.Task()

        #int32 DAQmxCreateAOVoltageChan (TaskHandle taskHandle,
        # const char physicalChannel[], 
        # const char nameToAssignToChannel[], 
        # float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);


        self.task.CreateAOVoltageChan(self.settings['ao_chan'], '', -10., 10., mx.DAQmx_Val_Volts, '')
        
        chan_count = mx.uInt32(0) 
        self.task.GetTaskNumChans(mx.byref(chan_count))
        self._chan_count = chan_count.value
        assert self._chan_count == 2
        
        # start
        self.task.StartTask()
        
        
        #connect settings to hardware
        self.settings.x.connect_to_hardware(
                                write_func=self.write_x)
        self.settings.y.connect_to_hardware(
                                write_func=self.write_y)

        # update hardware?
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'task'):
            self.task.StopTask()
            del self.task
            
            
    def write_x(self, new_x):
        self.write_xy(new_x, self.settings['y'])
    
    def write_y(self, new_y):
        self.write_xy(self.settings['x'], new_y)
    
    def write_xy(self, x, y):
        data = np.array([x,y], dtype=np.float64)

        #int32 DAQmxWriteAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
        
        sampsPerChanWritten  = mx.c_int32()
        self.task.WriteAnalogF64(1, True, 0.1, mx.DAQmx_Val_GroupByScanNumber, data, mx.byref(sampsPerChanWritten), None)
        assert sampsPerChanWritten.value == 1
    