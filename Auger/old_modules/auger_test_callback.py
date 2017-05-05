from __future__ import division
import numpy as np
import time
import matplotlib.pyplot as plt

import PyDAQmx as mx

from equipment.SEM.raster_generator import RasterGenerator
from equipment.NI_CallBack import NI_DacTask, NI_SyncTaskSet, NI_AdcTask, NI_CounterTask


#  various test code 
if __name__ == '__main__':

    test = 'block counter callback'
    
    if test == 'block counter callback':
        rate = 1e5
        block = 1000
        data=np.zeros(block)
        a=list()
        b=list()
        adc = NI_DacTask('X-6368/ao0')
        ctr = NI_CounterTask('X-6368/ctr0','PFI0')        
        ctr.set_rate( rate, block, clock_source='ao/SampleClock' )
        ctr.set_callback(a)   #finite read     
        adc.set_rate(rate, block)
        #adc.set_callback(b)
        adc.load_buffer(data)
        
        ctr.start()
        adc.start()        
        raw_input('Acquiring samples continuously. Press Enter to interrupt\n')
        ctr.stop()
        ctr.clear()
        adc.stop()
        adc.clear()
        print(len(a))
        
    if test == 'counter':  
        ctr = NI_CounterTask('X-6368/ctr2','PFI12')
        ctr.start()
        elapsed = time.clock()
        for i in range(10):
            time.sleep(0.1)
            events =  ctr.get()
            now = time.clock()
            rate = events / (now - elapsed)
            print rate
            elaspsed = now
    
    if test == 'callback':
        rate = 1e5
        block = 1000
        adc=NI_AdcTask('X-6368/ai3')
        adc.set_rate(rate,block,finite=False)
        a=list()
        adc.set_callback(a)
        adc.start()
        raw_input('Acquiring samples continuously. Press Enter to interrupt\n')
        
        
        adc.stop()
        adc.clear()
        print(len(a))

    if test == 'sem':
        # make output waveform
        rate = 5e5          
        sem = RasterGenerator(points=1024, lines=768)
        buff_out = sem.data()
        block = sem.count()

        #setup tasks
        scan = NI_SyncTaskSet('X-6368/ao0:1', 'X-6368/ai1:3')
        scan.setup(rate, block, rate, block)
        scan.write_output_data_to_buffer(buff_out)

        scan.start()
        x = scan.read_buffer(timeout=10)
        
        in3 = x[::3]
        in1 = x[1::3]
        in2 = x[2::3]
        out1 = buff_out[::2]
        out2 = buff_out[1::2]
        
#         plt.subplot(211)
#         plt.plot(in1)
#         plt.plot(out1)
#         plt.subplot(212)
#         plt.plot(in2)
#         plt.plot(out2)
#         plt.show()
        
        out1 = out1.reshape(sem.shape())
        out2 = out2.reshape(sem.shape())
        in1 = in1.reshape(sem.shape())
        in2 = in2.reshape(sem.shape())
        in3 = in3.reshape(sem.shape())
        
        zz = 0.01
        print np.max(out1 - in1), np.min(out1 - in1), np.max(out2 - in2), np.min(out2 - in2)
        
        plt.imshow(in3)
        plt.show()

#         plt.subplot(221)
#         plt.imshow(out1)
#         plt.subplot(222)     
#         plt.imshow(in1 - out1, vmin = -zz, vmax = zz)
#         plt.subplot(223)
#         plt.imshow(out2)
#         plt.subplot(224)     
#         plt.imshow(in2- out2, vmin = -zz, vmax = zz)
#         plt.show()
             
    elif test == 'sync':
        # make output waveform
        block = 100
        rate = 1.0e5
                
        amplitude = 0.5
        period = 2
        out1 = amplitude * np.sin( np.linspace( 0, period*2*np.pi, block) )
        out2 = amplitude * np.sin( np.linspace( 0 + np.pi/2, period*2*np.pi+ np.pi/2, block) )
        buff_out = np.zeros( len(out1) + len(out2) )
        buff_out[::2] = out1    #interlaced output
        buff_out[1::2] = out2   

        #setup tasks
        scan = NI_SyncTaskSet('X-6368/ao0:1', 'X-6368/ai2:3', 1.0)
        scan.setup(rate, block, 10*rate, 10*block)
        scan.write_output_data_to_buffer(buff_out)

        scan.start()
        x = scan.read_buffer()
        
        in1 = x[::2]
        in2 = x[1::2]
        plt.subplot(211)
        plt.plot(in1)
        plt.plot(out1)
        plt.subplot(212)
        plt.plot(in2)
        plt.plot(out2)
        plt.show()
    else:         
        dac = NI_DacTask('X-6368/ao0:1', 'SEM ext scan')
        data = np.arange(0, 10, 0.001, dtype = np.float64)
    
        adc = NI_AdcTask('X-6368/ai2:3', 5, name = 'chan 2-3')
    
    if test == 'dual':
        # make output waveform
        block = 100000
        amplitude = 0.5
        period = 2
        out1 = amplitude * np.sin( np.linspace( 0, period*2*np.pi, block) )
        out2 = amplitude * np.sin( np.linspace( 0 + np.pi/2, period*2*np.pi+ np.pi/2, block) )
        buff_out = np.zeros( len(out1) + len(out2) )
        buff_out[::2] = out1    #interlaced output
        buff_out[1::2] = out2   
#         plt.plot( out1 )
#         plt.plot( out2 )
#         plt.show()
        
        rate = 1.0e6
        adc.set_rate(rate, block)   #finite read
        dac.set_rate(rate, block, finite=True)
        
         
        buffSize = 512
        buff = mx.create_string_buffer( buffSize )
        adc.task.GetNthTaskDevice(1, buff, buffSize)    #DAQmx name for input device
        trig_name = '/' + buff.value + '/ai/StartTrigger'
        print 'trigger name' , trig_name 
        dac.task.CfgDigEdgeStartTrig(trig_name, mx.DAQmx_Val_Rising)
        dac.load_buffer(buff_out)
        dac.start() #start dac first, waits for trigger from ADC to output data
        adc.start()

        x = adc.read_buffer()
        in1 = x[::2]
        in2 = x[1::2]
        plt.subplot(211)
        plt.plot(in1)
        plt.plot(out1)
        plt.subplot(212)
        plt.plot(in2)
        plt.plot(out2)
        plt.show()
        
    if test == 'read block':
        adc.set_rate( 1e5, 1000 )   #finite read
        x = adc.read_buffer()
        #plt.ion()
        plt.subplot(211)
        plt.plot(x[::2])
        plt.subplot(212)
        plt.plot(x[1::2])
        plt.show()
        #raw_input("press enter")
        for i in range(5):
            x = adc.read_buffer()
            plt.subplot(211)
            plt.plot(x[::2])
            plt.subplot(212)
            plt.plot(x[1::2])
            plt.show()      
            #raw_input("press enter")
            
    if test == 'read single':
        dac.set((0.5,-1))
        for i in range(16): 
            data = adc.get()
            print 'cycle {}, {}, {}'.format( i, data[0], data[1] )
        count = 10000
        #adc.set_single_read()
        adc.start()
        elapsed = time.clock()
        for i in range(count):
            adc.get()
        elapsed = time.clock() - elapsed
        print 'read {} single samples @ {} us per sample'.format( count, 1e6*elapsed/count )       
        
                
    if test == 'start stop' or test == 'all':
        dac.set_rate(2e6, len(data)/2, finite=True)
        dac.load_buffer(data)
        dac.ready()
        elapsed = time.clock()
        for i in range(16):
            dac.start()
            dac.wait()
            dac.stop()
        elapsed = time.clock() - elapsed
        print 'output buffer 16 times of {} 2-channel points in {} sec'.format( dac._sample_count, elapsed )
        
    if test == 'single' or test == 'all':
        data0 = np.zeros(2, dtype=np.float64)
        data1 = np.zeros(2, dtype=np.float64)
        data0[0] = data1[1] = 0.5
        count = 10000

        #dac.set_single()
        dac.start()
        elapsed = time.clock()
        for i in range(count):
            dac.set(data0)
            dac.set(data1)
        elapsed = time.clock() - elapsed
        print 'wrote {} single samples @ {} us per sample'.format( 2*count, 1e6*elapsed/(2*count) )
        
    if test == 'auto' or test == 'all':
        dac.set_rate(2e6, len(data)/2, finite=True)
        elapsed = time.clock()
        for i in range(16):
            dac.stop()
            dac.load_buffer(data, auto=True)   
            #dac.start()
            dac.wait()
            #dac.stop()
        elapsed = time.clock() - elapsed
        print 'wrote 16 autostart buffers of {} 2-channel points in {} sec'.format( dac._sample_count, elapsed )

print 'done'