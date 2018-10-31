'''
Created on 31.08.2014

@author: Benedikt
'''

from __future__ import division
import numpy as np
import time
import matplotlib.pyplot as plt
import serial



class KeithleySourceMeter(object):#object -->KeithleySourceMeterComponent
    '''
    classdocs
    '''
    KeithleyBaudRate = 9600
    
    def __init__(self, port="COM21", debug=False):
        self.port = port
        self.debug = debug
        
        self.ser = serial.Serial(port=self.port, baudrate = self.KeithleyBaudRate, stopbits=1, xonxoff=0, rtscts=0, timeout=5.0)#,         
        self.ser.flush()
        time.sleep(0.1)        
    
    def resetA(self):
        self.ser.write('smua.reset()\r\n'.encode())        

    def close(self):
        self.ser.write('smua.source.output = smua.OUTPUT_OFF\n'.encode())
        self.ser.close()
        print('closed keithley')


    def setRanges_A(self,Vmeasure,Vsource,Imeasure,Isource):
        '''
        determines the accuracy for measuring and sourcing
        Alternatively use setAutorange_A() which might be slower
            possible V ranges: 200 mV, 2 V, 20 V, 200V 
            possible I ranges: 100 nA, 1 uA, 10uA, ... 100 mA, 1 A, 1.5, 10 A (10 A only in pulse mode)
        refer to UserManual/Specification for accuracy
        '''
        self.ser.write('smua.source.rangev = '+str(Vsource)+'\r\n'.encode())
        self.ser.write('smua.measure.rangev = '+str(Vmeasure)+'\r\n'.encode())   
        self.ser.write('smua.source.rangei = '+str(Isource)+'\r\n'.encode())
        self.ser.write('smua.measure.rangei = '+str(Imeasure)+'\r\n'.encode())
        
    def setAutoranges_A(self):
        '''
        enables autoranges on channel A
        Alternatively use setRanges_A(Vmeasure,Vsource,Imeasure,Isource) 
        to set ranges manually, which might be faster
        '''
        self.ser.write('smua.source.autorangev = smua.AUTORANGE_ON\r\n'.encode())
        self.ser.write('smua.measure.autorangev = smua.AUTORANGE_ON\r\n'.encode())   
        self.ser.write('smua.source.autorangei = smua.AUTORANGE_ON\r\n'.encode())
        self.ser.write('smua.measure.autorangei = smua.AUTORANGE_ON\r\n'.encode())                           
        
    def setV_A(self,V):
        """
        set DC voltage on channel A and turns it on
        """
        self.ser.write('smua.source.func = smua.OUTPUT_DCVOLTS\r\n'.encode())
        self.ser.write('smua.source.levelv = '+str(V)+'\r\n'.encode())
        #print('set Voltage in channel A to '+str(V_A))
        pass
    
    def switchV_A_on(self):
        self.ser.write('smua.source.output = smua.OUTPUT_ON\r\n'.encode())

    def switchV_A_off(self):
        self.ser.write('smua.source.output = smua.OUTPUT_OFF\r\n'.encode())
               
    def getI_A(self):
        """
        gets a single current measurement
        use measureI_A(self,N,KeithleyADCIntTime,delay) for multiple readouts
        """
        self.ser.write('print(smua.measure.i())\r\n'.encode())               
        return float(self.ser.readline())

    def getV_A(self):
        """
        gets a single voltage measurement
        """
        self.ser.write('print(smua.measure.v())\r\n'.encode())               
        return float(self.ser.readline())
        
   
    def measureI_A(self,N,KeithleyADCIntTime,delay):
        """
        takes N current measurements and returns them as ndarray
        KeithleyADCIntTime = 0.1 sets integration time in Keitheley ADC to 0.1/60 sec
            Note: lowering KeithleyADCIntTime increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)
        delay [sec]: delay between measurements
        """
        
        self.ser.write('format.data = format.ASCII\r\n'.encode())
        
        # Buffer
        self.ser.write('smua.nvbuffer1.clear()\r\n'.encode())
        self.ser.write('smua.nvbuffer1.appendmode = 1\r\n'.encode())
        self.ser.write('smua.measure.count = 1\r\n'.encode())
        #self.ser.write('smua.nvbuffer2.appendmode = 1\r\n')        
        #self.ser.write('smua.nvbuffer2.clear()\r\n')            

        # Timestamps (if needed uncomment lowest section)       
        #self.ser.write('smua.nvbuffer1.collecttimestamps = 1\r\n')
        #self.ser.write('smua.nvbuffer1.timestampresolution=0.000001\r\n')

        # Speed configurations: 
        # autozero = 0 = off no significant speed boost
        # deleay/delayfactor seem to be 0 by default
        # nplc really does boost steed: nplc = 0.1 sets integration time in Keitheley ADC to 0.1/60
        #     Note: lowering nplc increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)   
        self.ser.write('smua.measure.nplc = '+str(KeithleyADCIntTime)+'\r\n'.encode())
        self.ser.write('smua.measure.delay = '+str(delay)+'\r\n'.encode())
        #self.ser.write('smua.measure.delayfactor = 0\r\n')
        #self.ser.write('smua.measure.autozero = 0')
        
        # Make N measurements
          
        self.ser.write('for v = 1, '+str(N)+'do smua.measure.i(smua.nvbuffer1) end\r\n'.encode())
        # read out measured currents
        self.ser.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)\r\n'.encode())
        StrI = self.ser.readline()
        return np.array(StrI.replace(',', '').split(),dtype = np.float32)
    
        #self.ser.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.timestamps)\r\n')
        #Strt = self.ser.readline()
        #t = np.array(Strt.replace(',', '').split(),dtype = np.float32)  
        #return t,I 
        
    def measureIV_A(self,N,Vmin,Vmax,KeithleyADCIntTime=1, delay=0):
        """
        sweeps voltage from Vmin to Vmax in N steps and measures current using channel A
        returns I,V arrays, where I is measured, V is sourced
        KeithleyADCIntTime = 0.1 sets integration time in Keitheley ADC to 0.1/60 sec
            Note: lowering KeithleyADCIntTime increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)
        delay [sec]: delay between measurements
        """
        
        self.ser.write('format.data = format.ASCII\r\n'.encode())
        
        # Buffer
        self.ser.write('smua.nvbuffer1.clear()\r\n'.encode())
        self.ser.write('smua.nvbuffer1.appendmode = 1\r\n'.encode())
        self.ser.write('smua.measure.count = 1\r\n'.encode())
        self.ser.write('smua.nvbuffer1.collectsourcevalues = 1 \r\n'.encode())
        #self.ser.write('smua.nvbuffer2.appendmode = 1\r\n')        
        #self.ser.write('smua.nvbuffer2.clear()\r\n')            

        # Timestamps (if needed uncomment lowest section)       
        #self.ser.write('smua.nvbuffer1.collecttimestamps = 1\r\n')
        #self.ser.write('smua.nvbuffer1.timestampresolution=0.000001\r\n')

        # Speed configurations: 
        # autozero = 0 = off no significant speed boost
        # deleay/delayfactor seem to be 0 by default
        # nplc really does boost steed: nplc = 0.1 sets integration time in Keitheley ADC to 0.1/60
        #     Note: lowering nplc increases rate of measurements and decreases accuracy (0.001 is fastest and 25 slowest)   
        self.ser.write(('smua.measure.nplc = '+str(KeithleyADCIntTime)+'\r\n').encode())
        self.ser.write(('smua.measure.delay = '+str(delay)+'\r\n').encode())
        #self.ser.write('smua.measure.delayfactor = 0\r\n')
        #self.ser.write('smua.measure.autozero = 0')
        
        # Make N measurements  
        dV = str(float(Vmax-Vmin)/(N-1))
        self.ser.write(('for v = 0, '+str(N)+'do smua.source.levelv = v*'+dV+'+'+str(Vmin)+' smua.measure.i(smua.nvbuffer1) end\r\n').encode())
        
        # read out measured currents
        self.ser.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)\r\n'.encode())
        StrI = self.ser.readline()
        if self.debug: print("I:", repr(StrI))
        print(StrI.decode().split(','))
        I = np.array(StrI.decode().split(','), dtype = np.float32)
        
        # read out sourced voltages        
        self.ser.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.sourcevalues)\r\n'.encode())   
        StrV = self.ser.readline().decode()
        if self.debug: print("V:", repr(StrV))
        V = np.array(StrV.replace(',', '').split(),dtype = np.float32)  
        return I,V          


if __name__ == '__main__':
    
    K1 = KeithleySourceMeter()

    K1.resetA()
    
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