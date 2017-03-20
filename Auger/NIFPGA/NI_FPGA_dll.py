'''Alan Buckley, Ed Barnard, Frank Ogletree'''
import ctypes
#import time
from ctypes import windll
import csv
import numpy as np
from collections import OrderedDict
import os

fpga_dll = windll.LoadLibrary('NIFpga.dll')
#test_array = np.array([1,0,1,1,1,0,0,0])
#test_array2 = np.array([1,0,0,0,0,0,0,1])
#size_4  = np.array([1,0,1,0])
#bitfilename = r"C:\Users\NIuser\Documents\Programs LV\R Series\builds\Omicron_R_1\Omicron Auger\data\NiFpga_CountertoDAC.lvbitx"
#signature = "146CFF8F04265BED0C2F87F8C0A0672A"
#resource = "RIO0"
###--------------End Basic Command Section----------------###

class NI_FPGA(object):        
    def __init__(self, bitfilename, signature, resource="RIO0", debug=False):
        self.debug = debug
        self.session = ctypes.c_uint32(0)
        self.bitfilename = bitfilename
        self.signature = signature
        self.resource = resource
        
        self.load_bitfile()

        #self.fifo = ctypes.c_uint32(0)
        # NOTE: CounterFifo declared in last lines of
        #NiFpga_CountertoDAC.h as I32 datatype with value of 0
        #However, self.fifo argument warrants use of U32 type   (:c) <-- Disappointment.
        #self.test_array = np.array([1,0,1,1,1,0,0,0])
        #self.test_array2 = np.array([1,0,0,0,0,0,0,1])
        # Load error code information from csv file derived from header file
#         self.err_code_list = []
#         with open(os.path.join(os.path.dirname(__file__), 'nifpga_errorcodes_14.csv')) as err_file:
#             csv_read = csv.reader(err_file, quotechar='"') #np.array([])
#             for row in csv_read:
#                 self.err_code_list.append(row)
#                 # np.concatenate((array1, row), axis=0)
#             #result = np.reshape(array1,(49,3))
#             #print(self.err_code_list)
#         self.err_code_list = self.err_code_list[1:]
#         self.err_bynum = OrderedDict()
#         for code, name, description in self.err_code_list:
#             num = int(code.replace('_','-'))
#             self.err_bynum[num] = name + ": " + description 
#             
            
    def handle_err(self, err_code):
        if err_code != 0:
            #print "Error {}. Consult FPGA Interface C API > API Reference > Errors using provided status code for more details ".format(err_code)
            #print "Error {}: {}".format(err_code, self.err_bynum[err_code])
            raise IOError("NI_FPGA Error {}: {}".format(err_code, self.err_bynum[err_code]))
        return err_code
    
    def load_bitfile(self):
        NiFpga_OpenAttribute_NoRun = 1 # from Nifpga.h
        attribute = NiFpga_OpenAttribute_NoRun
        session=self.session
        err = self.handle_err(fpga_dll.NiFpgaDll_Open(self.bitfilename, self.signature, self.resource, attribute, ctypes.byref(session)))
        if self.debug: print("Connection Status:" + str(err), self.session)
        if err == 0:
            if self.debug: print("Connected, FPGA configured to automatically run.")
        return err
            
    def unload(self):
        err = self.handle_err(fpga_dll.NiFpgaDll_Finalize())
        if self.debug: print("Unload Status:" + str(err), self.session)
        if err == 0:
            if self.debug: print("FPGA Library unloaded (caveat: not thread safe).")
            
    def close(self):
        err = self.handle_err(fpga_dll.NiFpgaDll_Close(self.session, 0))
        if self.debug: print("Disconnect Status:" + str(err))
        if err == 0:
            if self.debug: print("FPGA session disconnected (closed).")
        
    def run(self):
        self.attribute = 0
        err = self.handle_err(fpga_dll.NiFpgaDll_Run(self.session, self.attribute))
        if self.debug: print("Status:" + str(err))
        if err == 0:
            if self.debug: print("Running FPGA VI on target.")
    #Runs the FPGA VI on the target. If you use 
    #NiFpga_RunAttribute_WaitUntilDone, 
    #NiFpga_Run blocks the thread until the FPGA finishes running.
    
    def abort(self):
        err = self.handle_err(fpga_dll.NiFpgaDll_Abort(self.session))
        if self.debug: print("Status:" + str(err))
        if err == 0:
            if self.debug: print("FPGA VI successfully aborted.")
    #Aborts the FPGA VI.
    
    
    def reset(self):
        err = fpga_dll.NiFpgaDll_Reset(self.session)
        if self.debug: print("Status:" + str(err))
        if err == 0:
            if self.debug: print("FPGA VI successfully reset.")
    #Resets the FPGA VI.
    
    
    def download(self):
            err = self.handle_err(fpga_dll.NiFpgaDll_Download(self.session))
            if self.debug: print("Status:" + str(err))
            if err == 0:
                if self.debug: print("FPGA VI successfully downloaded.")
    #Redownloads FPGA to target.

###--------------End Basic Command Section----------------###

##### -----------Begin FIFO Functions ---------######

#NiFpgaDll_ConfigureFifo2
#NiFpgaDll_StopFifo
#NiFpgaDll_StartFifo

# NOTE: CounterFifo declared in last lines of
#       NiFpga_CountertoDAC.h as I32 datatype with value of 0

    """
     * Acquiring, reading, and releasing FIFO elements prevents the need to copy
     * the contents of elements from the host memory buffer to a separate
     * user-allocated buffer before reading. The FPGA target cannot write to
     * elements acquired by the host. Therefore, the host must release elements
     * after reading them. The number of elements acquired may differ from the
     * number of elements requested if, for example, the number of elements
     * requested reaches the end of the host memory buffer. Always release all
     * acquired elements before closing the session. Do not attempt to access FIFO
     * elements after the elements are released or the session is closed.
     """

    def Configure_Fifo2(self, fifo=0, reqDepth=8000):
        #self.requested_depth = ctypes.c_size_t(reqDepth)
        actual_depth = ctypes.c_size_t(0)
        err = fpga_dll.NiFpgaDll_ConfigureFifo2(self.session,
                                                fifo, 
                                                reqDepth,
                                                ctypes.byref(actual_depth))
        if self.debug: print("FIFO Configure Status:" + str(err))
        if err == 0:
            if self.debug: print("FIFO Configured")
        return actual_depth.value

    def Configure_Fifo(self, fifo=0, reqDepth=8000):
        """
        /**
         * Specifies the depth of the host memory part of the DMA FIFO. This method is
         * optional. In order to see the actual depth configured, use
         * NiFpga_ConfigureFifo2.
         *
         * @param session handle to a currently open session
         * @param fifo FIFO to configure
         * @param depth requested number of elements in the host memory part of the
         *              DMA FIFO
         * @return result of the call
         */
        NiFpga_Status NiFpga_ConfigureFifo(NiFpga_Session session,
                                   uint32_t       fifo,
                                   size_t         depth);
        """
        #requested_depth = ctypes.c_size_t(reqDepth)
        err = fpga_dll.NiFpgaDll_ConfigureFifo(self.session, fifo, reqDepth)
        if self.debug: print("FIFO Configure Status:" + str(err))
        if err == 0:
            if self.debug: print("FIFO Configured")
        
    ##Optional Method:  
    def Start_Fifo(self, fifo=0):
        err = fpga_dll.NiFpgaDll_StartFifo(self.session, fifo)
        if self.debug: print("Start FIFO Status:" + str(err))
        if err == 0:
            if self.debug: print("FIFO Started")

    def Read_Fifo(self, fifo=0, numberOfElements=8, timeout=10000, dtype='U32'):
        dtype_map = {'U32': (np.uint32, ctypes.c_uint32, fpga_dll.NiFpgaDll_ReadFifoU32),
                     'U64': (np.uint64, ctypes.c_uint64, fpga_dll.NiFpgaDll_ReadFifoU64)}
        
        np_dtype, ctype_dtype, read_func = dtype_map[dtype]        
        
        buffer = np.zeros(numberOfElements, dtype=np_dtype)
        bufpointer = buffer.ctypes.data_as(ctypes.POINTER(ctype_dtype))
        remaining = ctypes.c_uint32(0)
        """
         * @param session handle to a currently open session
         * @param fifo target-to-host FIFO from which to read
         * @param data outputs the data that was read
         * @param numberOfElements number of elements to read
         * @param timeout timeout in milliseconds, or NiFpga_InfiniteTimeout
         * @param elementsRemaining if non-NULL, outputs the number of elements
         *                          remaining in the host memory part of the DMA FIFO
         * @return result of the call
         
         NiFpga_Status NiFpga_ReadFifo<>(NiFpga_Session session,
                                 uint32_t       fifo,
                                 uint32_t*      data, //(type depends on fifo read type) 
                                 size_t         numberOfElements,
                                 uint32_t       timeout,
                                 uint32_t*        elementsRemaining);

         
         where <> can be U32, U64 etc
        """
        err = read_func(
                         self.session, 
                         fifo,
                         bufpointer,
                         numberOfElements,
                         int(timeout),
                         ctypes.byref(remaining))
        
        if self.debug: print("Read FIFO Status:" + str(err))
        if err == 0:
            if self.debug: print("FPGA FIFO Read.")
            if self.debug: print(remaining, buffer.shape)
        #Returns Data as "Last" I32
        return remaining.value, buffer
    
    
    

    def ReleaseFifoElements(self, fifo=0, numberOfElements=8):
        """
        /**
         * Releases previously acquired FIFO elements.
         *
         * The FPGA target cannot read elements acquired by the host. Therefore, the
         * host must release elements after acquiring them. Always release all acquired
         * elements before closing the session. Do not attempt to access FIFO elements
         * after the elements are released or the session is closed.
         *
         * @param session handle to a currently open session
         * @param fifo FIFO from which to release elements
         * @param elements number of elements to release
         * @return result of the call
         */
        NiFpga_Status NiFpga_ReleaseFifoElements(NiFpga_Session session,
                                                 uint32_t       fifo,
                                                 size_t         elements);
        """
                                                 
        err = fpga_dll.NiFpgaDll_ReleaseFifoElements(self.session, fifo, numberOfElements)
        if self.debug: print("Release FIFO Status:" + str(err))
        return err

    ##Optional Method:
    def Stop_Fifo(self, fifo=0):
        err = fpga_dll.NiFpgaDll_StopFifo(self.session, fifo)
        if self.debug: print("Stop FIFO Status:" + str(err))
        if err == 0:
            if self.debug: print("FPGA VI successfully reset.")

##### -----------End FIFO Functions ---------######
### -----------Begin Read/Write Functions ------###

    def Read_Bool(self, indicator):
        data = ctypes.c_uint8(0)
        err = fpga_dll.NiFpgaDll_ReadBool(self.session, indicator, ctypes.byref(data))
        #print data.value
        return err, bool(data.value)

    def Read_I16(self, indicator):
        data = ctypes.c_int16(0)
        err = fpga_dll.NiFpgaDll_ReadI16(self.session, indicator, ctypes.byref(data))
        return err, data.value
  
    def Read_U8(self, indicator):
        data = ctypes.c_uint8(0)
        err = fpga_dll.NiFpgaDll_ReadU8(self.session, indicator, ctypes.byref(data))
        return err, data.value

    def Read_U16(self, indicator):
        data = ctypes.c_uint16(0)
        err = fpga_dll.NiFpgaDll_ReadU16(self.session, indicator, ctypes.byref(data))
        return err, data.value

    def Read_U32(self, indicator):
        data = ctypes.c_uint32(0)
        err = fpga_dll.NiFpgaDll_ReadU32(self.session, indicator, ctypes.byref(data))
        return err, data.value
    

    def Read_ArrayBool(self, indicator, size):
        self.data = np.zeros(shape=size, dtype=np.byte)
        pointer = self.data.ctypes.data_as(ctypes.POINTER(ctypes.c_char)) #  <-- Not sure if variable name is necessary
        err = fpga_dll.NiFpgaDll_ReadArrayBool(self.session, indicator, pointer, size)
        return err, self.data ## ** data.value could quite possibly be problematic due to structural reasons

    def Read_ArrayU32(self, indicator, size):
        self.data = np.zeros(shape=size, dtype=np.uint32)
        pointer = self.data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)) #  <-- Not sure if variable name is necessary
        err = fpga_dll.NiFpgaDll_ReadArrayU32(self.session, indicator, pointer, size)
        return err, self.data

    
    def Write_ArrayBool(self, indicator, array, size):
        self.data = array #<-- We are writing array. This won't be overwritten. Needs to receive something to write 
        pointer = self.data.ctypes.data_as(ctypes.POINTER(ctypes.c_char))
        err = fpga_dll.NiFpgaDll_WriteArrayBool(self.session, indicator, pointer, size)
        return err


    def Write_Bool(self, indicator, value):
        err = fpga_dll.NiFpgaDll_WriteBool(self.session, indicator, value)
        return err

    def Write_I16(self, indicator, value):
        err = fpga_dll.NiFpgaDll_WriteI16(self.session, indicator, value)
        return err
        
    def Write_U32(self, indicator, value):
        err = fpga_dll.NiFpgaDll_WriteU32(self.session, indicator, value)
        return err

    def Write_U8(self, indicator, value):
        err = fpga_dll.NiFpgaDll_WriteU8(self.session, indicator, value)
        return err


### -----------End Read/Write Functions ------###



###--------------Begin Executable Section-----------------###

#if __name__ == '__main__':
    
    #array_gen()
    #print fpga.err_code_list


