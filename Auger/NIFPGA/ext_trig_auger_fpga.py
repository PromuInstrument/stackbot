"""Written by Frank Ogletree, Ed Barnard, and Alan Buckley
    Updated to use new FPGA code with U64 FIFO Feb 15 2017 Frank
"""

## Labview VI Functions 

try:
    from Auger.NIFPGA.NI_FPGA_dll import NI_FPGA
except Exception as err:
    print("failed to load NI_FPGA_dll",err)
    
from ScopeFoundry import HardwareComponent, LoggedQuantity
#this logged quantity system is archaic, need updated ScopeFoundry framework.
import numpy as np
import ctypes
import os
from cffi import FFI


# manually copied from NiFpga_CtrExtTrigAuger.h
fpga_vi_header = """
static const char* const NiFpga_CtrExtTrigAuger_Signature = "C785982188720152F75C0DE37DB6F8C8";

typedef enum
{
   NiFpga_CtrExtTrigAuger_IndicatorBool_Overflow = 0x811A,
} NiFpga_CtrExtTrigAuger_IndicatorBool;

typedef enum
{
   NiFpga_CtrExtTrigAuger_ControlU8_TriggerMode = 0x810E,
} NiFpga_CtrExtTrigAuger_ControlU8;

typedef enum
{
   NiFpga_CtrExtTrigAuger_ControlU32_SampleCount = 0x8110,
   NiFpga_CtrExtTrigAuger_ControlU32_SamplePeriod = 0x8114,
} NiFpga_CtrExtTrigAuger_ControlU32;

typedef enum
{
   NiFpga_CtrExtTrigAuger_TargetToHostFifoU64_CounterFIFO = 0,
} NiFpga_CtrExtTrigAuger_TargetToHostFifoU64;
"""


class ExtTrigAugerFPGA(object):        
    
      
    def __init__(self, debug=False):
        self.debug = debug
        
        self.bitfilename = os.path.join(os.path.dirname(__file__), 
                               "FPGA Daqmx Sync", "FPGA Bitfiles", 
                               "NiFpga_CtrExtTrigAuger.lvbitx").encode()
        self.signature = b"C785982188720152F75C0DE37DB6F8C8" # manually copied from NiFpga_CtrExtTrigAuger.h
        self.resource = b"RIO0"
        self.session = ctypes.c_uint32(0)

        
        if self.debug:
            print(repr(self.bitfilename))

        
        self.FPGA = NI_FPGA(self.bitfilename, self.signature, self.resource, debug=debug) 
        
        #self.ffi = FFI()
        #self.ffi.cdef(fpga_vi_header)
        #self.C = self.ffi.dlopen(None)
        #self.C = self.ffi.dlopen(ctypes.util.find_library('c'))

    def read_overflow(self):
        # manually copied from header text above
        indicator = 0x811A # NiFpga_CtrExtTrigAuger_IndicatorBool_Overflow
        err, data = self.FPGA.Read_Bool(indicator)
        if self.debug: print(  "Status:" + str(err))
        print( 'ctr overflow', err, data )
        if err == 0:
            if self.debug: print(  "FIFO Overflow Read", data )
            return data
        else:
            raise IOError("FIFO Overflow read err {}".format(err))
    


    def write_triggerMode(self, mode='pxi'):
        mode_map = dict(off=0, pxi=1, dio=2, int=3)
        assert mode in mode_map.keys()
        value = mode_map[mode]
        
        # manually copied from header text above
        indicator = 0x810E #NiFpga_CtrExtTrigAuger_ControlU8_TriggerMode
        err = self.FPGA.Write_U8(indicator, value)
        if self.debug: print(  "write_triggerMode Status:" + str(err))
        if err == 0:
            if self.debug: print(  "Trigger mode", mode, value )

        
    def read_triggerMode(self):
        # manually copied from header text above
        indicator = 0x810E #NiFpga_CtrExtTrigAuger_ControlU8_TriggerMode
        err, value = self.FPGA.Read_U8(indicator)
        rev_mode_map = ('off', 'pxi', 'dio', 'int')
        mode = rev_mode_map[value]
        if self.debug: print(  "read_triggerMode Status:" + str(err))
        if err == 0:
            if self.debug: print(  "Trigger mode", mode, value )
        return mode

        
    def write_sampleCount(self, sampleCount=0):
        indicator = 0x8110    #NiFpga_CtrExtTrigAuger_ControlU32_SampleCount = 0x8110,
        err = self.FPGA.Write_U32( indicator, sampleCount )
        if self.debug: print(  "write_sampleCount Status:" + str(err))
        if err == 0:
            if self.debug: print(  "Sample count", sampleCount )
    
    def write_samplePeriod(self, samplePeriod=2500):
        indicator = 0x8114    #NiFpga_CtrExtTrigAuger_ControlU32_SamplePeriod = 0x8114,
        err = self.FPGA.Write_U32( indicator, samplePeriod )
        if self.debug: print(  "samplePeriod Status:" + str(err))
        if err == 0:
            if self.debug: print(  "Sample period", samplePeriod )
    
    def read_num_transfers_in_fifo(self):
        elements_remain, buf = self.read_fifo_raw(numberOfElements=0, timeout=0)
        return int(np.floor(elements_remain/5))

    def read_fifo_raw(self, numberOfElements=5, timeout=0):
        return self.FPGA.Read_Fifo( fifo=0, 
                                    numberOfElements=numberOfElements, 
                                    timeout=timeout,
                                    dtype='U64')
    
    def read_fifo_parse(self, n_transfers=1, timeout=0):
        """
        for each transfer we expect 5 U64 words
        Each trigger transfers 5 x U64 in FIFO in 200 ns
        Each U64 has two U32s        
        U32 has 28 data bits  with an ID field in the 4 msb        
        IDs: elapsed time 08, trigger count 09        
        data channels 00 to 07
        """
        
        numberofElements=5*n_transfers
        remaining_words, buffer = self.read_fifo_raw(numberofElements, timeout)
        if self.debug: print('read_fifo_parse remaining_words', remaining_words)
        
        if len(buffer) == 0:
            return np.zeros((0,10),dtype=np.uint32)
        
        # reshape to N x 5 uint64 
        buf = buffer.reshape(-1, 5)
        
        # convert to a N x 10 uint32 array
        msU32 = buf>>32
        lsU32 = buf& 0xFFFFFFFF
        wide_buf = np.concatenate( [msU32, lsU32], axis=1)
        if self.debug: print(wide_buf.shape, wide_buf.dtype)

        ### Reorder columns        
        data = np.zeros_like(wide_buf, dtype=np.uint32)
        
        header_order = wide_buf[0]>>28 # use the first transfer headers to define order
        if self.debug: print(header_order)
        
        for jj, header in enumerate(header_order):
            # grab the 28bit data from each buffer column
            # and place it in the correct column of data
            data[:, header] = wide_buf[:, jj] & 0x0FFFFFFF 
        
        return data
    
    def flush_fifo(self):
        elements_remain, buf =self.read_fifo_raw(0)
        self.read_fifo_raw(elements_remain)
        return elements_remain
       
     
###--------------TESTS------------------###

def test1():
    import time
    
    vi = ExtTrigAugerFPGA(debug=True)
    fpga = vi.FPGA
    fpga.connect()
    fpga.reset()
    fpga.run()
    
    print(vi.read_overflow())
    vi.write_triggerMode('pxi')
    
    print(vi.read_overflow())
    print(vi.read_overflow())
    print(vi.read_overflow())
    print(vi.read_overflow())
    time.sleep(10.0)
    print(vi.read_overflow())

    vi.write_triggerMode('off')
    print('trigger off', vi.read_overflow())
   
    fpga.close()    

def test2():
    import time
    from ScopeFoundryHW.ni_daq import NI_SyncTaskSet
    
    # set up sync io on X-board with a pixel trigger on PXI_Trig0
    sync_analog_io = NI_SyncTaskSet(out_chan  = b"X-6368/ao0:1",
                                       in_chan   = b"X-6368/ai0:1",
                                       ctr_chans = [],  #self.counter_channel_addresses.val.split(','),
                                       ctr_terms = [], #self.counter_channel_terminals.val.split(','),
                                       clock_source = b"",
                                       trigger_output_term = b"/X-6368/PXI_Trig0",
                                       )
    
    Nsamples = 100
    
    sync_analog_io.setup(rate_out = 1e3,
                        count_out = Nsamples, 
                        rate_in = 1e3,
                        count_in = Nsamples, 
                           #pad = ?,
                          is_finite=True)

    sync_analog_io.write_output_data_to_buffer(np.ones(2*Nsamples,dtype=float))

    # setup fpga and activate
    vi = ExtTrigAugerFPGA(debug=True)
    fpga = vi.FPGA
    fpga.load_bitfile()
    fpga.reset()
    fpga.run()
     
    vi.write_triggerMode('pxi')
    
    # start triggers
    sync_analog_io.start()
    
    time.sleep(2.0)
    
    vi.read_overflow()
    #print( fpga.Read_Fifo(fifo=0, numberOfElements=505, timeout=0, dtype='U64'))
    buf = vi.read_fifo_parse(n_transfers=Nsamples)
    print('parsed fifo output', buf.shape)
    print(buf[:10,:])
    
    print( sync_analog_io.read_adc_buffer_reshaped(count=0, timeout=1.0).shape)
    
    vi.read_overflow()

    sync_analog_io.stop()
    
    
    ### test internal triggering
    vi.write_triggerMode('off')
    vi.flush_fifo()
    print( 'remaining elements', vi.read_fifo_raw(0, 0))
    
    print( "internal counter test")
    vi.write_sampleCount(Nsamples)
    vi.write_samplePeriod(2500)
    vi.write_triggerMode('int')
    
    time.sleep(1.0)
    
    vi.read_overflow()
    #print( fpga.Read_Fifo(fifo=0, numberOfElements=505, timeout=0, dtype='U64'))
    print( 'elements after test', vi.read_fifo_raw(0, 0))
    buf = vi.read_fifo_parse(n_transfers=Nsamples)
    print('parsed fifo output', buf.shape)
    print(buf[:10,:])
    
    print( 'trigger mode', vi.read_triggerMode())
    
    
    fpga.close()
    
    #np.save('buffer.npy', buf)
    
if __name__ == '__main__':
    test2()