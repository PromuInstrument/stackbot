from ScopeFoundry.hardware import HardwareComponent
import numpy as np
import time
try:
    import PyDAQmx as mx
except Exception as err:
    print("Failed to load PyDAQmx {}".format(err))

class GalvoScannerHW(HardwareComponent):
    
    name = 'galvo_scanner'
    
    
    def setup(self):
        
        S = self.settings
        
        S.New("ni_device", dtype=str, initial='Dev2')
        
        xp_raw = S.New("x_position_raw", dtype=float, ro=True, unit='V', spinbox_decimals=3)
        S.New("x_target_raw", dtype=float, ro=False, initial=0, unit='V', vmin=-10, vmax=+10, spinbox_decimals=3)
        yp_raw = S.New("y_position_raw", dtype=float, ro=True, unit='V', spinbox_decimals=3)
        S.New("y_target_raw", dtype=float, ro=False, initial=0, unit='V', vmin=-10, vmax=+10, spinbox_decimals=3)
        
        S.New("x_fault", dtype=bool,  ro=True, )
        S.New("y_fault", dtype=bool,  ro=True, )
        
        S.New("x_velocity", dtype=float, ro=True, unit='V', spinbox_decimals=3)
        S.New("y_velocity", dtype=float, ro=True, unit='V', spinbox_decimals=3)

        S.New("x_current", dtype=float, ro=True, unit='V', spinbox_decimals=3)
        S.New("y_current", dtype=float, ro=True, unit='V', spinbox_decimals=3)
        
        xp_deg = S.New("x_position_deg", dtype=float, ro=True, unit="deg", spinbox_decimals=3)
        xp_deg.connect_lq_scale(xp_raw, 1/0.5) # 0.5 V/deg
        
        yp_deg = S.New("y_position_deg", dtype=float, ro=True, unit="deg", spinbox_decimals=3)
        yp_deg.connect_lq_scale(yp_raw, 1/0.5) # 0.5 V/deg
        
        xt_deg = S.New("x_target_deg", dtype=float, ro=False, unit="deg", spinbox_decimals=3)
        xt_deg.connect_lq_scale(S.x_target_raw, 1/1.33) # 1.33 V/deg

        yt_deg = S.New("y_target_deg", dtype=float, ro=False, unit="deg", spinbox_decimals=3)
        yt_deg.connect_lq_scale(S.y_target_raw, 1/1.33) # 1.33 V/deg
        
        S.New("slow_move_speed", dtype=float, initial=100, unit="%", spinbox_decimals=0 )
        
        
        
    def connect(self):
        
        S = self.settings
        
        # Digital In
        ## 46 | X Fault   | PFI 11 / P2.3
        ## 38 | Y Fault   | PFI 7 / P1.7

        self.di_chan_names = ["x_fault", "y_fault"]
        self.di_chan_path = "{dev}/PFI11, {dev}/PFI7".format(dev=S['ni_device']) #"S['ni_device'] + '/' + S['di_chan']
        di_task = self.di_task = mx.Task()
        #int32 DAQmxCreateDIChan (TaskHandle taskHandle, const char lines[],
        #    const char nameToAssignToLines[], int32 lineGrouping);
        di_task.CreateDIChan(self.di_chan_path, '', mx.DAQmx_Val_ChanPerLine)
        self.di_chan_count = task_get_num_chans(di_task)

        # Analog Out
        self.ao_chan_path = "{dev}/ao0:1".format(dev=S['ni_device'])
        ao_task = self.ao_task = mx.Task()
        # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
        #    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
        ao_task.CreateAOVoltageChan(self.ao_chan_path, '', -10.0, +10.0, mx.DAQmx_Val_Volts, '')
        self.ao_chan_count = task_get_num_chans(ao_task)
        self.ao_rate = 10000 #Hz
        ao_task.CfgSampClkTiming("", self.ao_rate, mx.DAQmx_Val_Rising,
                                   mx.DAQmx_Val_FiniteSamps , 10000)

        # Analog In
#         30 | X Pos Out | ai3
#         65 | Y Pos Out | ai2
#         26 | X Vel     | ai13 (ai5-)
#         28 | Y Vel     | ai4
#         57 | X Current | ai7
#         60 | Y Current | ai5

        self.ai_chan_names = ["x_position_raw", "y_position_raw", "x_velocity", "y_velocity", "x_current", "y_current"]
        self.ai_chan_path = "{d}/ai3, {d}/ai2, {d}/ai13, {d}/ai4, {d}/ai7, {d}/ai5".format(d=S['ni_device'])
        print(self.ai_chan_path)
        ai_task = self.ai_task = mx.Task()
        #int32 CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], 
        #    int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
        ai_task.CreateAIVoltageChan(self.ai_chan_path, '', mx.DAQmx_Val_RSE, -10.0, +10.0, mx.DAQmx_Val_Volts,'')
        self.ai_chan_count = task_get_num_chans(ai_task)
        
#        Test to see if multiple AI tasks are possible... they are!
#         ai_task2 = self.ai_task2 = mx.Task()
#         ai_task2.CreateAIVoltageChan("Dev2/ai1", '', mx.DAQmx_Val_RSE, -10.0, +10.0, mx.DAQmx_Val_Volts,'')
        
        S.x_target_raw.connect_to_hardware(
            write_func = lambda x: self.goto_position_slow(x_volt=x))

        S.y_target_raw.connect_to_hardware(
            write_func = lambda y: self.goto_position_slow(y_volt=y))
        
        self.goto_position_slow()

    
    def disconnect(self):
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()

        #disconnect hardware
        if hasattr(self, 'nanodrive'):
            self.nanodrive.close()
            # clean up hardware object
            del self.nanodrive

    def read_ai_single(self):

        data = np.zeros(self.ai_chan_count, dtype = np.float64)
        read_size = mx.uInt32(self.ai_chan_count)
        read_count = mx.int32(0)    #returns samples per chan read
            
        #int32 DAQmxReadAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, 
        #    bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead,
        #    bool32 *reserved);
        self.ai_task.ReadAnalogF64(1, 0.1, mx.DAQmx_Val_GroupByScanNumber,
                                   data, read_size, mx.byref(read_count), None)

        ## Update LQ's 
        for i, name in enumerate(self.ai_chan_names):
            self.settings[name] = data[i]
        return data

    def read_di_single(self):
        
        
        #int32 DAQmxReadDigitalU32 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, 
        #    bool32 fillMode, uInt32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead,
        #    bool32 *reserved);
        read_count = mx.int32(0)    #returns samples per chan read

        data = np.zeros(self.di_chan_count, dtype = np.uint8)

        self.di_task.ReadDigitalU8(1, 0.1, mx.DAQmx_Val_GroupByScanNumber, data,len(data), mx.byref(read_count), None)
        
        data = data.astype(np.bool)
        
        for i, name in enumerate(self.di_chan_names):
            self.settings[name] = not data[i]
        
        #print("di:", data)
        return data

    def goto_position(self,x_volt=None,y_volt=None):
        
        if x_volt is None:
            x_volt = self.settings['x_target_raw']
        if y_volt is None:
            y_volt = self.settings['y_target_raw']
        
        ao_data = np.array([x_volt,y_volt], dtype=float)
        
        writeCount = mx.int32(0)
        # int32 DAQmxWriteAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan,
        #                             bool32 autoStart, float64 timeout, bool32 dataLayout, 
        #                             float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);


        self.ao_task.WriteAnalogF64(1, True, 0.1, mx.DAQmx_Val_GroupByScanNumber, 
                              ao_data, mx.byref(writeCount), None)
        
        print(writeCount.value)
        
    def goto_position_slow(self,x_volt=None,y_volt=None):
        self.ao_task.StopTask()

        if x_volt is None:
            x_volt = self.settings['x_target_raw']
        if y_volt is None:
            y_volt = self.settings['y_target_raw']

        
        x_start_pos = self.settings['x_position_raw'] / 0.4 # convert 4V output to 10V input
        y_start_pos = self.settings['y_position_raw'] / 0.4 # convert 4V output to 10V input

        dx = x_volt - x_start_pos
        dy = y_volt - y_start_pos
        
        
        max_speed = 0.65/130e-6 * 1.33 # 0.65 deg / 130us  # 1.33 V/deg --> final unit V/s
        

        # Compute the amount of time that will be needed to make the movement.
        dL = np.sqrt(dx**2 + dy**2)
        dt = dL/max_speed # seconds
        dt /= 0.01*self.settings['slow_move_speed']
                
        N = int( np.ceil(dt*self.ao_rate))

        write_count = mx.int32(0)

        ao_data = np.zeros( (N, 2), dtype=float)
        ao_data[:,0] = np.linspace(x_start_pos,x_volt,N)
        ao_data[:,1] = np.linspace(y_start_pos,y_volt,N)
        
        print(ao_data)
        self.ao_task.CfgSampClkTiming("", self.ao_rate, mx.DAQmx_Val_Rising,
                           mx.DAQmx_Val_FiniteSamps , N)

        self.ao_task.WriteAnalogF64(N, True, 0.5, mx.DAQmx_Val_GroupByScanNumber, 
                              ao_data, mx.byref(write_count), None)
        print("dL:{}, dt:{}, N:{}->{}".format(dL, dt, N, write_count.value))
        
        self.ao_data = ao_data


        
    def threaded_update(self):
        try:
            self.read_ai_single()
            self.read_di_single()
        except Exception as err:
            print("{} threaded_update failed {}".format(self.name, err) )
        time.sleep(0.010)



def task_get_num_chans(task):
    import PyDAQmx as mx
    chan_count = mx.uInt32(0)
    task.GetTaskNumChans(mx.byref(chan_count))
    return chan_count.value


###################
"""
Pin | Signal | NI chan | 
--------------------------
22 | X Pos In  | ao0
21 | Y Pos In  | ao1
30 | X Pos Out | ai3
65 | Y Pos Out | ai2
26 | X Vel     | ai13 (ai5-)
28 | Y Vel     | ai4
38 | Y Fault   | PFI 7 / P1.7
46 | X Fault   | PFI 11 / P2.3
57 | X Current | ai7
60 | Y Current | ai5
54 | GND       | ao GND
"""