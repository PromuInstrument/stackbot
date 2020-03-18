from ScopeFoundry import Measurement, h5_io
import PyDAQmx as mx
import numpy as np
import time
import pyqtgraph as pg

import threading
import sys
import _thread
import pyqtgraph.widgets.RemoteGraphicsView

from .kde_interp import KDE_Image

def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    print('{0} took too long'.format(fn_name), file=sys.stderr)
    sys.stderr.flush() # Python 3 stderr is likely buffered.
    _thread.interrupt_main() # raises KeyboardInterrupt


def exit_after(s):
    '''
    use as decorator to exit process if 
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer

class SyncStreamScanImage(Measurement):
    
    def setup(self):
        
        self.settings.New('image_size_x', dtype=int, initial=1000)
        self.settings.New('image_size_y', dtype=int, initial=1000)
        self.settings.New('amplitude_x', dtype=float, initial=5.0)
        self.settings.New('amplitude_y', dtype=float, initial=5.0)
        self.settings.New('kde_sigma', dtype=float, initial=2)              
        self.settings.New('ni_device', dtype=str, initial='X-6363')
        self.settings.New('do_chan', dtype=str, initial='port0/line0:3')
        self.settings.New('di_chan', dtype=str, initial='port0/line4:7')
        self.settings.New('ao_chan', dtype=str, initial='ao0:1')
        self.settings.New('ai_chan', dtype=str, initial='ai1:2')
        
        # KDE Interp
        self.kde_img = None
 
        
        
        
    def setup_figure(self):
        
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget()
        self.imgplotitem = pg.PlotItem()
        self.imgitem = pg.ImageItem()
        
        self.graph_layout.clear()
        self.imgplotitem.addItem(self.imgitem)
        self.graph_layout.addItem(self.imgplotitem)
        
        #self.imv = pg.ImageView()
        
        #self.ui = self.remote_graphics_view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()

        
    def setup_tasks(self):
        S = self.settings

        # Rates
        self.do_rate = int(10e6)
        self.di_rate = self.do_rate
        self.ao_rate = self.do_rate/20
        self.ai_rate = self.ao_rate
        self.ctr_rate = self.do_rate
        
        self.block_time = block_time = 0.050 # seconds
        self.display_update_period = self.block_time/2.

        #N_do = int(1e6)
        self.N_do = N_do = int(self.do_rate*block_time)
        self.N_di = int(N_do*(self.di_rate/self.do_rate))
        self.N_ao = int(N_do*(self.ao_rate/self.do_rate))
        self.N_ai = int(N_do*(self.ai_rate/self.do_rate))
        print (self.N_do, self.N_di, self.N_ao, self.N_ai)
        
        self.i_do = 0
        self.i_di = 0
        self.i_ao = 0
        self.i_ai = 0
        
        self.do_block_queue = []
        self.di_block_queue = []
        self.ao_block_queue = []
        self.ai_block_queue = []      

        ### Create Tasks
                
        # Digital Out
        self.do_chan_path = S['ni_device'] + '/' + S['do_chan']
        do_task = self.do_task = mx.Task()
        #int32 DAQmxCreateDOChan (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
        #do_task.CreateDOChan(self.do_chan_path, '', mx.DAQmx_Val_ChanForAllLines)
        do_task.CreateDOChan(self.do_chan_path, '', mx.DAQmx_Val_ChanPerLine )
        do_task.CfgSampClkTiming(None, self.do_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*N_do)
        # buffer size set to 4x chunk size in case of a delayed callback
        self.do_chan_count = task_get_num_chans(do_task)
        print ('do_chan_count', self.do_chan_count)
        #assert self.do_chan_count == 1 # single channel for all lines, use bitwise math to switch individual lines
        
        # Digital In
        self.di_chan_path = S['ni_device'] + '/' + S['di_chan']
        di_task = self.di_task = mx.Task()
        #int32 DAQmxCreateDIChan (TaskHandle taskHandle, const char lines[],
        #    const char nameToAssignToLines[], int32 lineGrouping);
        di_task.CreateDIChan(self.di_chan_path, '', mx.DAQmx_Val_ChanForAllLines)
        di_task.CfgSampClkTiming(None, self.di_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*self.N_di)
        self.di_chan_count = task_get_num_chans(di_task)
        assert self.di_chan_count == 1 # single channel for all lines, use bitwise math to select individual lines
        
        # Analog Out
        self.ao_chan_path = S['ni_device'] + '/' + S['ao_chan']
        ao_task = self.ao_task = mx.Task()
        # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
        #    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
        ao_task.CreateAOVoltageChan(self.ao_chan_path, '', -10.0, +10.0, mx.DAQmx_Val_Volts, '')
        ao_task.CfgSampClkTiming("", self.ao_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*self.N_ao) 
        self.ao_chan_count = task_get_num_chans(ao_task)

        # Analog In
        self.ai_chan_path = S['ni_device'] + '/' + S['ai_chan']
        ai_task = self.ai_task = mx.Task()
        #int32 CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], 
        #    int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
        ai_task.CreateAIVoltageChan(self.ai_chan_path, '', mx.DAQmx_Val_Diff, -10.0, +10.0, mx.DAQmx_Val_Volts,'')
        ai_task.CfgSampClkTiming("", self.ai_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 4*self.N_ai) 
        self.ai_chan_count = task_get_num_chans(ai_task)

        # Counter In
        
        # self.task.CreateCICountEdgesChan(self._channel, '', mx.DAQmx_Val_Rising, 0, mx.DAQmx_Val_CountUp )
        # self.task.SetCICountEdgesTerm( self._channel, self._input_terminal)
        # self.task.CfgSampClkTiming(clk_source, ctr_rate, mx.DAQmx_Val_Rising, ctr_mode, ctr_count) 


        ### Setup synchronous timing
        
        # Sync everything on Digital Out StartTigger
        start_trig_name = "/" + S['ni_device'] + '/do/StartTrigger'
        di_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)
        ao_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)
        ai_task.CfgDigEdgeStartTrig(start_trig_name, mx.DAQmx_Val_Rising)

        ### Connect Callbacks        
        set_n_sample_callback(self.do_task, self.N_do, self.on_do_callback, 'out')
        set_n_sample_callback(self.ao_task, self.N_ao, self.on_ao_callback, 'out')
        set_n_sample_callback(self.di_task, self.N_di, self.on_di_callback, 'in')
        set_n_sample_callback(self.ai_task, self.N_ai, self.on_ai_callback, 'in')

        # Start Input Tasks, they will wait for trigger from DO task        
        di_task.StartTask()
        ai_task.StartTask()
        
        ### Pre-fill output buffers (4x)
        N_prebuffer_file = 4
        ao_task.CfgOutputBuffer(N_prebuffer_file*self.N_ao)
        for i in range(N_prebuffer_file):
            self.on_ao_callback()

        do_task.CfgOutputBuffer(N_prebuffer_file*N_do)
        for i in range(N_prebuffer_file):
            self.on_do_callback()
    
    def stop_tasks(self):
        # Stop all tasks
        self.di_task.StopTask()
        self.ai_task.StopTask()
        self.ao_task.StopTask()
        self.do_task.StopTask()
        
        self.di_task.ClearTask()
        self.ai_task.ClearTask()
        self.ao_task.ClearTask()
        self.do_task.ClearTask()
        

    def run(self):

        self.first_display = True
        self.do_callback_times = []
        self.img= np.zeros((self.settings['image_size_x'],self.settings['image_size_y']), dtype=np.float)
        self.counts= np.zeros((self.settings['image_size_x'],self.settings['image_size_y']), dtype=np.float)
        
        
        try:
            self.setup_tasks()
            
            # Create h5 arrays
            
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
            self.h5_filename = self.h5_file.filename
            self.h5_m = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5_file)
            
            
            self.ao_data_h5 = self.h5_m.create_dataset('ao_data', 
                                     shape=(self.N_ao, self.ao_chan_count), 
                                     maxshape=(None, self.ao_chan_count), dtype=float, 
                                     chunks=(self.N_ao, self.ao_chan_count))
            self.ai_data_h5 = self.h5_m.create_dataset('ai_data', 
                                     shape=(self.N_ai, self.ai_chan_count),
                                     maxshape=(None, self.ai_chan_count), dtype=float,
                                     chunks=(self.N_ai, self.ai_chan_count))
    
    
            self.i_processed = 0        
            
            #KDE interp (it overwrites the one created in setup())
            Nx=self.settings['image_size_x']
            Ny=self.settings['image_size_y']
            Ax=self.settings['amplitude_x']
            Ay=self.settings['amplitude_y']
            self.kde_img = KDE_Image((Ny,Nx), self.settings['kde_sigma'])

            
            ### Start Output Tasks
            self.ao_task.StartTask()
            self.do_task.StartTask()
            
            block_i=0
    
            while not self.interrupt_measurement_called:
                time.sleep(0.1)
                
                
                
                if len(self.ao_block_queue) > 0:    
                    # pop things off queue
                    i_ao, ao_block = self.ao_block_queue.pop(0)
                    assert ao_block.shape[0] == self.N_ao
                    
                    # store in h5 dataset
                    if i_ao >= self.ao_data_h5.shape[0]:
                        self.ao_data_h5.resize((i_ao+self.N_ao, self.ao_chan_count))
                    
                    self.ao_data_h5[i_ao:i_ao+self.N_ao,:] = ao_block
                    
                    # process block
                    
                if len(self.ai_block_queue) > 0:    
                    # pop things off queue
                    i_ai, ai_block = self.ai_block_queue.pop(0)
                    assert ai_block.shape[0] == self.N_ai
                    
                    # store in h5 dataset
                    if i_ai >= self.ai_data_h5.shape[0]:
                        self.ai_data_h5.resize((i_ai+self.N_ai, self.ai_chan_count))
                    self.ai_data_h5[i_ai:i_ai+self.N_ai,:] = ai_block
                    
                # process block
                
                if self.ai_data_h5.shape[0] > self.i_processed:
                    
                                    
                    x = self.ao_data_h5[self.i_processed: self.i_processed + self.N_ao, 0]
                    y = self.ao_data_h5[self.i_processed: self.i_processed + self.N_ao, 1]    
                    #we are choosing here analog input channel 0 as signal
                    z = self.ai_data_h5[self.i_processed: self.i_processed + self.N_ao, 0]
                
#                     print ("x",x)
#                     print ("y",y)
#                     print ("z",z)
#                     
                    # Quick interpolation
                    x_img=np.uint32((Nx-1)/2*x/Ax+(Nx)/2)
                    y_img=np.uint32((Ny-1)/2*y/Ay+(Ny)/2)
#                     for ii in range(len(x)):
#                         #self.img[x_img[ii],y_img[ii]]+=z[ii]
#                         self.counts[x_img[ii],y_img[ii]]+=1
#                         cc=self.counts[x_img[ii],y_img[ii]]
#                         old_z=self.img[x_img[ii],y_img[ii]]
#                         new_z=(old_z*(cc-1)+z[ii])/cc
#                         self.img[x_img[ii],y_img[ii]]=new_z
#                         
                    ### KDE
                    x_img=(Nx-1)/2*x/Ax+(Nx)/2
                    y_img=(Ny-1)/2*y/Ay+(Ny)/2
                    
                    x_img = np.clip(x_img, 4, Nx-4)
                    y_img = np.clip(y_img, 4, Ny-4)

                    self.kde_img.add_datapoints(x_img, y_img,z)
                    
                    self.i_processed += self.N_ao
                block_i+=1
                print('Acquired samples:' , block_i*self.N_ai)
                if (block_i*self.N_ai) > 2e6:
                    break
                
                # Optional: store old blocks in a finite sized buffer
        finally:
            self.stop_tasks()
        
    
    #### Data Callbacks
    def on_do_callback(self):
        # generate new output data
        dt = 1./self.do_rate
        self.do_i_array = np.arange(self.i_do, self.i_do + self.N_do)
        time_array = self.do_i_array*dt
        #do_data = self.do_stream_gen(time_array)        
        do_data = np.zeros((self.N_do, self.do_chan_count), dtype=np.uint32)
        do_data[self.do_i_array%2 ==0, 0] = 1
        do_data[self.do_i_array%4 ==0, 1] = 1
        # load data in to output buffer
        writeCount = mx.int32(0)
        t0 = time.time()
        self.do_task.WriteDigitalU32(self.N_do, False, self.N_di/self.di_rate, mx.DAQmx_Val_GroupByScanNumber,
                                do_data, mx.byref(writeCount), None)
        
        self.do_data = do_data
        
        self.do_block_queue.append((self.i_do, do_data))
        
#         print('--> do callback', self.i_do, writeCount.value, time.time()-t0)
        self.do_callback_times.append(time.time()-t0)
        self.i_do += self.N_do
        return 0
    
    
    def on_ao_callback(self):
        # generate new output data
        self.ao_i_array = np.arange(self.i_ao, self.i_ao + self.N_ao)
        time_array = self.ao_i_array/self.ao_rate

        ao_data = self.ao_stream_gen(time_array)
        
        # load data in to output buffer
        writeCount = mx.int32(0)
        self.ao_task.WriteAnalogF64(self.N_ao, False, self.N_ao/self.ao_rate, mx.DAQmx_Val_GroupByScanNumber, 
                              ao_data.flatten(), mx.byref(writeCount), None)
        
        
        self.ao_block_queue.append( (self.i_ao, ao_data))
        print(len(self.ao_block_queue))
        self.ao_data = ao_data
        
#         print('--> ao callback', self.i_ao, writeCount.value)
        self.i_ao += self.N_ao
        return 0
        
    
    def on_ai_callback(self):
        
        data = np.zeros(self.N_ai*self.ai_chan_count, dtype = np.float64)
        read_size = mx.uInt32(self.N_ai*self.ai_chan_count)
        read_count = mx.int32(0)    #returns samples per chan read
            
        #int32 DAQmxReadAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, 
        #    bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
        self.ai_task.ReadAnalogF64(self.N_ai, 0,mx.DAQmx_Val_GroupByScanNumber,data, read_size, mx.byref(read_count), None)
        
        self.ai_data = data.reshape(-1, self.ai_chan_count)
        self.ai_i_array = np.arange(self.i_ai, self.i_ai+self.N_ai)
        #self.update_image_data(self.ai_data,self.ai_i_array)
        self.ai_block_queue.append( (self.i_ai,  self.ai_data))
    
#         print('<-- ai callback', self.i_ai ,data.mean())
        self.i_ai += self.N_ai
        return 0
    
    
    def on_di_callback(self):
        data = np.zeros(self.N_di*self.di_chan_count, dtype=np.uint32)
        read_size = self.N_di*self.di_chan_count
        read_count = mx.int32(0)    #returns samples per chan read
        # int32 DAQmxReadDigitalU32 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout,
        #    bool32 fillMode, uInt32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
        self.di_task.ReadDigitalU32(self.N_di, 0, mx.DAQmx_Val_GroupByScanNumber, data, read_size, mx.byref(read_count), None)
    
        self.di_data = data.reshape(-1, self.di_chan_count)
        self.di_i_array = self.i_ai + np.arange(self.N_ai)

        
        #self.di_block_queue.append( (self.i_di, self.di_data))
        #commented not to fill the memory without reason as di is not used
    
#         print('<-- on di callback', self.i_di, data)
        self.i_di += self.N_di
        return 0
   
    
    def do_stream_gen(self, t):
        do_stream = np.zeros(len(t), dtype=np.uint32)
        do_stream[(t*self.do_rate).astype(int)%2 == 0 ] |= 0b0001
        #print("do_stream_gen", do_stream[:15], t[:15])
        return do_stream
    
    def ao_stream_gen(self, t):
#         print("ao_stream_gen",t[0], t[-1])

        print(np.amax(t))
        ao_stream = np.zeros((len(t), self.ao_chan_count), dtype=float)
        Ax=self.settings['amplitude_x']
        Ay=self.settings['amplitude_y']
        Amp=(t/4)**(1)
        if np.amax(Amp)>1:
            Amp=1
        Amp=1
        ao_stream[:,0] = Ax*Amp*np.sin(np.sqrt(1)*t*2*np.pi*100)
        ao_stream[:,1] = Ay*Amp*np.sin(np.sqrt(2)*t*2*np.pi*40)
        #ao_stream[:,0] = Ax*Amp*np.sin(np.sqrt(1)*t*2*np.pi*40)
        #ao_stream[:,1] = Ay*Amp*np.cos(np.sqrt(1)*t*2*np.pi*40)
        
        return ao_stream
    
#  old version to be removed
#    def update_image_data(self,ai_data, ai_i):
#         Nx=self.settings['image_size_x']
#         Ny=self.settings['image_size_y']
#         
#         for ii in range(len(ai_i)):
#                        
#             ai_chunk_i= ai_i[ii]//self.N_ai
#             x=self.ao_block_queue[ai_chunk_i][1][ii,0]
#             y=self.ao_block_queue[ai_chunk_i][1][ii,1]
#             z=ai_data[ii,1] #we are choosing here analog input channel 0 as signal
# #             print ("x",x)
# #             print ("y",y)
# #             print ("z",z)
#             x_img=int((Nx-1)/2*x+(Nx)/2)
#             y_img=int((Ny-1)/2*y+(Ny)/2)
#             self.img[x_img,y_img]=+z
#         return 0
    
    def update_image_data(self,ai_data, ai_i):
        Nx=self.settings['image_size_x']
        Ny=self.settings['image_size_y']
        ai_chunk_n= ai_i[0]//self.N_ai # corresponding chunk number 
        x=self.ao_block_queue[ai_chunk_n][1][:,0]
        y=self.ao_block_queue[ai_chunk_n][1][:,1]
        z=ai_data[:,0] #we are choosing here analog input channel 0 as signal
        print ("x",x)
        print ("y",y)
        print ("z",z)
        x_img=np.uint32((Nx-1)/2*x+(Nx)/2)
        y_img=np.uint32((Ny-1)/2*y+(Ny)/2)
        
        for ii in range(len(x)):
            self.img[x_img[ii],y_img[ii]]=+z[ii]
            self.counts[x_img[ii],y_img[ii]]=+1
        return 0
     
    
    def update_display(self):
        t0 = pg.ptime.time()
#         self.imgitem.setImage(self.img)
        if self.kde_img:
            self.imgitem.setImage(self.kde_img.data)
#         print("update_display", pg.ptime.time()-t0)
    
    def create_h5_framed_dataset(self, name, single_frame_map, **kwargs):
        """
        Create and return an empty HDF5 dataset in self.h5_m that can store
        multiple frames of single_frame_map.
        
        Must fill the dataset as frames roll in.
        
        creates reasonable defaults for compression and dtype, can be overriden 
        with**kwargs are sent directly to create_dataset
        """
        if self.settings['save_h5']:
            shape=(self.settings['n_frames'],) + single_frame_map.shape
            if self.settings['continuous_scan']:
                # allow for array to grow to store additional frames
                maxshape = (None,)+single_frame_map.shape 
            else:
                maxshape = shape
#             print('maxshape', maxshape)
            default_kwargs = dict(
                name=name,
                shape=shape,
                dtype=single_frame_map.dtype,
                #chunks=(1,),
                chunks=(1,)+single_frame_map.shape,
                maxshape=maxshape,
                compression='gzip',
                #shuffle=True,
                )
            default_kwargs.update(kwargs)
            map_h5 =  self.h5_m.create_dataset(
                **default_kwargs
                )
            return map_h5
    
    def extend_h5_framed_dataset(self, map_h5, frame_num):
        """
        Adds additional frames to dataset map_h5, if frame_num 
        is too large. Adds n_frames worth of extra frames
        """
        if self.settings['continuous_scan']:
            current_num_frames, *frame_shape = map_h5.shape
            if frame_num >= current_num_frames:
#                 print ("extend_h5_framed_dataset", map_h5.name, map_h5.shape, frame_num)
                n_frames_extend = self.settings['n_frames']
                new_num_frames = n_frames_extend*(1 + frame_num//n_frames_extend)
                map_h5.resize((new_num_frames,) + tuple(frame_shape))
                return True
            else:
                return False
        else:
            return False

        
#####################
# Helper Functions
#####################
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
    
#     print(n_samples)
    task.EveryNCallback = cb_func
    task.AutoRegisterEveryNSamplesEvent(
        everyNsamplesEventType=event_type, 
        nSamples=n_samples,
        #options=mx.DAQmx_Val_SynchronousEventCallbacks)
        options=0)
def task_get_num_chans(task):
    chan_count = mx.uInt32(0)
    task.GetTaskNumChans(mx.byref(chan_count))
    return chan_count.value

