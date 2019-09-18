import PyDAQmx as mx
import numpy as np
import time

### Timing
"""
Fastest clock is the digital clock at 10MHz for X-series,
We can use this as the trigger basis for sync scans

or maybe the 100MHz time base

"""


do_chan = "/X-6368/port0/line0:3"
di_chan = "/X-6368/port0/line4:7"
ao_chan = "/X-6368/ao0:1"
ai_chan = "/X-6368/ai0:1"
ctr_chan = "/X-6368/ctr0,/Dev1/ctr1"

do_rate = int(10e6)
di_rate = do_rate
ao_rate = do_rate/20
ai_rate = ao_rate
ctr_rate = do_rate

chunk_time = 0.050 # seconds

#N_do = int(1e6)
N_do = int(do_rate*chunk_time)
N_di = int(N_do*(di_rate/do_rate))
N_ao = int(N_do*(ao_rate/do_rate))
N_ai = int(N_do*(ai_rate/do_rate))
print (N_do, N_di, N_ao, N_ai)

i_do = 0
i_di = 0
i_ao = 0
i_ai = 0


ao_data_x = np.sin(np.linspace(0,2*np.pi,N_ao))
ao_data_y = np.cos(np.linspace(0,2*np.pi,N_ao))
do_data = np.zeros(N_do, dtype=np.uint32)
do_data[::2] = 0b0001
do_data[::3] = 0b0010
do_data[::4] = 0b0100
do_data[::5] = 0b1000

def interleave_xy_arrays(X, Y):
    """take 1D X and Y arrays to create a flat interleaved XY array
    of the form [x0, y0, x1, y1, .... xN, yN]
    """
    assert len(X) == len(Y)
    N = len(X)
    XY = np.zeros(2*N, dtype=float)
    XY[0::2] = X
    XY[1::2] = Y
    return XY     

ao_data = interleave_xy_arrays(ao_data_x, ao_data_y) 

### Create Tasks


# Digital Out
do_task = mx.Task()
#int32 DAQmxCreateDOChan (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
do_task.CreateDOChan(do_chan, '', mx.DAQmx_Val_ChanForAllLines)
do_task.CfgSampClkTiming(None, do_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*N_do)

chan_count = mx.uInt32(0) 
do_task.GetTaskNumChans(mx.byref(chan_count))
print('do_task chan count:', chan_count.value)

# Digital In
di_task = mx.Task()
#int32 DAQmxCreateDIChan (TaskHandle taskHandle, const char lines[],
#    const char nameToAssignToLines[], int32 lineGrouping);
di_task.CreateDIChan(di_chan, '', mx.DAQmx_Val_ChanForAllLines)
di_task.CfgSampClkTiming(None, di_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*N_di)

di_task.GetTaskNumChans(mx.byref(chan_count))
di_n_chans = chan_count.value

# Analog Out
ao_task = mx.Task()
# CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
#    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
ao_task.CreateAOVoltageChan(ao_chan, '', -10.0, +10.0, mx.DAQmx_Val_Volts, '')
#int32 DAQmxCfgSampClkTiming (TaskHandle taskHandle, const char source[], 
#    float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChanToAcquire);
ao_task.CfgSampClkTiming("", ao_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*N_ao) 

#allow regen lets DAQ loop over scan buffer, do before task starts
#callbacks optionally dynamically update buffer for drift
#mx.DAQmxSetWriteRegenMode(ao_task.taskHandle, mx.DAQmx_Val_AllowRegen)


chan_count = mx.uInt32(0) 
ao_task.GetTaskNumChans(mx.byref(chan_count))
print('ao_task chan count:', chan_count.value)


# Analog In
ai_task = mx.Task()
#int32 CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], 
#    int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
ai_task.CreateAIVoltageChan(ai_chan, '', mx.DAQmx_Val_Diff, -10.0, +10.0, mx.DAQmx_Val_Volts,'')
ai_task.CfgSampClkTiming("", ai_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*N_ai) 

ai_task.GetTaskNumChans(mx.byref(chan_count))
ai_n_chans = chan_count.value



# Counter In

# self.task.CreateCICountEdgesChan(self._channel, '', mx.DAQmx_Val_Rising, 0, mx.DAQmx_Val_CountUp )
# self.task.SetCICountEdgesTerm( self._channel, self._input_terminal)
# self.task.CfgSampClkTiming(clk_source, ctr_rate, mx.DAQmx_Val_Rising, ctr_mode, ctr_count) 



### Setup synchronous timing

# Sync DAC StartTrigger on ADC StartTigger
start_trig_name = '/X-6368/do/StartTrigger'
#start_trig_name = b'/Dev1/ai/StartTrigger'
#di_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)
di_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)
ao_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)
ai_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)

### Set up callbacks

def set_n_sample_callback(task, n_samples, cb_func, io='in'):
    """
    Setup callback functions for EveryNSamplesEvent
    *cb_func* will be called with when new data is available
    after every *n_samples* are acquired.
    
    cb_func should return 0 on completion
    """
    if io == 'in':
        event_type = mx.DAQmx_Val_Acquired_Into_Buffer        
    elif io == 'out':
        event_type = mx.DAQmx_Val_Transferred_From_Buffer
    
    print(n_samples)
    task.EveryNCallback = cb_func
    task.AutoRegisterEveryNSamplesEvent(
        everyNsamplesEventType=event_type, 
        nSamples=n_samples,
        options=0)
# or

"""def DoneCallback_py(taskHandle, status, callbackData):
    print "Status",status.value
    return 0 # The function should return an integer
    
def set_n_sample_callback(task, n_samples, cb_func):
    # Convert the python function to a C function callback
    cb_func_ptr = mx.DAQmxEveryNSamplesEventCallbackPtr(cb_func)
    # int32 DAQmxRegisterEveryNSamplesEvent (TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, uInt32 options, DAQmxEveryNSamplesEventCallbackPtr callbackFunction, void *callbackData);
    mx.DAQmxRegisterEveryNSamplesEvent(task.taskHandle, mx.DAQmx_Val_Acquired_Into_Buffer, n_samples, 0, cb_func_ptr, None)
"""
def on_do_callback():
    print('do callback')

    # load data in to output buffer
    writeCount = mx.int32(0)
    do_task.WriteDigitalU32(N_do, False, N_di/di_rate, mx.DAQmx_Val_GroupByScanNumber,
                            do_data, mx.byref(writeCount), None)
    global i_do
    print('do callback', i_do, writeCount.value)
    i_do += N_do
    return 0
set_n_sample_callback(do_task, N_do, on_do_callback, 'out')


def on_ao_callback():
    # load data in to output buffer
    writeCount = mx.int32(0)
    ao_task.WriteAnalogF64(N_ao, False, N_ao/ao_rate, mx.DAQmx_Val_GroupByScanNumber, 
                          ao_data, mx.byref(writeCount), None)
    global i_ao
    print('ao callback', i_ao, writeCount.value)
    i_ao += N_ao
    return 0
set_n_sample_callback(ao_task, N_ao, on_ao_callback, 'out')
    

def on_ai_callback():
    
    data = np.zeros(N_ai*ai_n_chans, dtype = np.float64)
    read_size = mx.uInt32(N_ai*ai_n_chans)
    read_count = mx.int32(0)    #returns samples per chan read
        
    #int32 DAQmxReadAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, 
    #    bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
    ai_task.ReadAnalogF64(N_ai, 0,mx.DAQmx_Val_GroupByScanNumber,data, read_size, mx.byref(read_count), None)

    global i_ai
    print('on ai callback', i_ai ,data.mean())
    i_ai += N_ai
    return 0
set_n_sample_callback(ai_task, N_ai, on_ai_callback, 'in')


def on_di_callback():
    data = np.zeros(N_di*di_n_chans, dtype=np.uint32)
    read_size = N_di*di_n_chans
    read_count = mx.int32(0)    #returns samples per chan read
    # int32 DAQmxReadDigitalU32 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout,
    #    bool32 fillMode, uInt32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
    di_task.ReadDigitalU32(N_di, 0, mx.DAQmx_Val_GroupByScanNumber, data, read_size, mx.byref(read_count), None)

    global i_di
    print('on di callback', i_di, data)
    i_di += N_di
    return 0
set_n_sample_callback(di_task, N_di, on_di_callback, 'in')

### load buffers

di_task.StartTask()
ai_task.StartTask()


# Analog Out

#  WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, 
#    bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)
# writeCount = mx.int32(0)
# ao_task.WriteAnalogF64(4*N_ao, False, 0.0, mx.DAQmx_Val_GroupByScanNumber, 
#                           np.concatenate(4*[np.zeros_like(ao_data),], axis=0),
#                           mx.byref(writeCount), None)
ao_task.CfgOutputBuffer(4*N_ao)
for i in range(4):
    on_ao_callback()

# Digital Out
#int32 DAQmxWriteDigitalLines (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout,
#    bool32 dataLayout, uInt8 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
#int32 DAQmxWriteDigitalU8 (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout,
#    bool32 dataLayout, uInt8 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
#writeCount = mx.int32(0)
#do_task.WriteDigitalU32(N_do, False, 0, mx.DAQmx_Val_GroupByScanNumber,
#                          do_data, mx.byref(writeCount), None)
do_task.CfgOutputBuffer(4*N_do)
for i in range(4):
    on_do_callback()


ao_task.StartTask()
do_task.StartTask()

while True:
    time.sleep(1.0)

