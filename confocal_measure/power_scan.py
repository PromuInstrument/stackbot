from ScopeFoundry import Measurement
import numpy as np
import time
from ScopeFoundry import h5_io
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg

class PowerScanMeasure(Measurement):
    
    name = 'power_scan'
    
    def __init__(self, app):
        self.ui_filename = sibling_path(__file__, "power_scan.ui")
        Measurement.__init__(self, app)
        
    def setup(self):
        
        self.power_wheel_min = self.add_logged_quantity("power_wheel_min", 
                                                          dtype=float, unit='', initial=0, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_max = self.add_logged_quantity("power_wheel_max", 
                                                          dtype=float, unit='', initial=280, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_ndatapoints = self.add_logged_quantity("power_wheel_ndatapoints", 
                                                          dtype=int, unit='', initial=100, vmin=1, vmax=3200, ro=False)
        
        self.up_and_down_sweep    = self.add_logged_quantity("up_and_down_sweep",dtype=bool, initial=True)

        self.collect_apd      = self.add_logged_quantity("collect_apd",      dtype=bool, initial=True)
        self.collect_spectrum = self.add_logged_quantity("collect_spectrum", dtype=bool, initial=False)
        self.collect_lifetime = self.add_logged_quantity("collect_lifetime", dtype=bool, initial=True)
        self.collect_ascom_img = self.add_logged_quantity('collect_ascom_img', dtype=bool, initial=False)
        
        self.settings.New("x_axis", dtype=str, initial='power_wheel', choices=('power_wheel', 'pm_power'))
    
    
    
    def setup_figure(self):
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

        self.power_wheel_min.connect_to_widget(self.ui.powerwheel_min_doubleSpinBox)
        self.power_wheel_max.connect_to_widget(self.ui.powerwheel_max_doubleSpinBox)
        self.power_wheel_ndatapoints.connect_to_widget(self.ui.num_datapoints_doubleSpinBox)

        self.up_and_down_sweep.connect_bidir_to_widget(self.ui.updown_sweep_checkBox)

        self.collect_apd.connect_to_widget(self.ui.collect_apd_checkBox)
        self.collect_spectrum.connect_to_widget(self.ui.collect_spectrum_checkBox)
        self.collect_lifetime.connect_to_widget(self.ui.collect_picoharp_checkBox)
        self.collect_ascom_img.connect_to_widget(self.ui.collect_ascom_img_checkBox)
        
        
        
        # Hardware connections
        if 'apd_counter' in self.app.hardware.keys():
            self.app.hardware.apd_counter.settings.int_time.connect_bidir_to_widget(
                                                                    self.ui.apd_int_time_doubleSpinBox)
        else:
            self.collect_apd.update_value(False)
            self.collect_apd.change_readonly(True)
        
        if 'winspec_remote_client' in self.app.hardware.keys():
            self.spec_acq_time = self.app.hardware['winspec_remote_client'].settings.acq_time
            self.spec_acq_time.connect_to_widget(self.ui.spectrum_int_time_doubleSpinBox)
            self.spec_readout_measure_name  = 'winspec_readout'
            
        elif 'andor_ccd' in self.app.hardware.keys():
            self.spec_acq_time = self.app.hardware['andor_ccd'].settings.exposure_time
            self.spec_acq_time.connect_to_widget(self.ui.spectrum_int_time_doubleSpinBox)
            self.spec_readout_measure_name = 'andor_ccd_readout'
        else:
            self.collect_spectrum.update_value(False)
            self.collect_spectrum.change_readonly(True)

        if 'ascom_camera' in self.app.hardware.keys():
            self.app.hardware.ascom_camera.settings.exp_time.connect_bidir_to_widget(
                self.ui.ascom_img_int_time_doubleSpinBox)
        else:
            self.collect_ascom_img.update_value(False)
            self.collect_ascom_img.change_readonly(True)
            
        if 'picoharp' in self.app.hardware.keys():
            self.app.hardware['picoharp'].settings.Tacq.connect_to_widget(
                self.ui.picoharp_int_time_doubleSpinBox)
        else:
            self.collect_lifetime.update_value(False)
            self.collect_lifetime.change_readonly(True)
            
            
        # Plot
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.plot1 = self.graph_layout.addPlot(title="Power Scan")

        self.plot_line1 = self.plot1.plot([0])

    def update_display(self):
        ii = self.ii
        if self.settings['x_axis'] == 'power_wheel':
            X = self.power_wheel_position[:ii]
        else:
            X = self.pm_powers[:self.ii]
        
        if self.settings['collect_apd']:
            self.plot_line1.setData(X, self.apd_count_rates[:ii])
        elif self.settings['collect_lifetime']:
            self.plot_line1.setData(X, self.picoharp_histograms[:ii, :].sum(axis=1)/self.picoharp_elapsed_time[:ii])
        elif self.settings['collect_spectrum']:
            self.plot_line1.setData(X, self.integrated_spectra[:ii])
            self.winspec_readout.update_display()
        elif self.settings['collect_ascom_img']:
            self.plot_line1.setData(X, self.ascom_img_integrated[:ii])
            self.ascom_camera_capture.update_display()
        else: # no detectors set, show pm_powers
            self.plot_line1.setData(X, self.pm_powers[:ii])


    def run(self):
        self.spec_readout_measure_name = 'andor_ccd_readout'

        # hardware and delegate measurements
        #self.power_wheel_hw = self.app.hardware.power_wheel_arduino
        #self.power_wheel_dev = self.power_wheel_hw.power_wheel_dev
        self.power_wheel_hw = self.app.hardware['power_wheel']
        
        if self.settings['collect_apd']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.count_rate     

        if self.settings['collect_lifetime']:
            self.ph_hw = self.app.hardware['picoharp']

        if self.settings['collect_spectrum']:
            self.spec_readout = self.app.measurements[self.spec_readout_measure_name]
                   
        if self.settings['collect_ascom_img']:
            self.ascom_camera_capture = self.app.measurements.ascom_camera_capture
            self.ascom_camera_capture.settings['continuous'] = False
            
            
        
        #####
        self.Np = Np = self.power_wheel_ndatapoints.val
#        self.step_size = int( (self.power_wheel_max.val-self.power_wheel_min.val)/Np )
        
        self.power_wheel_position = np.linspace(self.settings['power_wheel_min'], self.settings['power_wheel_max'], self.Np)
        self.step_size = self.power_wheel_position[1] - self.power_wheel_position[0]
    
        if self.settings['up_and_down_sweep']:
            self.direction = np.ones(Np*2) # step up
            self.direction[Np] = 0 # don't step at the top!
            self.direction[Np+1:] = -1 # step down
            Np = self.Np = 2*Np
            
            self.power_wheel_position = np.concatenate([self.power_wheel_position, self.power_wheel_position[::-1]])
            
        else:
            self.direction = np.ones(Np)
    
        # Create Data Arrays    
        #self.power_wheel_position = np.zeros(Np, dtype=float)      

        
        self.pm_powers = np.zeros(Np, dtype=float)
        self.pm_powers_after = np.zeros(Np, dtype=float)

        if self.settings['collect_apd']:
            self.apd_count_rates = np.zeros(Np, dtype=float)
        if self.settings['collect_lifetime']:
            Nt = self.num_hist_chans = self.ph_hw.calc_num_hist_chans()
            self.picoharp_time_array = np.zeros(Nt, dtype=float)
            self.picoharp_elapsed_time = np.zeros(Np, dtype=float)
            self.picoharp_histograms = np.zeros((Np,Nt ), dtype=int)
        if self.settings['collect_spectrum']:
            self.spectra = [] # don't know size of ccd until after measurement
            self.integrated_spectra = []
        if self.settings['collect_ascom_img']:
            self.ascom_img_stack = []
            self.ascom_img_integrated = []
            
        
        ### Acquire data
        
        self.move_to_min_pos()
        
        self.ii = 0
        
        # loop through power wheel positions
        for ii in range(self.Np):
            self.ii = ii
            self.settings['progress'] = 100.*ii/self.Np
            
            if self.interrupt_measurement_called:
                break
            
            # record power wheel position
            #self.power_wheel_position[ii] = self.power_wheel_hw.encoder_pos.read_from_hardware()
            #self.power_wheel_hw.settings.raw_position.read_from_hardware()
            self.power_wheel_hw.settings['position'] = self.power_wheel_position[ii]
            print("moving power wheel", "now at ", self.power_wheel_hw.settings['position'])
            time.sleep(0.050)

            
            # collect power meter value
            self.pm_powers[ii]=self.collect_pm_power_data()
            
            # read detectors
            if self.settings['collect_apd']:
                time.sleep(self.apd_counter_hw.settings['int_time'])
                self.apd_count_rates[ii] = \
                    self.apd_counter_hw.settings.count_rate.read_from_hardware()
                
            if self.settings['collect_lifetime']:
                ph = self.ph_hw.picoharp
                ph.start_histogram()
                while not ph.check_done_scanning():
                    if self.interrupt_measurement_called:
                        break
                    ph.read_histogram_data()
                    self.ph_hw.settings.count_rate0.read_from_hardware()
                    self.ph_hw.settings.count_rate1.read_from_hardware()
                    time.sleep(0.1)        
                ph.stop_histogram()
                ph.read_histogram_data()
                self.picoharp_histograms[ii,:] = ph.histogram_data[0:Nt]
                self.picoharp_time_array =  ph.time_array[0:Nt]
                self.picoharp_elapsed_time[ii] = ph.read_elapsed_meas_time()
            if self.settings['collect_spectrum']:
                self.spec_readout.run()
                spec = np.array(self.spec_readout.spectrum)
                self.spectra.append( spec )
                self.integrated_spectra.append(spec.sum())
            if self.settings['collect_ascom_img']:
                self.ascom_camera_capture.interrupt_measurement_called = False
                self.ascom_camera_capture.run()
                img = self.ascom_camera_capture.img.copy()
                self.ascom_img_stack.append(img)
                self.ascom_img_integrated.append(img.astype(float).sum())
                
                
            # collect power meter value after measurement
            self.pm_powers_after[ii]=self.collect_pm_power_data()

            # move to new power wheel position
            #self.power_wheel_dev.write_steps_and_wait(self.step_size*self.direction[ii])
            #time.sleep(0.5)
            #self.power_wheel_hw.encoder_pos.read_from_hardware()
            #delta = self.step_size*self.direction[ii]
            #print("moving power wheel", delta)
            #self.power_wheel_hw.settings['position'] += delta
            #print("moving power wheel", delta, "now at ", self.power_wheel_hw.settings['position'])
            
            
        # write data to h5 file on disk
        
        self.t0 = time.time()
        #self.fname = "%i_%s.h5" % (self.t0, self.name)
        #self.h5_file = h5_io.h5_base_file(self.app, self.fname )
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
            #create h5 data arrays
    
            if self.settings['collect_apd']:
                H['apd_count_rates'] = self.apd_count_rates
            if self.settings['collect_lifetime']:
                H['picoharp_elapsed_time'] = self.picoharp_elapsed_time
                H['picoharp_histograms'] = self.picoharp_histograms
                H['picoharp_time_array'] = self.picoharp_time_array
            if self.settings['collect_spectrum']:
                H['wls'] = self.spec_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            if self.settings['collect_ascom_img']:
                H['ascom_img_stack'] = np.array(self.ascom_img_stack)
                H['ascom_img_integrated'] = np.array(self.ascom_img_integrated)
                
            H['pm_powers'] = self.pm_powers
            H['pm_powers_after'] = self.pm_powers_after
            H['power_wheel_position'] = self.power_wheel_position
            H['direction'] = self.direction
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
        


        """    def move_to_min_pos(self):
        self.power_wheel_dev.read_status()
        
        delta_steps = self.power_wheel_min.val - self.power_wheel_hw.encoder_pos.read_from_hardware()
        if delta_steps != 0:
            #print 'moving to min pos'
            self.power_wheel_dev.write_steps_and_wait(delta_steps)
            #print 'done moving to min pos'
"""
    def move_to_min_pos(self):
        self.power_wheel_hw.settings['position'] = self.settings['power_wheel_min']
        time.sleep(2.0)
    
    def collect_pm_power_data(self):
        PM_SAMPLE_NUMBER = 10

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power = 0.0
        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called: break
            try_count = 0
            #print "samp", ii, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    pm_power = pm_power + self.app.hardware['thorlabs_powermeter'].power.read_from_hardware(send_signal=True)
                    samp_count = samp_count + 1
                    break 
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > 9:
                        print("failed to collect power meter sample:", err)
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power = pm_power/samp_count
        else:
            print("  Failed to read power")
            pm_power = 10000.  

        
        return pm_power    
