from ScopeFoundry import Measurement, h5_io
import PyDAQmx as mx
import numpy as np
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path,\
    auto_connect_widget_in_ui
from scipy import signal
import os

class PowerSpectrumLogger(Measurement):
    
    name = 'power_spec_logger'
        
    def setup(self):
        
        self.settings.New('channel', dtype=str, initial='/Dev2/ai0:2')
        self.settings.New('refresh_time', dtype=float, initial=1.0, unit='s')
        self.settings.New('log_freq_max', dtype=float, initial=2000., unit='Hz')
        self.settings.New('IEPE_excitation', dtype=bool, initial=False)
        self.settings.New('phys_unit', dtype=str, initial='V')
        self.settings.New('scale', dtype=float, initial=1.0, unit='V/V', spinbox_decimals=5)
        
        
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('save_raw', dtype=bool, initial=False)
        
        self.settings.New('update_display', dtype=bool, initial=True)
        self.settings.New('view_freq_min', dtype=float, initial=0.0, unit='Hz')
        self.settings.New('view_freq_max', dtype=float, initial=1000., unit='Hz')
        self.settings.New('view_show_dc', dtype=bool, initial=True)
        
        self.n_chans = 0
        self.N = 0
    
    def setup_figure(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "power_spec_logger.ui"))
        
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.settings.channel.connect_to_widget(self.ui.chan_lineEdit)
        self.settings.refresh_time.connect_to_widget(self.ui.time_doubleSpinBox)
        
        auto_connect_widget_in_ui(self.ui, self.settings.update_display)
        auto_connect_widget_in_ui(self.ui, self.settings.view_freq_min)
        auto_connect_widget_in_ui(self.ui, self.settings.view_freq_max)
        auto_connect_widget_in_ui(self.ui, self.settings.log_freq_max)
        auto_connect_widget_in_ui(self.ui, self.settings.save_h5)
        auto_connect_widget_in_ui(self.ui, self.settings.save_raw)

        
        
            
        #### Plots
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        
        p = self.power_spec_plot = self.graph_layout.addPlot(row=0, col=0)
        self.dc_plotlines = [None,None,None]

        p.setTitle("Power Spectrum")
        p.addLegend()

        p.current_plotline = p.plot(pen=pg.mkPen('r'), name='Current')
        p.avg_plotline = p.plot(name='Running average')
    
        #p.showLabel('top', True)
        p.setLabel('bottom', "Frequency", 'Hz')
        p.setLabel('left', 'PSD [V<sup>2</sup>/Hz]')
        p.setLogMode(x=False, y=True)
        
        self.settings.view_freq_min.add_listener(self.on_update_freq_lims)
        self.settings.view_freq_max.add_listener(self.on_update_freq_lims)
        
        self.on_update_freq_lims()


                    
        dc_p = self.dc_plot = self.graph_layout.addPlot(row=1, col=0)
        dc_p.addLegend()
        dc_p.setTitle("DC")
        dc_p.setLabel('bottom', "Time", 's')
        dc_p.setLabel('left', '&Delta; <sub>DC</sub>', units='V')
        
        dc_p.addItem(pg.InfiniteLine(movable=False, angle=0))

        for i,name in enumerate('xyz'):
            self.dc_plotlines[i] = dc_p.plot(pen=pg.mkPen('rgb'[i]), name=name, autoDownsampleFactor=1.0)
        
        dc_p.setDownsampling(auto=True, mode='subsample',)
        
        
        p = self.roi_plot = self.graph_layout.addPlot(row=2, col=0)
        p.addLegend()
        p.setTitle("Frequency Band History")
        p.setLabel('bottom', "Time", 's')        
        p.setXLink(self.dc_plot)
        p.setLabel('left', 'V')
        p.setLogMode(x=False, y=True)
        
        self.linear_range_items = []
        for i in range(2):
            color = ['#F005','#0F05'][i]
            lr = pg.LinearRegionItem(values=[55*(i+1),65*(i+1)], brush=pg.mkBrush(color))
            lr.num = i
            self.power_spec_plot.addItem(lr)
            lr.label = pg.InfLineLabel(lr.lines[0], "Region {}".format(i), position=0.8, rotateAxis=(1,0), anchor=(1, 1), movable=True)
            self.linear_range_items.append(lr)
            
            lr.hist_plotline = self.roi_plot.plot(pen=pg.mkPen(color[:-1]), name='Region {}'.format(i))
            lr.hist_plotline.setAlpha(1, auto=False)
        
        self.roi_plot.setDownsampling(auto=True, mode='subsample',)

        self.settings.phys_unit.add_listener(self.on_change_phys_unit)


    def on_change_phys_unit(self):
        unit = self.settings['phys_unit']
        self.power_spec_plot.setLabel('left', 'PSD [{}<sup>2</sup>/Hz]'.format(unit))
        self.dc_plot.setLabel('left', '&Delta; <sub>DC</sub>', units=unit)
        self.roi_plot.setLabel('left', unit)
        self.settings.scale.change_unit("{}/V".format(unit))


    def on_update_freq_lims(self):
        self.power_spec_plot.setXRange(self.settings['view_freq_min'], self.settings['view_freq_max'])

    def run(self):
        
        
        task = mx.Task()
        
        chan = self.settings['channel']
        task.CreateAIVoltageChan(chan, '',
                          mx.DAQmx_Val_PseudoDiff,
                          -5,+5, mx.DAQmx_Val_Volts, '')
        
        # https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000P7hXSAS&l=en-US
#                 task.CreateAIAccelChan(self.settings['channel'], '',
#                                  mx.DAQmx_Val_PseudoDiff,
#                                  -10.121457 , +10.121457, mx.DAQmx_Val_AccelUnit_g, 
#                                  0.494,#494mV/g
#                                  mx.DAQmx_Val_VoltsPerG,
#                                  mx.DAQmx_Val_Internal, 0.002, '')
        if self.settings['IEPE_excitation']:
            task.SetAICoupling(chan, mx.DAQmx_Val_AC)
            task.SetAIExcitVoltageOrCurrent(chan,mx.DAQmx_Val_Current)
            task.SetAIExcitSrc(chan, mx.DAQmx_Val_Internal)
            task.SetAIExcitVal(chan, 0.002)
        
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

        #self.psd_freq = np.fft.rfftfreq(self.current_data.shape[0], 1./rate)
        #self.current_psd = np.zeros((len(self.psd_freq), n_chans), dtype=float) + 1
        self.psd_freq, self.current_psd = signal.periodogram(self.current_data, fs=rate,window='hanning', detrend='linear', axis=0)
        max_freq_idx = np.searchsorted(self.psd_freq, self.settings['log_freq_max'])
        self.psd_freq = self.psd_freq[:max_freq_idx]
        self.current_psd = self.current_psd[:max_freq_idx]
        
        self.mean_psd = np.zeros_like(self.current_psd) 
        self.N = 0
        self.display_N = 0
        
        self.hist_len = int(100)
        self.dc_time = np.zeros(self.hist_len, dtype=float)
        self.dc_history = np.zeros( (self.hist_len, n_chans), dtype=float)
        self.psd_history = np.zeros( (self.hist_len, len(self.psd_freq), n_chans), dtype=float)
        
        self.mean_dc = np.zeros(n_chans, dtype=float)
        
        save_h5 = self.settings['save_h5']
        save_raw = self.settings['save_raw']
        
        if save_h5:
            self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
            print("Saving to", self.h5_file.filename)
            self.h5_m = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5_file)
        
            self.time_h5 = h5_io.create_extendable_h5_like(self.h5_m, 'time', self.dc_time, axis=0)
            self.dc_h5 = h5_io.create_extendable_h5_like(self.h5_m, 'dc_history', self.dc_history, axis=0)
            self.psd_h5 = h5_io.create_extendable_h5_like(self.h5_m, 'psd_history', self.psd_history, axis=0)
            if save_raw:
                self.raw_h5 = h5_io.create_extendable_h5_like(self.h5_m, 'raw_data', self.current_data, axis=0)
        
            self.h5_m['psd_freq'] = self.psd_freq # check this!
            
            self.ui.save_info_label.setText("Saving to: {}".format(os.path.basename(self.h5_file.filename)))
        else:
            self.ui.save_info_label.setText("Running: No Data Saving")
            
        
        try:
            while not self.interrupt_measurement_called:
                read_count = mx.int32(0)    #returns samples per chan read
                task.ReadAnalogF64(n_samples, n_samples/rate + 0.010, mx.DAQmx_Val_GroupByScanNumber, 
                                    self.adc_buffer, len(self.adc_buffer), mx.byref(read_count), None)
            
                self.current_data = self.adc_buffer.reshape(-1, n_chans)*self.settings['scale']
                dc = self.current_data.mean(axis=0)
                            
                self.psd_freq, self.current_psd = signal.periodogram(self.current_data, fs=rate,window='hanning', detrend='linear', axis=0)
                self.psd_freq = self.psd_freq[:max_freq_idx]
                self.current_psd = self.current_psd[:max_freq_idx]

                N = self.N
    
                            
                if N >= len(self.dc_time):
                    print("resizing arrays", N)
                    self.dc_time = np.resize(self.dc_time, 2*N)
                    self.dc_history = np.resize( self.dc_history, (2*N, n_chans))
                    self.psd_history = np.resize( self.psd_history, (2*N, len(self.psd_freq), n_chans))
                    
                    if save_h5:
                        h5_io.extend_h5_dataset_along_axis(self.time_h5, 2*N, 0)
                        h5_io.extend_h5_dataset_along_axis(self.dc_h5, 2*N, 0)
                        h5_io.extend_h5_dataset_along_axis(self.psd_h5, 2*N, 0)
                        if save_raw:
                            h5_io.extend_h5_dataset_along_axis(self.raw_h5, 2*N*n_samples, 0)
                            
                self.dc_time[N] = N * self.settings['refresh_time']
                self.dc_history[N,:] = self.current_data.mean(axis=0)
                self.psd_history[N, :, :] = self.current_psd
                
                if save_h5:
                    self.time_h5[N] = self.dc_time[N]
                    self.dc_h5[N,:] = self.dc_history[N,:]
                    self.psd_h5[N, :, :] = self.psd_history[N, :, :]
                    if save_raw:
                        self.raw_h5[N*n_samples:(N+1)*n_samples,:] = self.current_data
                        
                
                self.mean_psd = self.mean_psd*(N)/(N+1) + self.current_psd/(N+1)
                self.mean_dc = self.mean_dc*(N)/(N+1) + dc/(N+1)
                
                    
    
                self.N += 1
        finally:
            task.StopTask()
            if save_h5:
                self.ui.save_info_label.setText("Saved To: {}".format(os.path.basename(self.h5_file.filename)))
                self.h5_file.close()
            else:
                self.ui.save_info_label.setText("Done. No Data Saved")
                
            print("done")

        
    def update_display(self):
        #self.display_update_period = 0.5*self.settings['refresh_time']
        self.dc_plot.setVisible(self.settings['view_show_dc'])
        
        unit = self.settings['phys_unit']
        
        if (self.N > 1) and (self.N > self.display_N):
            self.power_spec_plot.current_plotline.setData(self.psd_freq[:], self.current_psd[:,:].sum(axis=1))
            self.power_spec_plot.avg_plotline.setData(self.psd_freq[:], self.mean_psd[:,:].sum(axis=1))
        
            #downsample_int = 1000
            N = self.N
            for i in range(self.n_chans):
                self.dc_plotlines[i].setData(self.dc_time[:N], self.dc_history[:N,i]-self.mean_dc[i])
                
            if self.n_chans == 3:
                x,y,z = self.mean_dc
                self.dc_plot.setTitle("DC x={:1.2f} {}   y={:1.2f} {}   z={:1.2f} {}".format(x, unit, y,unit, z,unit))
            else:
                self.dc_plot.setTitle("DC {} {}".format(self.mean_dc, unit))
            
            
            
            for lr in self.linear_range_items:
                f0, f1 = lr.getRegion()
                
                new_label = "R{}: {:1.1f} Hz : {:1.1f}".format(lr.num, 0.5*(f0+f1), 0.5*(f1-f0))
                lr.label.setFormat(new_label)
                
                i0 = np.searchsorted(self.psd_freq, f0)
                i1 = np.searchsorted(self.psd_freq, f1)
                
                lr.hist_plotline.setData(self.dc_time[:N], np.sqrt(self.psd_history[:N, i0:i1, :].sum(axis=(1,2) ) ))
                self.roi_plot.legend.items[lr.num][1].setText(new_label)
                #lr.hist_plotline.setName("asdf")
            self.display_N = self.N


