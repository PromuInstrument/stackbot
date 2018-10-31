from ScopeFoundry import Measurement
from ScopeFoundry import h5_io

import numpy as np
import time
class PowerScanMapMeasurement(Measurement):
    
    name = 'power_scan_maps'
    
    def setup(self):
        self.power_wheel_min = self.settings.New("power_wheel_min", 
                                                          dtype=int, unit='', initial=0, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_max = self.settings.New("power_wheel_max", 
                                                          dtype=int, unit='', initial=1000, vmin=-3200, vmax=+3200, ro=False)
        self.power_wheel_ndatapoints = self.settings.New("power_wheel_ndatapoints", 
                                                          dtype=int, unit='', initial=100, vmin=1, vmax=3200, ro=False)
        self.power_wheel_laser_autofocus = self.settings.New('laser_autofocus_power_wheel_position', dtype = int, unit = '', initial = 0)
        
        self.up_and_down_sweep    = self.settings.New("up_and_down_sweep",dtype=bool, initial=True)

        self.settings.New('map_type', dtype=str,
                          choices=('APD_MCL_2DSlowScan', 'Picoharp_MCL_2DSlowScan', 'WinSpecMCL2DSlowScan'), initial='APD_MCL_2DSlowScan')
        self.settings.New('laser_camera_exposure', dtype=float, unit='s', initial=0.1)
        self.settings.New('PL_camera_exposure', dtype=float, unit='s', initial=60.0)
        self.settings.New('picoharp_exposure', dtype=float, unit='s', initial=60)
        self.settings.New('depth_scan_magnitude', dtype=float, unit='um', initial=2.0)
        self.settings.New('depth_scan_stepsize', dtype=float, unit='um', initial=2.0)
#         self.settings.New('2D_map_x_min', dtype=float, unit='um', initial=20)
#         self.settings.New('2D_map_x_max', dtype=float, unit='um', initial=35)
#         self.settings.New('2D_map_y_min', dtype=float, unit='um', initial=20)
#         self.settings.New('2D_map_y_max', dtype=float, unit='um', initial=35)
#         self.settings.New('2D_map_x_stepSize', dtype=float, unit='um', initial=0.5)
#         self.settings.New('2D_map_y_stepSize', dtype=float, unit='um', initial=0.5)
        
                
    def run(self):
        
        """ Loop through excitation powers (ii)
                Autofocus
                Loop through depths (jj)
                    Move Z
                    PL image
                    Laser image
                    Map Scan
                    Single TRPL measurement
                    """
                    
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        self.h5_file.attrs['time_id'] = self.t0
        H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)

        
        # hardware and delegate measurements
        self.power_wheel_hw = self.app.hardware.power_wheel_arduino
        self.power_wheel_dev = self.power_wheel_hw.power_wheel_dev
        stage = self.app.hardware['mcl_xyz_stage']
        
        map_measure = self.app.measurements[self.settings['map_type']]
        map_measure.interrupt_measurement_called = False
        
        cameraHW = self.app.hardware['ascom_camera']
        camera = self.app.measurements['ascom_camera_capture']
        picoharpHW = self.app.hardware['picoharp']
        picoharp_measurement = self.app.measurements['picoharp_histogram']
        
        ELLIPTEC_PL_FILTER_POS = 0
        ELLIPTEC_OD4_LASER_POS = 32

        LASER_IN_SHUTTER_CLOSED_POS = 1        
        LASER_IN_SHUTTER_OPEN_POS   = 25
        
        ### Define number of depth slices
        Stepsize = self.settings['depth_scan_stepsize']
        Depth = self.settings['depth_scan_magnitude']
        self.rel_z_array = np.arange(0, Depth, Stepsize) 
        self.NSlices = len(self.rel_z_array)
        H['rel_z_array'] = self.rel_z_array
        
        ### Define number of power steps (same as number of maps)
        self.Np = Np = self.power_wheel_ndatapoints.val
        self.step_size = int( (self.power_wheel_max.val-self.power_wheel_min.val)/Np )

        if self.settings['up_and_down_sweep']:
            self.direction = np.ones((Np*2)+1) # step up
            self.direction[Np] = 0 # don't step at the top!
            self.direction[Np+1:] = -1 # step down
            Np = self.Np = (2*Np)+1
        else:
            self.direction = np.ones(Np)
                    
        ### Create Data Arrays    
        self.power_wheel_position = np.zeros(Np)      
        self.pm_powers = H.create_dataset('pm_powers', (Np, ), dtype=float) #np.zeros(Np, dtype=float)
        self.pm_powers_after = H.create_dataset('pm_powers_after', (Np,), dtype=float) 
        H['power_wheel_position'] = self.power_wheel_position
        H['direction'] = self.direction
        
        ## Picoharp data arrays 
        
        # make sure you acquire one histogram using picoharp_histogram_measurement
        trpl_array_shape = (Np, self.NSlices, picoharpHW.settings['histogram_channels'])   
        self.trpl_histograms = H.create_dataset('trpl_histograms', trpl_array_shape, dtype=float)
        self.trpl_elapsed_time = H.create_dataset('trpl_elapsed_time', trpl_array_shape[:-1], dtype=float)
        
        ## image data arrays

        img_array_shape =(Np, self.NSlices, cameraHW.settings['NumY'], cameraHW.settings['NumX'])
        self.pl_images = H.create_dataset('pl_images', img_array_shape, dtype=float)
        self.laser_images = H.create_dataset('laser_images', img_array_shape, dtype=float)
        
        ## trpl map data arrays
        
        #self.Nx = (self.settings['2D_map_x_max'] - self.settings['2D_map_x_min'])/self.settings['2D_map_x_stepSize']
        #self.Ny = (self.settings['2D_map_y_max'] - self.settings['2D_map_y_min'])/self.settings['2D_map_y_stepSize']
        #self.Nx = int(round(self.Nx))
        #self.Ny = int(round(self.Ny))
        
        
        ### Start measurement:

        #close shutter
        self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_CLOSED_POS
        time.sleep(0.1)        
        
        # move power wheel to start
        self.move_to_min_pos()
        
        # set SP filter to block the laser (and detect only the PL):
        self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_PL_FILTER_POS
        time.sleep(0.1)

        # open shutter
        self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_OPEN_POS        
        time.sleep(0.1)
        
        # EMPIRICAL: define integration time array
        #intTime = [60, 30, 10, 1, 0.1]
        intTime = [20, 10, 5]
        #powerwheel: [300, ..., 650, 700, 750, 800]
        
        # loop over powers
        for ii in range(Np):
            
            if self.interrupt_measurement_called:
                break
            
            # record power wheel position
            self.power_wheel_position[ii] = self.power_wheel_hw.encoder_pos.read_from_hardware()
            
            # change integration time depending on excitation power
            wheelPos = self.power_wheel_position[ii]
            
            '''
            if (wheelPos < 650):
                self.settings['PL_camera_exposure'] = intTime[0]
                self.settings['picoharp_exposure'] = intTime[0]
            if (np.abs(wheelPos-650) < 20):
                self.settings['PL_camera_exposure'] = intTime[1]
                self.settings['picoharp_exposure'] = intTime[1]
            if (np.abs(wheelPos-700) < 20):
                self.settings['PL_camera_exposure'] = intTime[2]
                self.settings['picoharp_exposure'] = intTime[2]
            if (np.abs(wheelPos-750) < 20):
                self.settings['PL_camera_exposure'] = intTime[3]
                self.settings['picoharp_exposure'] = intTime[3]
            if (np.abs(wheelPos-800) < 20):
                self.settings['PL_camera_exposure'] = intTime[4]
                self.settings['picoharp_exposure'] = intTime[4]
            '''
            '''
            if (np.abs(wheelPos-950) < 20):
                self.settings['PL_camera_exposure'] = intTime[1]
                self.settings['picoharp_exposure'] = intTime[1]
                '''
                
            '''   
            if (np.abs(wheelPos-800) < 20):
                self.settings['PL_camera_exposure'] = intTime[1]
                self.settings['picoharp_exposure'] = intTime[1]
            if (np.abs(wheelPos-850) < 15):
                self.settings['PL_camera_exposure'] = intTime[1]
                self.settings['picoharp_exposure'] = intTime[1]
            if (np.abs(wheelPos-900) < 15):               
                self.settings['PL_camera_exposure'] = intTime[2]
                self.settings['picoharp_exposure'] = intTime[2]
            if (np.abs(wheelPos-950) < 15):
                self.settings['PL_camera_exposure'] = intTime[3]
                self.settings['picoharp_exposure'] = intTime[3]
            '''
                
            if (wheelPos < 1020):
                self.settings['picoharp_exposure'] = 20
            else:
                self.settings['picoharp_exposure'] = 4
            '''
            elif (wheelPos < 80):
                self.settings['picoharp_exposure'] = 10                             
            elif (wheelPos > 80):
                self.settings['picoharp_exposure'] = 5
            '''
            # collect power meter value
            self.pm_powers[ii]=self.collect_pm_power_data()
            
            ## run autofocus
            # Old version:
            ##go first to the max power (for better alignment signal):
            #self.power_wheel_dev.write_absolute_position_and_wait(self.power_wheel_max.val)
            # New version:
            #close shutter
            self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_CLOSED_POS 
            time.sleep(0.1)  
            # go first to the optimum power (about 10kHz on APD):
            self.power_wheel_dev.write_absolute_position_and_wait(self.power_wheel_laser_autofocus.val)
            #self.power_wheel_dev.write_absolute_position_and_wait(0)
            # send laser to APD through OD4 filter:
            self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_OD4_LASER_POS
            time.sleep(0.1)
            # OPEN  shutter
            self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_OPEN_POS
            time.sleep(0.1)        

            # autofocus
            self.log.info('autofocus started')
            autofocus = self.app.measurements['auto_focus']
            autofocus.interrupt_measurement_called = False
            autofocus.start()
            time.sleep(0.1)
            while( autofocus.is_measuring()):
                #print('waiting for autofocus')
                if self.interrupt_measurement_called:
                    autofocus.interrupt()
                time.sleep(0.1)
            # go back to the right filter (SP to block the laser):
            self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_PL_FILTER_POS
            time.sleep(0.1)
            # go back to the right power for the measurement:
            self.power_wheel_dev.write_absolute_position_and_wait(self.power_wheel_position[ii])
            self.log.info('autofocus complete')
            
            #Record depth:
            original_z = stage.settings['z_target']
            
            # loop through depths
            for jj, rel_z in enumerate(self.rel_z_array):
                
                self.settings['progress'] = 100.*(ii+jj/self.NSlices)/self.Np
                
                if self.interrupt_measurement_called:
                    break

                
                # set z to z_target - rel_z            
                #stage.settings['z_target'] += Stepsize
                #if stage.settings['z_target'] - original_z >= Depth:
                #    depthScanComplete = True
                
                #autofocus here to find original_z

                ############ move stage to correct depth
                stage.settings['z_target'] = original_z + rel_z

                ############ take image of the PL on ascom camera:
                
                if False:
                    # switch to camera using flip mirror:
                    self.app.hardware['flip_mirrors'].settings['apd_flip'] = False
                    self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_PL_FILTER_POS
                    time.sleep(1)
                    self.log.info('switched to ascom camera')
                    # change camera's integration time:
                    cameraHW.settings['exp_time'] = self.settings['PL_camera_exposure']
                    # record image:
                    camera.interrupt_measurement_called = False
                    camera.start()
                    time.sleep(0.1)
                    self.log.info('recording PL image')
                    while( camera.is_measuring()):
                        #print('waiting for camera')
                        if self.interrupt_measurement_called:
                            camera.interrupt()
                        time.sleep(0.1)
                    time.sleep(0.1)
                    self.pl_images[ii,jj,:,:] = camera.img.T

                ############## record image of the laser on ascom camera:
                
                if False:
                    # change camera's integration time:
                    cameraHW.settings['exp_time'] = self.settings['laser_camera_exposure']
                    # send laser to APD through OD4 filter:
                    self.app.hardware['flip_mirrors'].settings['apd_flip'] = False
                    self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_OD4_LASER_POS
                    time.sleep(0.1)            
                    # start acquisition:
                    camera.start()
                    time.sleep(0.1)
                    self.log.info('recording laser image')
                    while( camera.is_measuring()):
                        #print('waiting for camera')
                        if self.interrupt_measurement_called:
                            camera.interrupt()
                        time.sleep(0.1)
                    time.sleep(0.1)
                    self.laser_images[ii,jj,:,:] = camera.img.T
                
                ############ switch back to apd:
                self.app.hardware['flip_mirrors'].settings['apd_flip'] = True
                self.log.info('switched back to apd')
                time.sleep(1)
                
                ############# reset apd:
                apd = self.app.hardware['apd_counter']
                apd.disconnect()
                time.sleep(0.1)
                apd.connect()
                
                ############## start single trpl measurement:
                if False:    
                    # change acquisition time:
                    picoharpHW.settings['Tacq'] = self.settings['picoharp_exposure']
                    self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_PL_FILTER_POS
                    time.sleep(0.1)
                    #picoharp_measurement.interrupt_measurement_called = False
                    picoharp_measurement.start()
                    time.sleep(0.1)
                    self.log.info('recording trpl histogram')
                    while(picoharp_measurement.is_measuring()):
                        #print('waiting for picoharp')
                        if self.interrupt_measurement_called:
                            picoharp_measurement.interrupt()
                        time.sleep(0.1)
                    time.sleep(0.1)
                    Nhist = picoharpHW.settings['histogram_channels']
                    histogram_data = picoharp_measurement.ph.histogram_data[:Nhist]
                    self.trpl_histograms[ii,jj,:] = histogram_data
                    self.trpl_elapsed_time[ii,jj] = picoharp_measurement.ph.read_elapsed_meas_time()
                    if not ("trpl_time_array" in H): #for first histogram
                        H['trpl_time_array'] = picoharp_measurement.ph.time_array[:Nhist]
                        H['trpl_histogram_channels'] = picoharpHW.settings['histogram_channels']   
                    
                    
                ############### start 2D trpl measurement:
                    """ 
                   if False:
                   
                    for nx in range (0, self.Nx):
                        for ny in range(0, self.Ny):
                            # change acquisition time:
                            picoharpHW.settings['Tacq'] = self.settings['picoharp_exposure']
                            self.app.hardware['collection_filter'].settings['position'] = ELLIPTEC_PL_FILTER_POS
                            time.sleep(0.1)
                            #picoharp_measurement.interrupt_measurement_called = False
                            picoharp_measurement.start()
                            time.sleep(0.1)
                            self.log.info('recording trpl histogram')
                            while(picoharp_measurement.is_measuring()):
                                #print('waiting for picoharp')
                                if self.interrupt_measurement_called:
                                    picoharp_measurement.interrupt()
                                time.sleep(0.1)
                            time.sleep(0.1)
                            Nhist = picoharpHW.settings['histogram_channels']
                            histogram_data = picoharp_measurement.ph.histogram_data[:Nhist]
                            self.trpl_map[ii,jj,nx,ny] = histogram_data
                            if not ("trpl_time_array" in H): #for first histogram
                                H['trpl_time_array'] = picoharp_measurement.ph.time_array[:Nhist]
                                H['trpl_histogram_channels'] = picoharpHW.settings['histogram_channels'] 
                                                   
                    self.trpl_elapsed_time[ii,jj] = picoharp_measurement.ph.read_elapsed_meas_time()        
                        """
                
                
                ############## start map measure
                
                if False:
                    
                    # store current xy position
                    orig_x = stage.settings.x_position.read_from_hardware()
                    orig_y = stage.settings.y_position.read_from_hardware()
                    
                    # change acquisition time:
                    picoharpHW.settings['Tacq'] = self.settings['picoharp_exposure']
                    
                    # start map measurement
                    map_measure.interrupt_measurement_called = False
                    map_measure.start()
                    time.sleep(0.1)
                    self.log.info('map started')
                    
                    # wait till complete
                    while( map_measure.is_measuring()):
                        #print('waiting for map')
                        if self.interrupt_measurement_called:
                            map_measure.interrupt()
                        time.sleep(0.1)
                    self.log.info('map complete')
                    
                    if self.settings['map_type'] == "Picoharp_MCL_2DSlowScan":
                        # if H5 dataset does not exist, create with shape (Np, Nslice,1, Ny, Nx, M.num_hist_chans)
                        if not "trpl_3d_map" in H:
                            trpl_map_array_shape =(Np, self.NSlices, ) + map_measure.time_trace_map.shape
                            self.trpl_3d_map_h5 = H.create_dataset('trpl_3d_map', trpl_map_array_shape, dtype=float)
                        # copy time trace map (M.time_trace_map of shape (1,Ny,Nx,M.num_hist_chans))
                        self.trpl_3d_map_h5[ii,jj] = map_measure.time_trace_map

                    # restore old xy position
                    stage.settings['x_target'] = orig_x
                    stage.settings['y_target'] = orig_y
                    
                #################### Fiber scan measure
                
                if True:
                    # store original fiber position
                    fiber_hw = self.app.hardware['thorlabs_stepper_controller']
                    orig_fiber_x = fiber_hw.settings['x_position']
                    orig_fiber_y = fiber_hw.settings['y_position']
                    orig_fiber_z = fiber_hw.settings['z_position']
    
                    # APD fiber map PL                   
                    if False:    
                        fiber_apd_scan = self.app.measurements['fiber_apd_scan']
                        self.run_measurement_and_wait(fiber_apd_scan)
                    
                        if not "fiber_apd_scans_PL" in H:
                            fiber_apd_scans_shape = (Np, self.NSlices, ) + fiber_apd_scan.count_rate_map.shape
                            self.fiber_apd_scans_h5 = H.create_dataset('fiber_apd_scans_PL', 
                                                                       fiber_apd_scans_shape, dtype=float )
                        self.fiber_apd_scans_h5[ii,jj] = fiber_apd_scan.count_rate_map
                    
                    # APD fiber map laser
                    if False:
                        fiber_apd_scan = self.app.measurements['fiber_apd_scan']
                        self.run_measurement_and_wait(fiber_apd_scan)
                    
                        if not "fiber_apd_scans_laser" in H:
                            fiber_apd_scans_shape = (Np, self.NSlices, ) + fiber_apd_scan.count_rate_map.shape
                            self.fiber_apd_scans_h5 = H.create_dataset('fiber_apd_scans_laser', 
                                                                       fiber_apd_scans_shape, dtype=float )
                        self.fiber_apd_scans_h5[ii,jj] = fiber_apd_scan.count_rate_map
                    
                    # TRPL fiber map
                    
                    # change acquisition time:
                    picoharpHW.settings['Tacq'] = self.settings['picoharp_exposure']
                        
                    fiber_picoharp_scan = self.app.measurements['fiber_picoharp_scan']
                    self.run_measurement_and_wait(fiber_picoharp_scan)
                    
                    if not "fiber_picoharp_scans" in H:
                        fiber_picoharp_scans_shape = (Np, self.NSlices,) + fiber_picoharp_scan.time_trace_map.shape
                        self.fiber_picoharp_scans_h5 = H.create_dataset('fiber_picoharp_scans', 
                                                                        fiber_picoharp_scans_shape, dtype=float)
                    
                    binMax = min( fiber_picoharp_scan.time_trace_map.shape[-1], self.fiber_picoharp_scans_h5.shape[-1])
                    print( "fiber_picoharp_scan.time_trace_map", fiber_picoharp_scan.time_trace_map.shape )
                    print( "fiber_picoharp_scans_h5", self.fiber_picoharp_scans_h5.shape )
                    print("binMax", binMax)
                    self.fiber_picoharp_scans_h5[ii,jj,...,0:binMax] = fiber_picoharp_scan.time_trace_map[...,0:binMax]
                    
                    # restore old fiber position
                    fiber_hw.settings['x_target_position'] = orig_fiber_x 
                    fiber_hw.settings['y_target_position'] = orig_fiber_y
                    fiber_hw.settings['z_target_position'] = orig_fiber_z 
                    
                    
                ############## collect power meter value after measurement
                self.pm_powers_after[ii]=self.collect_pm_power_data()

                # move z
                #stage.settings['z_target'] += Stepsize
                #if stage.settings['z_target'] - original_z >= Depth:
                #    depthScanComplete = True
            
            ############## move back to surface:
            #depthScanComplete = False
            stage.settings['z_target'] = original_z
            
            ############ set power:
            # move to new power wheel position
            #close shutter
            self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_CLOSED_POS
            time.sleep(0.1)     
            self.power_wheel_dev.write_steps_and_wait(self.step_size*self.direction[ii])
            time.sleep(0.5)
            self.power_wheel_hw.encoder_pos.read_from_hardware()
            #close shutter
            self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_OPEN_POS        
            time.sleep(0.1)
            
        # write data to h5 file on disk
        
        try: 
            pass      
            #create h5 data arrays
            #H['pm_powers'] = self.pm_powers
            #H['pm_powers_after'] = self.pm_powers_after
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
            #close shutter
            self.app.hardware['laser_in_shutter'].settings['position'] = LASER_IN_SHUTTER_CLOSED_POS
            time.sleep(0.1)     
    
    def run_measurement_and_wait(self, M):
        # start measurement
        M.interrupt_measurement_called = False
        M.start()
        time.sleep(0.1)
        self.log.info('Measurement started {}'.format(M.name))
        
        # wait till complete
        while( M.is_measuring()):
            if self.interrupt_measurement_called:
                M.interrupt()
            time.sleep(0.1)
        self.log.info('Measurement complete {}'.format(M.name))
            
    def move_to_min_pos(self):
        self.power_wheel_dev.read_status()
        
        delta_steps = self.power_wheel_min.val - self.power_wheel_hw.encoder_pos.read_from_hardware()
        if delta_steps != 0:
            #print 'moving to min pos'
            self.power_wheel_dev.write_steps_and_wait(delta_steps)
            #print 'done moving to min pos'
            
            
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
                        self.log.error("failed to collect power meter sample: {}".format(err))
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power = pm_power/samp_count
        else:
            print("  Failed to read power")
            pm_power = 10000.  

        
        return pm_power    
