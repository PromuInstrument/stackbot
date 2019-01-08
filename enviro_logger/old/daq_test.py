import PyDAQmx as mx
import numpy as np

task = mx.Task()

# task.CreateAIVoltageChan("/Dev2/ai0:3", '',
#                          mx.DAQmx_Val_PseudoDiff,
#                          -5,+5, mx.DAQmx_Val_Volts, '')


#int32 DAQmxCreateAIAccelChan (TaskHandle taskHandle, 
# const char physicalChannel[], const char nameToAssignToChannel[],
# int32 terminalConfig, float64 minVal, float64 maxVal, int32 units,
# float64 sensitivity, int32 sensitivityUnits, int32 currentExcitSource,
# float64 currentExcitVal, const char customScaleName[]);
task.CreateAIAccelChan("/Dev2/ai3", '',
                         mx.DAQmx_Val_PseudoDiff,
                         -10.121457 , +10.121457, mx.DAQmx_Val_AccelUnit_g, 
                         0.494,#494mV/g
                         mx.DAQmx_Val_VoltsPerG,
                         mx.DAQmx_Val_Internal, 0.002, '')





chan_count = mx.uInt32(0) 
task.GetTaskNumChans(mx.byref(chan_count))
n_chans = chan_count.value

#  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
#                        int32 sampleMode, uInt64 sampsPerChan );
#  default clk_source (clock source) is subsystem acquisition clock (OnboardClock)
# adc_rate: The sampling rate in samples per second per channel. 
#             If you use an external source for the Sample Clock, set this value to the maximum expected rate of that clock.  

n_samples = 1000
rate = 50000

# task.CfgSampClkTiming("", 1e3, mx.DAQmx_Val_Rising,
#                            mx.DAQmx_Val_FiniteSamps, n_samples)
task.CfgSampClkTiming("", rate, mx.DAQmx_Val_Rising,
                           mx.DAQmx_Val_ContSamps, n_samples)


task.StartTask()
 
# ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
#    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
data = np.zeros(n_chans * n_samples, dtype = np.float64)

for i in range(10):
    read_count = mx.int32(0)    #returns samples per chan read
    task.ReadAnalogF64(n_samples, 1.0, mx.DAQmx_Val_GroupByScanNumber,  data, len(data), mx.byref(read_count), None)

    print('read', read_count.value)
    print(data.mean())#, data)

print("done")