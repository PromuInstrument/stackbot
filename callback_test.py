'''
Created on Mar 3, 2015

@author: NIuser
'''
from PyDAQmx import *
import numpy as np

class CallbackTask(Task):
    def __init__(self):
        Task.__init__(self)
        self.data = np.zeros(1000)
        self.a = []
        self.CreateAIVoltageChan('X-6368/ao0','',DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None)
        self.CfgSampClkTiming("",10000.0,DAQmx_Val_Rising,DAQmx_Val_ContSamps,1000)
        self.AutoRegisterEveryNSamplesEvent(DAQmx_Val_Acquired_Into_Buffer,1000,0)
        self.AutoRegisterDoneEvent(0)
    def EveryNCallback(self):
        read = int32()
        self.ReadAnalogF64(1000,10.0,DAQmx_Val_GroupByScanNumber,self.data,1000,byref(read),None)
        self.a.extend(self.data.tolist())
        print self.data[0]
        print len(self.a)
        return 0 # The function should return an integer
    def DoneCallback(self, status):
        print "Status",status.value
        return 0 # The function should return an integer


task=CallbackTask()
task.StartTask()

raw_input('Acquiring samples continuously. Press Enter to interrupt\n')

task.StopTask()
task.ClearTask()