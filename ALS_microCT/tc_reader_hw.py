from ScopeFoundry.hardware import HardwareComponent
import PyDAQmx as mx
import numpy as np
import time

class TcReaderHW(HardwareComponent):
    """
    using a NI 9211 CDAQ TC reader
    Configured as K-type thermocouple reader
    """
    
    name = 'tc_reader'
    
    def setup(self):
        self.settings.New('channel', dtype=str, initial='cDAQ1Mod1/ai0')
        self.settings.New('temp0', dtype=float, unit='C')
    
    
    def connect(self):
        
        """int32 DAQmxCreateAIThrmcplChan (TaskHandle taskHandle, 
            const char physicalChannel[], const char nameToAssignToChannel[],
            float64 minVal, float64 maxVal, int32 units, 
            int32 thermocoupleType,
            int32 cjcSource, float64 cjcVal, const char cjcChannel[]);
        """
        
        # Create Task
        self.task = mx.Task()
        
        chan = self.settings['channel']
        self.task.CreateAIThrmcplChan(chan, '',
                                 -200, 1200,mx.DAQmx_Val_DegC,
                                 mx.DAQmx_Val_K_Type_TC,
                                 mx.DAQmx_Val_BuiltIn , 0, '' )

        
        chan_count = mx.uInt32(0) 
        self.task.GetTaskNumChans(mx.byref(chan_count))
        self._chan_count = chan_count.value
        # Set single

        # start
        self.task.StartTask()
        
        
        #connect settings to hardware
        self.settings.temp0.connect_to_hardware(
                                read_func=self.read_single)

        self.read_from_hardware()
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'task'):
            self.task.StopTask()
            del self.task
        
        
    def read_single(self):
        t0 = time.time()
        data = np.zeros(self._chan_count, dtype = np.float64 )

        read_size = self._chan_count
        read_count = mx.int32(0)
        timeout = 1.0
        """ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
                float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
        """
        self.task.ReadAnalogF64(1, timeout, mx.DAQmx_Val_GroupByScanNumber, 
                      data, read_size, mx.byref(read_count), None)

        assert read_count.value == 1, \
            "sample count {} transfer count {}".format( 1, read_count.value )

        print(self.name + " read_single dt=", time.time() - t0 )
        return data
        
        