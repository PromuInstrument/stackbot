from ScopeFoundry import Measurement
import numpy as np
import time
from ScopeFoundry import h5_io
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg
from matplotlib.backends.qt_compat import QtWidgets
from ScopeFoundry.logged_quantity import LQRange
from _operator import pos

class PowerScanMeasure(Measurement):
    
    name = 'power_scan'
    
    def __init__(self, app, shutter_open_lq_path = None):
        self.ui_filename = sibling_path(__file__, "power_scan.ui")
        Measurement.__init__(self, app)
        if shutter_open_lq_path != None:
            self.shutter_open = app.lq_path(shutter_open_lq_path)
        
    def setup(self):
               
        self.power_wheel_range = self.settings.New_Range('power_wheel', include_sweep_type = True,
                                                         initials = [0, 280, 28])
        self.power_wheel_range.sweep_type.update_value('up_down')
        self.acq_mode = self.settings.New('acq_mode', dtype=str, initial = 'const_time', 
                                          choices=('const_time', 'const_dose', 'manual_acq_times'))

                                               
        #possible hardware components and their integration times setting:
        self.hws = { 'picoharp': 'Tacq',
                     'hydraharp': 'Tacq',
                     'ascom_img': 'exp_time',
                     'andor_ccd': 'exposure_time',
                     'winspec_remote_client': 'acq_time', 
                     'apd_counter': 'int_time',}
                
        for key in self.hws.keys():
            self.settings.New('collect_{}'.format(key), dtype=bool, initial=False)
        
        self.settings.New("x_axis", dtype=str, initial='pm_power', 
                                        choices=('power_wheel_positions', 'power'))
        self.settings.New('use_shutter', dtype=bool, initial=True)
        
            
    def setup_figure(self):
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.x_axis.connect_to_widget(self.ui.x_axis_comboBox)
        self.settings.x_axis.add_listener(self.update_display)
        self.acq_mode.connect_to_widget(self.ui.acq_mode_comboBox)
        
        if hasattr(self, 'shutter_open'):
            CB_widget = QtWidgets.QCheckBox('use shutter')
            self.settings.use_shutter.connect_to_widget(CB_widget)
            self.ui.gridGroupBox.layout().addWidget(CB_widget)
        else:
            self.settings['use_shutter'] = False
            self.settings.use_shutter.change_readonly(True)            

        self.power_wheel_range.min.connect_to_widget(self.ui.power_wheel_min_doubleSpinBox)
        self.power_wheel_range.max.connect_to_widget(self.ui.power_wheel_max_doubleSpinBox)
        self.power_wheel_range.num.connect_to_widget(self.ui.power_wheel_num_doubleSpinBox)
        self.power_wheel_range.step.connect_to_widget(self.ui.power_wheel_step_doubleSpinBox)
        self.power_wheel_range.sweep_type.connect_to_widget(self.ui.sweep_type_comboBox)

        # Hardware connections
        layout = self.ui.collect_groupBox.layout()
        hw_list = self.app.hardware.keys()
        self.installed_hw = {}
        
        for key in self.hws.keys():
            if key in hw_list:
                CB_widget = QtWidgets.QCheckBox(key)
                lq = getattr(self.settings, 'collect_{}'.format(key))
                lq.connect_to_widget(CB_widget)

                SP_widget = QtWidgets.QDoubleSpinBox()                
                Tacq_lq = getattr(self.app.hardware[key].settings, self.hws[key])
                Tacq_lq.connect_to_widget(SP_widget)
                
                layout.addRow(CB_widget, SP_widget)
                
                self.installed_hw.update({key: Tacq_lq})
        
                
            
        # Plot
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        self.plot1 = self.graph_layout.addPlot(title="Power Scan")
        self.display_ready = False



    def pre_run(self):
        
        self.display_ready = False
        
        # Prepare data arrays and links to components:
        self.power_wheel_position = self.power_wheel_range.sweep_array
        self.Np = Np = len(self.power_wheel_position)

        self.pm_powers = np.zeros(Np, dtype=float)
        self.pm_powers_after = np.zeros(Np, dtype=float)
        
        self.power_wheel_hw = self.app.hardware['power_wheel']
        self.power_wheel_hw.settings['connected'] = True
        self.pm_hw = self.app.hardware['thorlabs_powermeter']
        self.pm_hw.settings['connected'] = True        
        
        self.used_hws = {}
        
        if self.settings['collect_apd_counter']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.count_rate            
            self.apd_count_rates = np.zeros(Np, dtype=float)
            self.used_hws.update( {'apd_counter':self.installed_hw['apd_counter']} )
            
        if self.settings['collect_picoharp']:
            self.ph_hw = self.app.hardware['picoharp']
            self.ph_hw.settings['connected'] = True
            Nt = self.ph_hw.settings['histogram_channels']
            self.picoharp_time_array = np.zeros(Nt, dtype=float)
            self.picoharp_elapsed_time = np.zeros(Np, dtype=float)
            self.picoharp_histograms = np.zeros((Np,Nt ), dtype=int)
            self.used_hws.update( {'picoharp':self.installed_hw['picoharp']} )
            
        if self.settings['collect_hydraharp']:
            self.hh_hw = self.app.hardware['hydraharp']
            self.hh_hw.update_HistogramBins()
            self.hh_hw.settings['connected'] = True
            shape = self.hh_hw.hist_shape
            self.hydraharp_time_array = np.zeros(shape[-1], dtype=float)
            self.hydraharp_elapsed_time = np.zeros(Np, dtype=float)
            self.hydraharp_histograms = np.zeros((Np,)+shape, dtype=int)
            self.used_hws.update( {'hydraharp':self.installed_hw['hydraharp']} )

        #TODO: Can not currently take spectra from different cameras
        if self.settings['collect_winspec_remote_client']:
            self.spec_readout = self.app.measurements['winspec_remote_client']
            self.spectra = [] # don't know size of ccd until after measurement
            self.integrated_spectra = []
            self.used_hws.update( {'winspec_remote_client':self.installed_hw['winspec_remote_client']} )

        if self.settings['collect_andor_ccd']:
            self.spec_readout = self.app.measurements['collect_andor_ccd']
            self.spectra = [] # don't know size of ccd until after measurement
            self.integrated_spectra = []
            self.used_hws.update( {'andor_ccd':self.installed_hw['andor_ccd']} )

        if self.settings['collect_ascom_img']:
            self.ascom_camera_capture = self.app.measurements.ascom_camera_capture
            self.ascom_camera_capture.settings['continuous'] = False
            self.ascom_img_stack = []
            self.ascom_img_integrated = []
            self.used_hws.update( {'ascom_img':self.installed_hw['ascom_img']} )


        # Prepare for different acquisition modes        
        #if self.settings['acq_mode'] == 'const_SNR':
        #    self.spec_acq_times_array = self.spec_acq_time.val / np.exp(2*self.log_power_index)
        #    self.lifetime_acq_times_array = self.lifetime_acq_time.val / np.exp(2*self.log_power_index) 

        if self.settings['use_shutter']:
            self.shutter_open.update_value(True)
            
            
        total_acquisition_time = 0
        self.Tacq_arrays = [] 
        
        if self.settings['acq_mode'] == 'const_dose':
            self.dose_calibration_data = self.acquire_dose_calibration_data()
            for hw,Tacq_lq in self.used_hws.items():
                acq_time_array = self.calc_times_const_dose_calibrated(Tacq_lq.val, self.dose_calibration_data)
                self.Tacq_arrays.append( (hw, Tacq_lq, acq_time_array) )
                print(hw, 'acquisition time', acq_time_array.sum())
                total_acquisition_time += acq_time_array.sum()
        
        elif self.settings['acq_mode'] == 'manual_acq_times':    
            #list of (p,t) where p is the lowest position with acquisition time t
            #Note: all hw will us the same list
            #Not tested for zigzak sweep
            
            pos_vs_acqtime = [(0,5),(260,4),(120,3),(200,2)] 
            
            for hw,Tacq_lq in self.used_hws.items():
                acq_time_array = self.calc_acq_time_array_manual_input(pos_vs_acqtime)
                self.Tacq_arrays.append( (hw, Tacq_lq, acq_time_array) )    
                total_acquisition_time += acq_time_array.sum()      
        
        elif self.settings['acq_mode'] == 'const_time': 
            for hw,Tacq_lq in self.used_hws.items():
                acq_time_array = np.ones_like(self.power_wheel_position) * Tacq_lq.val #easy peasy const time array.
                self.Tacq_arrays.append( (hw, Tacq_lq, acq_time_array) )
                total_acquisition_time += acq_time_array.sum()      
        
        print(self.name, self.settings['acq_mode'], 'total_acquisition_time (s)', total_acquisition_time)
                    
        self.ii = 0

        # prepare plot curves
        self.plot1.clear()
        self.plot_lines = []
        N_plot_lines = len(self.used_hws.keys())
        for i in range(N_plot_lines):
            c = (i+1)/N_plot_lines
            self.plot_lines.append(self.plot1.plot([0], symbol='o', pen=(c,c,c)))
        self.plot1.setTitle('Power Scan')
        self.display_ready = True

        

            
    def post_run(self):
        self.display_ready = False
        if self.settings['use_shutter']:
            self.shutter_open.update_value(False)        

    def run(self):
        if len(self.used_hws) == 0: 
            print('Nothing selected to collect data from.')
            self.interrupt_measurement_called = True #self.interrupt() #This causes problems?
            
        self.move_to_min_pos()
                
        # loop through power wheel positions and measure active components.
        for ii in range(self.Np):
            self.ii = ii
            self.settings['progress'] = 100.*ii/self.Np
            if self.interrupt_measurement_called:
                break
                        
            for hw, Tacq_lq, Tacq_array in self.Tacq_arrays:
                print("power scan {} of {}, {} acq_time {}".format(ii + 1, self.Np, hw, Tacq_array[ii]))
                Tacq_lq.update_value(Tacq_array[ii])


            print("moving power wheel to", self.power_wheel_hw.settings['position'])            
            self.power_wheel_hw.settings['position'] = self.power_wheel_position[ii]
            time.sleep(0.25)

            
            # collect power meter value
            self.pm_powers[ii]=self.collect_pm_power_data()
            
            
            # read detectors
            if self.settings['collect_apd_counter']:
                time.sleep(self.apd_counter_hw.settings['int_time'])
                self.apd_count_rates[ii] = \
                    self.apd_counter_hw.settings.count_rate.read_from_hardware()
                
                
            if self.settings['collect_picoharp']:
                ph = self.ph_hw.picoharp
                ph.start_histogram()
                while not ph.check_done_scanning():
                    if self.interrupt_measurement_called:
                        break
                    ph.read_histogram_data()
                    time.sleep(0.1)        
                ph.stop_histogram()
                ph.read_histogram_data()
                Nt = self.ph_hw.settings['histogram_channels']
                self.picoharp_elapsed_time[ii] = ph.read_elapsed_meas_time()
                self.picoharp_histograms[ii,:] = ph.histogram_data[0:Nt]
                self.picoharp_time_array =  ph.time_array[0:Nt]
                
                
            if self.settings['collect_hydraharp']:
                self.hydraharp_histograms[ii,:] = self.aquire_histogram(self.hh_hw)
                self.hydraharp_time_array = self.hh_hw.sliced_time_array
                self.hydraharp_elapsed_time[ii] = self.hh_hw.settings['ElapsedMeasTime']
                
                
            if self.settings['collect_winspec_remote_client']:
                #self.spec_readout.run()
                self.spec_readout.settings['read_single'] = True
                self.spec_readout.settings['save_h5'] = True
                
                self.spec_readout.settings['activation'] = True
                time.sleep(0.5)
                time.sleep(self.spec_acq_time.val)
                spec = np.array(self.spec_readout.spectrum)
                self.integrated_spectra.append(spec.sum())/self.spec_readout.settings['acq_time'] 
                self.spec_readout.settings['read_single'] = True
                
                
            if self.settings['collect_andor_ccd']:
                #self.spec_readout.run()
                self.spec_readout.settings['read_single'] = True
                self.spec_readout.settings['save_h5'] = True
                #self.start_nested_measure_and_wait(self.spec_readout)
                
                self.spec_readout.settings['activation'] = True
                time.sleep(0.5)
                time.sleep(self.spec_acq_time.val)
                spec = np.array(self.spec_readout.spectrum)
                spec = spec/self.spec_readout.settings['exposure_time'] 
                self.spectra.append(spec)
                self.integrated_spectra.append(spec.sum())
                self.spec_readout.settings['read_single'] = True
                                
                                
            if self.settings['collect_ascom_img']:
                self.ascom_camera_capture.interrupt_measurement_called = False
                self.ascom_camera_capture.run()
                img = self.ascom_camera_capture.img.copy()/self.ascom_camera_capture.settings['exp_time']
                self.ascom_img_stack.append(img)
                self.ascom_img_integrated.append(img.astype(float).sum())
                
                
            # collect power meter value after measurement
            self.pm_powers_after[ii]=self.collect_pm_power_data()

            

        # write data to h5 file on disk        
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)    
            if self.settings['collect_apd_counter']:
                H['apd_count_rates'] = self.apd_count_rates
            if self.settings['collect_picoharp']:
                H['picoharp_elapsed_time'] = self.picoharp_elapsed_time
                H['picoharp_histograms'] = self.picoharp_histograms
                H['picoharp_time_array'] = self.picoharp_time_array
            if self.settings['collect_hydraharp']:
                H['hydraharp_elapsed_time'] = self.hydraharp_elapsed_time
                H['hydraharp_histograms'] = self.hydraharp_histograms
                H['hydraharp_time_array'] = self.hydraharp_time_array                
            if self.settings['collect_winspec_remote_client']:
                H['wls'] = self.spec_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            if self.settings['collect_andor_ccd']:
                H['wls'] = self.spec_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)
            if self.settings['collect_ascom_img']:
                H['ascom_img_stack'] = np.array(self.ascom_img_stack)
                H['ascom_img_integrated'] = np.array(self.ascom_img_integrated)
                
            H['pm_powers'] = self.pm_powers
            H['pm_powers_after'] = self.pm_powers_after
            H['power_wheel_position'] = self.power_wheel_position
            
            for hw, Tacq_lq, acq_time_array in self.Tacq_arrays:
                H[hw + '_acquisition_times'] = acq_time_array
                print('saving ' + hw + '_acquisition_times')
                
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
        

        self.update_display()
        

    def update_display(self):

        if self.display_ready:
        
            ii = self.ii + 1
            if self.settings['x_axis'] == 'power':
                X = self.pm_powers[:ii]            
            else:
                X = self.power_wheel_position[:ii]

            jj = 0          
            if self.settings['collect_apd_counter']:
                self.plot_lines[jj].setData(X, self.apd_count_rates[:ii])
                jj += 1
                
            if self.settings['collect_picoharp']:
                self.plot_lines[jj].setData(X, self.picoharp_histograms[:ii, :].sum(axis=1)/self.picoharp_elapsed_time[:ii])
                jj += 1
    
            if self.settings['collect_hydraharp']:
                Y = self.hydraharp_histograms[:ii].sum(axis=(1,2))/self.hydraharp_elapsed_time[:ii]
                self.plot_lines[jj].setData(X,Y)
                #print('update_display', ii, X, self.hydraharp_histograms[:ii].sum(axis=(1,2)))
                jj += 1
    
            elif self.settings['collect_andor_ccd']:
                self.plot_lines[jj].setData(X, self.integrated_spectra[:ii])
                jj += 1
    
            elif self.settings['collect_winspec_remote_client']:
                self.plot_lines[jj].setData(X, self.integrated_spectra[:ii])
                jj += 1
    
            elif self.settings['collect_ascom_img']:
                self.plot_lines[jj].setData(X, self.ascom_img_integrated[:ii])
                self.ascom_camera_capture.update_display()
                jj += 1
        
            else: # no detectors set, show pm_powers
                self.plot1.setTitle('No Detector')


    def aquire_histogram(self, hw): 
        hw.start_histogram()
        while not hw.check_done_scanning():
            if self.interrupt_measurement_called:
                break
            self.hist_data = np.array(hw.read_histogram_data(clear_after=False) )
            time.sleep(5e-3)
        hw.stop_histogram()
        self.hist_data = np.array(hw.read_histogram_data(clear_after=True))

        print(self.hist_data.shape, hw.hist_slice)
        hist_data = self.hist_data[hw.hist_slice]

        print('aquire_histogram', hw.name, hist_data.sum())
        return hist_data


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
                    pm_power = pm_power + self.pm_hw.power.read_from_hardware(send_signal=True)
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

    
    def acquire_dose_calibration_data(self):
        print('calibrating dose')
        dose_calibration_data = np.zeros_like(self.power_wheel_position)        
        for ii,pos in enumerate(self.power_wheel_position):
            self.power_wheel_hw.settings['position'] = pos
            time.sleep(0.20)
            dose_calibration_data[ii] = self.collect_pm_power_data()
            time.sleep(0.20)
        return dose_calibration_data
    
            
    def calc_times_const_dose_calibrated(self, t0, dose_calibration_data):
        '''predicts the acq times needed to have the same dose at every wheel position 
        based on calibration data'''
        dose = dose_calibration_data[0] * t0 #this the targed dose.
        print('calc_times_const_dose_calibrated() dose is:', dose)
        acq_times_array =  np.array([round(item,4) for item in dose/dose_calibration_data]) 
        return acq_times_array


    def calc_times_const_dose_specs(self, t0, OD_MAX = 4.3 ,OD_MAX_POS = 270.):
        '''predicts the acq times needed to have the same dose at every wheel position 
        based on specification of the power wheel'''
        theta = self.power_wheel_position
        OD = OD_MAX * (theta - theta[0]) / OD_MAX_POS         
        acq_times_array = np.array([round(item,4) for item in (t0 * 10**(-OD))])
        print('Estimated time {}'.format(np.sum(acq_times_array)))
        return acq_times_array
        

    def calc_acq_time_array_manual_input(self, manual_pos_vs_times):
        pos,time = np.array(manual_pos_vs_times).T
        x = self.power_wheel_position
        # lowest position
        assert len(x) >= 2
        acq_time_array =  np.piecewise(x, [x < pos[1],   x >= pos[1]], [ time[0], 0]) 
        # highest position
        acq_time_array += np.piecewise(x, [x >= pos[-1], x < pos[-1]], [time[-1], 0])
        # all other
        for i in range(1,len(pos)-1):
            t = np.piecewise(x, [x < pos[i], x >= pos[i], x >= pos[i+1]], [0, time[i], 0])
            acq_time_array += t    
        return acq_time_array
    