'''
Created on Aug 22, 2014

@author: Frank Ogletree
'''
from __future__ import division, print_function
import numpy as np
import PyDAQmx as mx
import logging


logger = logging.getLogger(__name__)

class NamedTask(mx.Task):
    ''' replaces __init__ with one that accepts a name for the task, otherwise identical to PyDaqmx task
        override PyDAQmx definition, which does not support named tasks
        no special chars in names, space OK
    '''
    def __init__(self, name= ''):
        self.taskHandle = mx.TaskHandle(0)
        mx.DAQmxCreateTask(name, mx.byref(self.taskHandle))

class NI_TaskWrap(object):
    '''
    class to wrap National Instruments tasks using DAQmx drivers
    '''
    def __init__(self, name = '' ):
        '''
        Constructor
        '''
        self._error_list = []
        self._channel = self._task_name = self._mode = ''
        self._chan_count = self._rate = 0
        self.make_task( name )
    
    def make_task(self, name = '' ):
        ''' creates a [named] task, should not fail if DAQmx present'''
        # clean up name to remove unallowed characters (might be missing some)
        for char in '/,;':
            name = name.replace(char, "_")
        print("make_task", name)
        self._task_name = name
        try:
            self.task = NamedTask(name)        
        except mx.DAQError as err:
            self.error( err )
            self.task = None               
        
    def error(self, err ):
            self._error_list.append(err)
            logger.error('Error calling "{}": {}'.format( err.fname, err.mess ))

    def stop(self):
        try:
            self.task.StopTask()
        except mx.DAQError as err:
            self.error(err)
        
    def start(self):
        try:
            self.task.StartTask()
        except mx.DAQError as err:
            self.error(err)
    
    def clear(self):
        try:
            self.task.ClearTask()
        except mx.DAQError as err:
            self.error(err)
        finally:
            self.task = None
            
    def close(self):
        return self.clear()
    
    def unreserve(self):
        ''' releases resources for other tasks to use without destroying task'''
        try:
            self.task.TaskControl(mx.DAQmx_Val_Task_Unreserve)
        except mx.DAQError as err:
            self.error(err)
            
    def ready(self):
        ''' validates params, reserves resources, ready to start'''
        try:
            self.task.TaskControl(mx.DAQmx_Val_Task_Commit)
        except mx.DAQError as err:
            self.error(err)
        
    def is_done(self):
        ''' checks for task done'''
        status = mx.bool32(0)
        try:
            self.task.GetTaskComplete( mx.byref(status));
        except mx.DAQError as err:
            self.error(err)
        if status.value:
            return True
        else:
            return False
        
    def get_rate(self):
        return self._rate
    
    def get_chan_count(self):
        return self._chan_count
    
    def wait(self, timeout = 10.0 ):
        try:
            self.task.WaitUntilTaskDone( timeout)
        except mx.DAQError as err:
            self.error(err)        
    
    def get_devices(self):
        '''
        polls for installed NI devices
        '''
        buffSize = 2048
        buff = mx.create_string_buffer( buffSize )
        try:
            mx.DAQmxGetSysDevNames( buff, buffSize );
        except mx.DAQError as err:
            self.error( err )
        dev_list = buff.value.split(',')
        for i in range(len(dev_list)):
            dev_list[i] = dev_list[i].strip()
        self._device_list = dev_list       
        #mx.DAQmxGetDevAIPhysicalChans( AIdev, chanList, buffSize )
    
class NI_AdcTask(NI_TaskWrap):
    '''
    Analog to digital input task, inherits from abstract NI_TaskWrap task
    '''
    def __init__(self, channel, range = 10.0, name = '', terminalConfig='default'  ):
        ''' creates ADC task
        Range [+/- 1, 2, 5, 10]
        terminalConfig in ['default', 'rse', 'nrse', 'diff', 'pdiff']
        '''
        assert terminalConfig in  ('default', 'rse', 'nrse', 'diff', 'pdiff')
        
        NI_TaskWrap.__init__(self, name)
        
        self.terminalConfig = terminalConfig
        self._terminalConfig_enum = dict(
              default = mx.DAQmx_Val_Cfg_Default, 
              rse = mx.DAQmx_Val_RSE,
              nrse = mx.DAQmx_Val_NRSE,
              diff = mx.DAQmx_Val_Diff,
              pdiff = mx.DAQmx_Val_PseudoDiff,
              )[self.terminalConfig]

        if self.task:
            self.set_channel(channel, range)
            
        self.done_callback_is_set = False
            
    def set_channel(self, channel, adc_range = 10.0):
        ''' adds input channel[s] to existing task, tries voltage range +/- 1, 2, 5, 10'''
        #  could use GetTaskDevices followed by GetDevAIVoltageRngs to validate max volts
        #  also can check for simultaneous, max single, max multi rates
        self._channel = channel
        self._input_range = min( abs(adc_range), 10.0 ) #error if range exceeds device maximum
        self._sample_count = 0
        adc_max = mx.float64(  self._input_range )
        adc_min = mx.float64( -self._input_range )


        try:                
            #int32 CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], 
            #    int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
            self.task.CreateAIVoltageChan(self._channel, '', self._terminalConfig_enum,
                                          adc_min, adc_max, mx.DAQmx_Val_Volts, '')            
            chan_count = mx.uInt32(0) 
            self.task.GetTaskNumChans(mx.byref(chan_count))
            self._chan_count = chan_count.value
            self._mode = 'single'   #until buffer created
        except mx.DAQError as err:
            self._chan_count = 0
            self.error(err)
            
    def set_rate(self, rate = 1e4, count = 1000, finite = True, clk_source=""):
        """
        Input buffer
            In continuous mode, count determines per-channel buffer size only if
                count EXCEEDS default buffer (1 MS over 1 MHz, 100 kS over 10 kHz, 10 kS over 100 Hz, 1 kS <= 100 Hz
                unless buffer explicitly set by DAQmxCfgInputBuffer()

            In finite mode, buffer size determined by count
         """
        if finite:
            adc_mode = mx.int32(mx.DAQmx_Val_FiniteSamps)
        else:
            adc_mode = mx.int32(mx.DAQmx_Val_ContSamps)
        adc_rate = mx.float64(rate)   #override python type
        adc_count = mx.uInt64(int(count))
        
        self.stop() #make sure task not running, 
        
        #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
        #                        int32 sampleMode, uInt64 sampsPerChan );
        #  default clk_source (clock source) is subsystem acquisition clock (OnboardClock)
        # adc_rate: The sampling rate in samples per second per channel. 
        #             If you use an external source for the Sample Clock, set this value to the maximum expected rate of that clock.  
        try:                 
            self.task.CfgSampClkTiming(clk_source, adc_rate, mx.DAQmx_Val_Rising, adc_mode, adc_count) 
            adc_rate = mx.float64(0)
            #exact rate depends on hardware timer properties, may be slightly different from requested rate
            self.task.GetSampClkRate(mx.byref(adc_rate));
            self._rate = adc_rate.value
            self._count = int(count)
            self._mode = 'buffered'
        except mx.DAQError as err:
            self.error(err)
            self._rate = 0
    
    def set_n_sample_callback(self, n_samples, cb_func):
        """
        Setup callback functions for EveryNSamplesEvent
        *cb_func* will be called with when new data is available
        after every *n_samples* are acquired.
        """
        self.cb_nSamples = n_samples
        self.cb_func = cb_func
        self.task.EveryNCallback = cb_func
        self.task.AutoRegisterEveryNSamplesEvent(
            everyNsamplesEventType=mx.DAQmx_Val_Acquired_Into_Buffer, 
            nSamples=self.cb_nSamples,
            options=0)


        
        
    def set_done_callback(self, done_func):
        'done_func takes one argument (status)'
        self.cb_done_func =  done_func
        self.task.DoneCallback= self.cb_done_func
        if not self.done_callback_is_set:
            self.task.AutoRegisterDoneEvent(options=0)
            self.done_callback_is_set = True

    """def EveryNCallback(self):
        self.data_buffer=self.read_buffer(self.cb_nSamples, timeout=1.0)
        self.cb_func(self.data_buffer)
        return 0 # The function should return an integer
    
    def DoneCallback(self, status):
        self.data_buffer=self.read_buffer(0, timeout=1.0)
        print('done_callback finaldata', self.data_buffer.shape)
        self.cb_func(self.data_buffer)
        self.cb_done_func()
        #print "Status",status.value
        return 0 # The function should return an integer
    """
  
    def set_single(self):
        ''' single-value [multi channel] input, no clock or buffer
                   
            For unbuffered input (one sample per channel no timing or clock),
            if task STARTed BEFORE reading, in tight loop overhead between consecutive reads ~ 36 us with some jitter
                task remains in RUN, must be STOPed or cleared to modify
            if task is COMMITted  before reading, overhead ~ 116 us 
                (implicit transition back to COMMIT instead of staying in RUNNING)
            if task is STOPed before reading, requiring START read STOP overhead 4 ms
         '''
        if self._mode != 'single':
            self.clear()    #delete old task
            self.make_task(self._task_name)
            self.set_channel(self._channel, self._input_range)
            self._mode = 'single'
            
    def get(self):
        ''' reads one sample per channel in immediate (non buffered) mode, fastest if task pre-started'''
        data = np.zeros(self._chan_count, dtype = np.float64 )
        if self._mode != 'single':
            self.set_single()
            self.start()
        read_size = mx.uInt32(self._chan_count)
        read_count = mx.int32(0)
        timeout = mx.float64( 1.0 )
        try:
            # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
            #    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
            self.task.ReadAnalogF64(1, timeout, mx.DAQmx_Val_GroupByScanNumber, 
                                  data, read_size, mx.byref(read_count), None)
        except mx.DAQError as err:
            self.error(err)
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
        assert read_count.value == 1, \
            "sample count {} transfer count {}".format( 1, read_count.value )
        return data
              
    def read_buffer(self, count = 0, timeout = 0):
        ''' reads block of input data, defaults to block size from set_rate()
            for now allocates data buffer, possible performance hit
            in continuous mode, reads all samples available up to block_size
            in finite mode, waits for samples to be available, up to smaller of block_size or
                _chan_cout * _count
                
            for now return interspersed array, latter may reshape into 
        '''
        count = int(count)
        if count == 0:
            count = self._count
        block_size = count * self._chan_count
        data = np.zeros(block_size, dtype = np.float64)
        read_size = mx.uInt32(block_size)
        read_count = mx.int32(0)    #returns samples per chan read
        adc_timeout = mx.float64( timeout )
        try:
            # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
            #    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
            self.task.ReadAnalogF64(-1, adc_timeout, mx.DAQmx_Val_GroupByScanNumber, 
                                  data, read_size, mx.byref(read_count), None)
        except mx.DAQError as err:
            self.error(err)
            #not sure how to handle actual samples read, resize array??
        if read_count.value < count:
            pass
            #logger.warning( 'requested {} values for {} channels, only {} read'.format( count, self._chan_count, read_count.value) )
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
#        assert read_count.value == 1, \
#           "sample count {} transfer count {}".format( 1, read_count.value )
        return data
            
class NI_DacTask(NI_TaskWrap):
    '''
    Digital-to-Analog output task, inherits from abstract NI_TaskWrap task
    '''
    def __init__(self, channel, name = '' ):
        ''' creates DAC task'''
        NI_TaskWrap.__init__(self, name)       
        if self.task:
            self.set_channel(channel)
            
    def set_channel(self, channel ):
        ''' adds output channel[s] to existing task, always voltage range +/- 10 no scaling'''
        self._channel = channel
        self._sample_count = 0
        try:                
            # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
            #    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
            self.task.CreateAOVoltageChan(self._channel, '', -10.0, +10.0, mx.DAQmx_Val_Volts, '')
            
            chan_count = mx.uInt32(0) 
            self.task.GetTaskNumChans(mx.byref(chan_count))
            self._chan_count = chan_count.value
            self._mode = 'single'   #until buffer created
        except mx.DAQError as err:
            self._chan_count = 0
            self.error(err)
            
    def set_rate(self, rate = 1e4, count = 1000, finite = True, clk_source=""):
        """
        Output buffer size determined by amount of data written, unless explicitly set by DAQmxCfgOutputBuffer()
        
        In Finite output mode, count is samples per channel to transfer on Start()
               if count > buffer size, output loops over buffer
               if count < buffer size, partial output, next start resumes from this point in buffer
        waiting for finite task to complete then restarting task has > 1 ms overhead, unclear why,
            overhead can fluctuate by 1.00 ms amounts. stupid old c clock??
        
        In Cont output mode, count is not used, output loops over buffer until stopped
            restarts at beginning of buffer
            stop/restart also has 2 ms overhead

        For unbuffered output (one sample per channel no timing or clock) with autostart enabled,
            if task STARTed BEFORE writing, in tight loop overhead between consecutive writes 18 us with some jitter
            if task is COMMITted  before writing, overhead 40 us 
                (implicit transition back to COMMIT instead of staying in RUNNING)
         """
        if finite:
            dac_mode = mx.int32(mx.DAQmx_Val_FiniteSamps)
        else:
            dac_mode = mx.int32(mx.DAQmx_Val_ContSamps)
        #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
        #                        int32 sampleMode, uInt64 sampsPerChan );
        #  default clock source is subsystem acquisition clock
        try:                 
            dac_rate = mx.float64(rate)   #override python type
            dac_count = mx.uInt64(int(count))
            self.stop() #make sure task not running, 
            self.task.CfgSampClkTiming(clk_source, dac_rate, mx.DAQmx_Val_Rising, dac_mode, dac_count) 
            dac_rate = mx.float64(0)
            #exact rate depends on hardware timer properties, may be slightly different from requested rate
            self.task.GetSampClkRate(mx.byref(dac_rate));
            self._rate = dac_rate.value
            self._mode = 'buffered'
        except mx.DAQError as err:
            self.error(err)
            self._rate = 0
    
    def set_callback(self,source):
        self.data_buffer=np.zeros(self._count)
        self.task.EveryNCallback=self.EveryNCallback
        self.task.DoneCallback=self.DoneCallback
        self.task.AutoRegisterEveryNSamplesEvent(mx.DAQmx_Val_Transferred_From_Buffer,self._count,0)
        self.task.AutoRegisterDoneEvent(0)
        self._source=source
    
    def set_single(self):
        ''' single-value [multi channel] output, no clock or buffer
        
        For unbuffered output (one sample per channel no timing or clock) with autostart enabled,
            if task STARTed BEFORE writing, in tight loop overhead between consecutive writes 21 us with some jitter
                (no implicit mode transition)
            if task is COMMITted  before writing, overhead 40 us 
                (implicit transition back to COMMIT instead of staying in RUNNING)
            if task stopped, autostart takes ~ 5 ms per write
                (implicit start stop)
                
        No clean way to change from buffered to single point output without creating new task
         '''
        if self._mode != 'single':
            self.clear()    #delete old task
            self.make_task(self._task_name)
            self.set_channel(self._channel)
            self._mode = 'single'
              
    def load_buffer(self, data, auto = False ):
        '''  writes data to output buffer, array-like objects converted to np arrays if required
            data is interleved, i.e. x1, y1, x2, y2, x3, y3... for output on x and y
            implicitly COMMITs task, also starts if autostart is True
        '''
        if not isinstance( data, np.ndarray ) or data.dtype != np.float64:
            data = np.asarray(data, dtype = np.float64 )
        dac_samples = mx.int32( int(len(data) / self._chan_count) )
        self._sample_count = dac_samples.value
        writeCount = mx.int32(0)
        if auto:
            auto_start = mx.bool32(1)
        else:
            auto_start = mx.bool32(0)       
        try:
            #  WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, 
            #    bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)
            #self.task.SetWriteRelativeTo(mx.DAQmx_Val_FirstSample)
            self.task.WriteAnalogF64(dac_samples, auto_start, 1.0, mx.DAQmx_Val_GroupByScanNumber, 
                                  data, mx.byref(writeCount), None)
        except mx.DAQError as err:
            self.error(err)
        #print "samples {} written {}".format( self._sample_count, writeCount.value)
        if writeCount.value != self._sample_count:
            "sample load count {} transfer count {}".format( self._sample_count, writeCount.value )

    def set(self, data):
        ''' writes one sample per channel in immediate (non buffered) mode, fastest if task pre-started'''
        if not isinstance( data, np.ndarray ) or data.dtype != np.float64:
            data = np.asarray(data, dtype = np.float64 )
        if self._mode != 'single':
            self.set_single()
            self.start()
        writeCount = mx.int32(0)
        auto_start = mx.bool32(1)
        try:
            #  WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, 
            #    bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)
            self.task.WriteAnalogF64(1, auto_start, 1.0, mx.DAQmx_Val_GroupByChannel, 
                                  data, mx.byref(writeCount), None)
        except mx.DAQError as err:
            self.error(err)
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
        assert writeCount.value == 1, \
            "sample count {} transfer count {}".format( 1, writeCount.value )

    def EveryNCallback(self):
        #np.copyto(self.data_buffer,self._source,None)
        self.load_buffer(self.data_buffer)
        return 0 # The function should return an integer
    
    def DoneCallback(self, status):
        #print "Status",status.value
        return 0 # The function should return an integer

class NI_CounterTask( NI_TaskWrap ):
    '''
    Event counting input task, inherits from abstract NI_TaskWrap task
    '''
    def __init__(self, channel, input_terminal='PFI0', name = ''  ):
        ''' creates Counter task, default channel names ctr0, ctr1...
            uses input 'PFI0' by default
        '''
        NI_TaskWrap.__init__(self, name)
        

        if self.task:
            self.set_channel(channel, input_terminal)
        else:
            raise IOError("NI_CounterTask failed to create counter task")
            
    def set_channel(self, channel, input_terminal = 'PFI0' ):
        ''' adds input channel[s] to existing task'''
        logger.debug("NI_CounterTask.set_channel-- {} {}".format(channel, input_terminal))
        #  could use GetTaskDevices followed by GetDevAIVoltageRngs to validate max volts
        #  also can check for simultaneous, max single, max multi rates            
        self._channel = channel
        #self._sample_count = 0
        self._input_terminal = input_terminal

        try:                
            #int32 DAQmxCreateCICountEdgesChan (TaskHandle taskHandle, const char counter[], 
            #    const char nameToAssignToChannel[], int32 edge, uInt32 initialCount, int32 countDirection);
            self.task.CreateCICountEdgesChan(self._channel, '', mx.DAQmx_Val_Rising, 0, mx.DAQmx_Val_CountUp )
            self.task.SetCICountEdgesTerm( self._channel, self._input_terminal)
        except mx.DAQError as err:
            #self._chan_count = 0
            self.error(err)
            
    def set_rate(self, rate = 1e4, count = 1000,  clk_source = 'ao/SampleClock', finite = True):
        """
        NOTE analog output and input clocks are ONLY available when NI_DacTask or NI_AdcTask task are running. This
        is OK for simultaneous acquisition. Otherwise use dummy task or use another ctr as a clock. If the 
        analog task completes before the counter task, the sample trigger will no longer arrive
        
        Input buffer
            Uses analog output clock for now, may conflict with DAC tasks
            In continuous mode, count determines per-channel buffer size only if
                count EXCEEDS default buffer (1 MS over 1 MHz, 100 kS over 10 kHz, 10 kS over 100 Hz, 1 kS <= 100 Hz
                unless buffer explicitly set by DAQmxCfgInputBuffer()
    
            In finite mode, buffer size determined by count
        """
        if finite:
            ctr_mode = mx.int32(mx.DAQmx_Val_FiniteSamps)
        else:
            ctr_mode = mx.int32(mx.DAQmx_Val_ContSamps)
        ctr_rate = mx.float64(rate)   #override python type
        ctr_count = mx.uInt64(int(count))
        self._clock_source = clk_source
        
        self.stop() #make sure task not running, 
        #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
        #                        int32 sampleMode, uInt64 sampsPerChan );
        #  default clock source is subsystem acquisition clock
        try:                 
            self.task.CfgSampClkTiming(clk_source, ctr_rate, mx.DAQmx_Val_Rising, ctr_mode, ctr_count) 
            #exact rate depends on hardware timer properties, may be slightly different from requested rate
            ctr_rate.value = 0
            self.task.GetSampClkRate(mx.byref(ctr_rate));
            self._rate = ctr_rate.value
            self._count = count
            #self._mode = 'buffered'
        except mx.DAQError as err:
            self.error(err)
            self._rate = 0
    
    def start(self):
        self.prev_count = 0
        NI_TaskWrap.start(self)
        
    def set_n_sample_callback(self, n_samples, cb_func):
        """
        Setup callback functions for EveryNSamplesEvent
        *cb_func* will be called with when new data is available
        after every *n_samples* are acquired.
        """
        self.cb_nSamples = n_samples
        self.cb_func = cb_func
        self.task.EveryNCallback = cb_func
        self.task.AutoRegisterEveryNSamplesEvent(
            everyNsamplesEventType=mx.DAQmx_Val_Acquired_Into_Buffer, 
            nSamples=self.cb_nSamples,
            options=0)


### copied for ADC, probably irrelevant for counter              
#     def set_single(self):
#         ''' single-value [multi channel] input, no clock or buffer
#                    
#             For unbuffered input (one sample per channel no timing or clock),
#             if task STARTed BEFORE reading, in tight loop overhead between consecutive reads ~ 36 us with some jitter
#                 task remains in RUN, must be STOPed or cleared to modify
#             if task is COMMITted  before reading, overhead ~ 116 us 
#                 (implicit transition back to COMMIT instead of staying in RUNNING)
#             if task is STOPed before reading, requiring START read STOP overhead 4 ms
#          '''
#         if self._mode != 'single':
#             self.clear()    #delete old task
#             self.make_task(self._task_name)
#             self.set_channel(self._channel, self._input_terminal)
#             self._mode = 'single'

### copied for ADC, probably irrelevant for counter            
#     def get(self):
#         ''' reads one sample per channel in immediate (non buffered) mode, fastest if task pre-started
#             works rather well for count rates when combined with python time.clock()
#         '''
#         data = np.zeros(1, dtype = np.float64 )
#         data = mx.float64(0)
#         if self._mode != 'single':
#             self.set_single()
#             self.start()
#         read_size = mx.uInt32(self._chan_count)
#         timeout = mx.float64( 1.0 )
#         try:
#             # int32 DAQmxReadCounterScalarF64 (TaskHandle taskHandle, float64 timeout, 
#             #    float64 *value, bool32 *reserved);
#             self.task.ReadCounterScalarF64(timeout, mx.byref(data), None )
# 
#         except mx.DAQError as err:
#             self.error(err)
#         return data.value
    
    def read_buffer(self, count = 0, timeout = 0):
        ''' reads block of input data, defaults to block size from set_rate()
            for now allocates data buffer, possible performance hit
            in continuous mode, reads all samples available up to block_size
            in finite mode, waits for samples to be available, up to smaller of block_size or
                _chan_cout * _count
            
            returns data
        '''
        if count == 0:
            count = self._count
        data = np.zeros(count, dtype = np.float64)
        read_count = mx.int32(0)    #returns samples per chan read
        try:
            # int32 DAQmxReadCounterF64 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, 
            #    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
            self.task.ReadCounterF64(-1, timeout, data, count, mx.byref(read_count), None)
        except mx.DAQError as err:
            self.error(err)
            #not sure how to handle actual samples read, resize array??
        if read_count.value < count:
            logger.warn('NI_CounterTask: requested {} values for {} channels, only {} read'.format( count, self._chan_count, read_count.value))
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
#        assert read_count.value == 1, \
#           "sample count {} transfer count {}".format( 1, read_count.value )
        return data[0:read_count.value]
    
    def read_diff_buffer(self, count = 0, timeout = 0):
        data_block = self.read_buffer(count, timeout)
        x=np.insert(data_block,0,self.prev_count)
        x=np.diff(x)
        self.prev_count = data_block[-1]
        return x

class NI_SyncTaskSet(object):
    '''
    creates simultaneous input (ADC, counter) and output (DAC) tasks with 
    synchronized start triggers
    input and output task elapsed time need not be equal, but typically will be, 
    can oversample input with for example 10x rate, 10x sample count
    '''
    def __init__(self, out_chan, in_chan,ctr_chans, ctr_terms, vin_range = 10.0, 
                terminalConfig='default', clock_source = "", trigger_output_term=None ):
    
        # create input and output tasks
        self.dac = NI_DacTask( out_chan, name='SyncTaskSet_DAC')        
        self.adc = NI_AdcTask( in_chan, vin_range, 'SyncTaskSet_ADC', terminalConfig )
        self.ctr_chans=ctr_chans
        self.ctr_terms=ctr_terms
        self.num_ctrs=len(self.ctr_chans)
        self.ctrs=[]

        for i in range(self.num_ctrs):
            self.ctrs.append(NI_CounterTask(ctr_chans[i],ctr_terms[i],
                                            name='ctr_{}_{}'.format(ctr_chans[i], ctr_terms[i])))
        
        # if a clock_source is defined, use it to clock the ADC, 
        # otherwise internally clock ADC, rate set during setup()
        self.clock_source = clock_source
        if self.clock_source:
            logger.debug( "setup clock_source" + repr( self.clock_source) )
            self.adc.task.CfgDigEdgeStartTrig(clock_source, mx.DAQmx_Val_Rising)

        # Sync DAC StartTrigger on ADC StartTigger
        buffSize = 512
        buff = mx.create_string_buffer( buffSize )
        self.adc.task.GetNthTaskDevice(1, buff, buffSize)    #DAQmx name for input device
        dac_trig_name = b'/' + buff.value + b'/ai/StartTrigger'
        self.dac.task.CfgDigEdgeStartTrig(dac_trig_name, mx.DAQmx_Val_Rising)


        # Route DAC SampleClock signal to trigger_output_term
        # This allows you to trigger other devices simultaneously with DAC output
        self.trigger_output_term = trigger_output_term
        if self.trigger_output_term:
            self.dac.task.ExportSignal(mx.DAQmx_Val_SampleClock, self.trigger_output_term)
            #self.adc.task.SetDOTristate(trigger_output_term, False)
            
            ## For debugging, send trigger to another pin
            #mx.DAQmxConnectTerms(trigger_output_term, b"/X-6368/PFI12", mx.DAQmx_Val_DoNotInvertPolarity )
            
    def setup(self, rate_out, count_out, rate_in, count_in, is_finite=True):
        """
        Set the i/o rates and size of buffers
        
        *rate_out*: DAC rate (Hz), counters are also clocked at this rate
        *rate_in*: ADC rate (Hz)
        
        *is_finite* defines if single shot or continuous
        
        ADC, Counters lag DAC, 
        ADC reads voltage while DAC is starting to move to voltage
        therefore removing extra values, from ADC, counters may be necessary to align writes/reads
        """
        # Pad removed 2017-02-23 ESB + DFO
        #        *Pad* if true, acquire one extra input value per channel, 
        #        strip off the first read, so writes/reads align
        # if pad:
        #      self.delta = int(np.rint(rate_in / rate_out))
        # else:
        #     self.delta = 0
        
        if rate_in % rate_out > 0:
            logger.warn("NI_SyncTaskSet: rate_in/rate_out is not an integer, funny oversampling will occur")

        self.dac.set_rate(rate_out, count_out, finite=is_finite, clk_source=self.clock_source)
        self.adc.set_rate(rate_in,  count_in  ,finite=is_finite, clk_source=self.clock_source)
        for i in range(self.num_ctrs):
            self.ctrs[i].set_rate(rate_in,count_in,
                                  clk_source='ao/SampleClock',finite=is_finite)
            
        
    def write_output_data_to_buffer(self, data):
        self.dac.load_buffer(data)
    
    def start(self):
        for i in range(self.num_ctrs):
            self.ctrs[i].start()
        self.dac.start() #start dac first, waits for trigger from ADC to output data
        self.adc.start()
        
       
    def read_adc_buffer(self, count=0, timeout = 1.0):
        x = self.adc.read_buffer(count=count, timeout=timeout)
        #return x[self.delta*self.adc.get_chan_count()::]
        # Changed 2/10/17: don't remove delta -- works for sync scan,this may break other things!
        return x
    
    def get_adc_chan_count(self):
        return self.adc.get_chan_count()
    
    def read_adc_buffer_reshaped(self, count=0, timeout = 1.0):
        return self.read_adc_buffer(count=count, timeout=timeout).reshape(-1, self.get_adc_chan_count()) 
    
    def read_ctr_buffer(self, ctr_i, count=0, timeout=0):
        """Reads the counter ctr_i buffer up to count,
        if count=0 (default) read up to block_size"""
        x = self.ctrs[ctr_i].read_buffer(count, timeout)
        return x
    
    def read_ctr_buffer_diff(self, ctr_i, count=0, timeout = 0):
        return self.ctrs[ctr_i].read_diff_buffer(count, timeout)
    
    def stop(self):
        logger.debug('dac.task {}'.format( self.dac.task ))
        logger.debug('adc.task {}'.format( self.adc.task ))
        self.dac.stop() 
        self.adc.stop()
        for i in range(self.num_ctrs):
            self.ctrs[i].stop()
        
    def close(self):
        self.dac.close()
        self.adc.close()
        for i in range(self.num_ctrs):
            self.ctrs[i].close()
            
