from ScopeFoundry import Measurement
import PyDAQmx as mx
import numpy as np
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class AccelLogger(Measurement):
    
    name = 'accel_logger'
    
    def setup(self):
        
        self.settings.New('channel', dtype=str, initial='/Dev2/ai3')
        self.settings.New('refresh_time', dtype=float, initial=1.0, unit='s')

    
    def setup_figure(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "accel_logger.ui"))
        
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.settings.channel.connect_to_widget(self.ui.chan_lineEdit)
        self.settings.refresh_time.connect_to_widget(self.ui.time_doubleSpinBox)
        
            
        #### Plots
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        
        self.power_spec_plots = [None,None,None]
        for i in range(3):
            self.power_spec_plots[i] = p = self.graph_layout.addPlot(row=i, col=0)
            p.setTitle("Chan {}".format(i))
            p.current_plotline = p.plot(pen=pg.mkPen('r'))
            p.mean_plotline = p.plot()
        
            p.showLabel('top', True)
            p.setLabel('top', "Frequency", 'Hz')
            p.setLogMode(x=True, y=True)
            
    def run(self):
        
        
        task = mx.Task()
        task.CreateAIAccelChan(self.settings['channel'], '',
                                 mx.DAQmx_Val_PseudoDiff,
                                 -10.121457 , +10.121457, mx.DAQmx_Val_AccelUnit_g, 
                                 0.494,#494mV/g
                                 mx.DAQmx_Val_VoltsPerG,
                                 mx.DAQmx_Val_Internal, 0.002, '')
        
        
        chan_count = mx.uInt32(0) 
        task.GetTaskNumChans(mx.byref(chan_count))
        self.n_chans = n_chans = chan_count.value

        #n_samples = 51200
        rate = 51200
        n_samples = int(self.settings['refresh_time']*rate)
        
        task.CfgSampClkTiming("", rate, mx.DAQmx_Val_Rising,
                                   mx.DAQmx_Val_ContSamps, 0)
        
        
        self.adc_buffer = np.zeros(n_chans * n_samples, dtype = np.float64)
        self.current_data = self.adc_buffer.reshape(-1, n_chans)

        self.fft_freq = np.fft.rfftfreq(self.current_data.shape[0], 1./rate)
        self.current_fft = np.zeros((len(self.fft_freq), n_chans), dtype=float)
        self.mean_fft = np.zeros_like(self.current_fft)
        self.mean_fft_count = 0
        
        while not self.interrupt_measurement_called:
            read_count = mx.int32(0)    #returns samples per chan read
            task.ReadAnalogF64(n_samples, n_samples/rate + 0.010, mx.DAQmx_Val_GroupByScanNumber, 
                                self.adc_buffer, len(self.adc_buffer), mx.byref(read_count), None)
        
            self.current_data = self.adc_buffer.reshape(-1, n_chans)
            self.current_fft = np.abs(np.fft.rfft(self.current_data,axis=0))
            
            self.mean_fft_count += 1
            n = self.mean_fft_count
            
            self.mean_fft = self.mean_fft*(n-1)/n + self.current_fft/n
            
            #print('read', read_count.value)
            #print(data.mean())#, data)
        task.StopTask()
        print("done")
        
    def update_display(self):
        for i,p in enumerate(self.power_spec_plots):
            if i >= self.n_chans:
                return
            p.current_plotline.setData(self.fft_freq[1:], self.current_fft[1:,i]+1e-10)
            p.mean_plotline.setData(self.fft_freq[1:], self.mean_fft[1:,i]+1e-10)