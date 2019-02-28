'''
Created on 31.08.2014

@author: Benedikt Ursprung
'''

from __future__ import division
import numpy as np
import time
import matplotlib.pyplot as plt
import serial



class KeithleySourceMeter(object):#object -->KeithleySourceMeterComponent
    '''
    python low level Keythley Source
    '''
    KeithleyBaudRate = 9600
    
    def __init__(self, port="COM21", debug=False):
        self.port = port
        self.debug = debug
        
        self.ser = serial.Serial(port=self.port, baudrate = self.KeithleyBaudRate, stopbits=1, xonxoff=0, rtscts=0, timeout=5.0)#,         
        self.ser.flush()
        time.sleep(0.1)        
    
    def ask(self, cmd):
        self.send(cmd)
        resp = self.ser.readline()
        return resp.decode()
    
    def send(self, cmd):
        cmd += '\r\n'
        self.ser.write(cmd.encode())       

    def close(self):
        self.send('smua.source.output = smua.OUTPUT_OFF')
        self.ser.close()
        print('closed keithley')

    def source_V(self, V, channel = 'a', mode = 'DC'):
        self.send('smu{0}.source.func = smu{0}.OUTPUT_{1}VOLTS'.format(channel,mode))        
        self.send('smu{0}.source.levelv = {1}'.format(channel, V))

    def source_I(self, I, channel = 'a', mode = 'DC'):
        self.send('smu{0}.source.func = smu{0}.OUTPUT_{1}AMPS'.format(channel,mode))        
        self.send('smu{}.source.leveli = {}'.format(channel, I))   
        
    def reset(self, channel = 'a'):
        self.send('smu{}.reset()'.format(channel)) 
        
    def resetA(self):
        #depreciated 
        self.reset(channel='a')
        
    def setRanges_A(self,Vmeasure,Vsource,Imeasure,Isource):
        '''
        determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
            possible V ranges: 200 mV, 2 V, 20 V, 200V 
            possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy
        '''
        self.send('smua.source.rangev = '+str(Vsource))
        self.send('smua.measure.rangev = '+str(Vmeasure))   
        self.send('smua.source.rangei = '+str(Isource))
        self.send('smua.measure.rangei = '+str(Imeasure))
        
    def setAutoranges_A(self):
        '''
        enables autoranges on channel A
        Alternatively use setRanges_A(Vmeasure,Vsource,Imeasure,Isource) 
        to set ranges manually, which might be faster
        '''
        self.send('smua.source.autorangev = smua.AUTORANGE_ON')
        self.send('smua.measure.autorangev = smua.AUTORANGE_ON')   
        self.send('smua.source.autorangei = smua.AUTORANGE_ON')
        self.send('smua.measure.autorangei = smua.AUTORANGE_ON')                           
        
    def setV_A(self,V):
        """
        DEPRECIATED set DC voltage on channel A and turns it on
        """
        self.source_V(V, 'a', 'DC')
    
    def write_output_on(self, on = True, channel = 'a'):
        s = {True:'OUTPUT_ON',False:'OUTPUT_OFF'}[on]
        self.send('smu{0}.source.output = smu{0}.{1}'.format(channel,s))
    
    def switchV_A_on(self):
        self.write_output_on(True, channel='a')
        
    def switchV_A_off(self):
        self.write_output_on(False, channel='a')
               
    def getI_A(self):
        """
        DEPRECATED use read_I('a') gets a single current measurement
        """
        return self.read_I('a')

    def getV_A(self):
        """
        DEPRECATED use read_V('a') gets a single voltage measurement, 
        """
        return self.read_V('a')
      
    def read_V(self, channel = 'a'):
        resp = self.ask('print(smu{}.measure.v())'.format(channel))
        return float(resp)
    
    def read_I(self, channel = 'a'):
        resp = self.ask('print(smu{}.measure.i())'.format(channel))
        return float(resp)    
    
    def measureI_A(self,N,KeithleyADCIntTime,delay):
        """
        takes N current measurements and returns them as ndarray
        KeithleyADCIntTime = 0.1 sets integration time in Keitheley ADC to 0.1/60 sec
            Note: lowering KeithleyADCIntTime increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)
        delay [sec]: delay between measurements
        """
        
        self.send('format.data = format.ASCII')
        
        # Buffer
        self.send('smua.nvbuffer1.clear()')
        self.send('smua.nvbuffer1.appendmode = 1')
        self.send('smua.measure.count = 1')
        #self.ser.write('smua.nvbuffer2.appendmode = 1\r\n')        
        #self.ser.write('smua.nvbuffer2.clear()\r\n')            

        # Timestamps (if needed uncomment lowest section)       
        #self.ser.write('smua.nvbuffer1.collecttimestamps = 1\r\n')
        #self.ser.write('smua.nvbuffer1.timestampresolution=0.000001\r\n')

        # Speed configurations: 
        # autozero = 0 = off no significant speed boost
        # deleay/delayfactor seem to be 0 by default
        #     Note: lowering nplc increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)   
        self.write_ADC(KeithleyADCIntTime)        
        self.write_measure_delay(delay)
        #self.ser.write('smua.measure.delayfactor = 0\r\n')
        #self.ser.write('smua.measure.autozero = 0')
        
        # Make N measurements
          
        self.send('for v = 1, '+str(N)+'do smua.measure.i(smua.nvbuffer1) end')
        # read out measured currents
        StrI = self.ask('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        return np.array(StrI.split(','),dtype = np.float32)
    
        #self.ser.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.timestamps)\r\n')
        #Strt = self.ser.readline()
        #t = np.array(Strt.replace(',', '').split(),dtype = np.float32)  
        #return t,I 
        
    def write_ADC(self, time, channel= 'a'):
        # nplc really does boost steed: nplc = 0.1 sets integration time in Keitheley ADC to 0.1/60
        self.send('smu{}.measure.nplc = {}'.format(channel, time))
    
    def write_measure_delay(self, delay, channel= 'a'):
        '''
        delay [sec]: delay between measurements
        '''
        self.send('smu{}.measure.delay = {}'.format(channel, delay))

    def prepare_buffer(self, channel = 'a'):
        self.send('smu{}.nvbuffer1.clear()'.format(channel))
        self.send('smu{}.nvbuffer1.appendmode = 1'.format(channel))
        self.send('smu{}.measure.count = 1'.format(channel))
        self.send('smu{}.nvbuffer1.collectsourcevalues = 1'.format(channel))
        #self.ser.write('smua.nvbuffer2.appendmode = 1\r\n')        
        #self.ser.write('smua.nvbuffer2.clear()\r\n')  
        
    def measureIV_A(self,N,Vmin,Vmax,KeithleyADCIntTime=1, delay=0):
        """
        sweeps voltage from Vmin to Vmax in N steps and measures current using channel A
        returns I,V arrays, where I is measured, V is sourced
        KeithleyADCIntTime = 0.1 sets integration time in Keitheley ADC to 0.1/60 sec
            Note: lowering KeithleyADCIntTime increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)
        delay [sec]: delay between measurements
        """
        
        self.send('format.data = format.ASCII')
        
        # Buffer
        self.prepare_buffer()  

        # Timestamps (if needed uncomment lowest section)       
        #self.ser.write('smua.nvbuffer1.collecttimestamps = 1\r\n')
        #self.ser.write('smua.nvbuffer1.timestampresolution=0.000001\r\n')

        # Speed configurations: 
        # autozero = 0 = off no significant speed boost
        # deleay/delayfactor seem to be 0 by default
        # nplc really does boost steed: nplc = 0.1 sets integration time in Keitheley ADC to 0.1/60
        #     Note: lowering nplc increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)   
        self.write_ADC(KeithleyADCIntTime)        
        self.write_measure_delay(delay)
        
        # Make N measurements  
        dV = str(float(Vmax-Vmin)/(N-1))
        self.send('for v = 0, '+str(N)+'do smua.source.levelv = v*'+dV+'+'+str(Vmin)+' smua.measure.i(smua.nvbuffer1) end\r\n')
        time.sleep( N*(delay+0.05) ) # wait for the measurement to be completed 
        # read out measured currents
        StrI = self.ask('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        if self.debug: print("I:", repr(StrI))
        print(StrI.split(','))
        I = np.array(StrI.split(','), dtype = np.float32)
        
        # read out sourced voltages        
        StrV = self.ask('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)')   
        if self.debug: print("V:", repr(StrV))
        V = np.array(StrV.split(','),dtype = np.float32)
        return I,V          


if __name__ == '__main__':
    
    K1 = KeithleySourceMeter()

    K1.reset('a')
    
    #K1.setRanges_A(Vmeasure=2,Vsource=2,Imeasure=0.1,Isource=0.1)
    #K1.setAutoranges_A()
    K1.setV_A(V=0)
    
    K1.switchV_A_on()

    
    K1.setRanges_A(Vmeasure=2,Vsource=2,Imeasure=1,Isource=1)    
    I,V = K1.measureIV_A(20, Vmin=-1, Vmax = 1, KeithleyADCIntTime=1, delay=0)
    plt.plot(I,V)
    plt.show()
    
    K1.switchV_A_off()         
    K1.close()

    pass