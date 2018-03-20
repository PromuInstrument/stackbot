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
        
        self.up_and_down_sweep    = self.settings.New("up_and_down_sweep",dtype=bool, initial=True)

        self.settings.New('map_type', dtype=str,
                          choices=('APD_MCL_2DSlowScan', 'Picoharp_MCL_2DSlowScan', 'WinSpecMCL2DSlowScan'), initial='APD_MCL_2DSlowScan')
    
    def run(self):
        
        # hardware and delegate measurements
        self.power_wheel_hw = self.app.hardware.power_wheel_arduino
        self.power_wheel_dev = self.power_wheel_hw.power_wheel_dev
        
        map_measure = self.app.measurements[self.settings['map_type']]
        map_measure.interrupt_measurement_called = False
        
        ### Define number of power steps (same as number of maps)
        self.Np = Np = self.power_wheel_ndatapoints.val
        self.step_size = int( (self.power_wheel_max.val-self.power_wheel_min.val)/Np )


        if self.settings['up_and_down_sweep']:
            self.direction = np.ones(Np*2) # step up
            self.direction[Np] = 0 # don't step at the top!
            self.direction[Np+1:] = -1 # step down
            Np = self.Np = 2*Np
        else:
            self.direction = np.ones(Np)
                    
        ### Create Data Arrays    
        self.power_wheel_position = np.zeros(Np)      
        self.pm_powers = np.zeros(Np, dtype=float)
        self.pm_powers_after = np.zeros(Np, dtype=float)
        
        ### Start measurement:
        self.move_to_min_pos()

        
        for ii in range(Np):
            self.settings['progress'] = 100.*ii/self.Np
            
            if self.interrupt_measurement_called:
                break
            
           
            # record power wheel position
            self.power_wheel_position[ii] = self.power_wheel_hw.encoder_pos.read_from_hardware()
            
            # collect power meter value
            self.pm_powers[ii]=self.collect_pm_power_data()
            
            ## run autofocus
            autofocus = self.app.measurements['auto_focus']
            autofocus.interrupt_measurement_called = False
            autofocus.start()
            time.sleep(0.1)
            while( autofocus.is_measuring()):
                if self.interrupt_measurement_called:
                    autofocus.interrupt()
                time.sleep(0.1)

            
            ## start map measure
            map_measure.interrupt_measurement_called = False
            map_measure.start()
            print('map started')
            
            # wait till complete
            while( map_measure.is_measuring()):
                if self.interrupt_measurement_called:
                    map_measure.interrupt()
                time.sleep(0.1)
            
            ## collect power meter value after measurement
            self.pm_powers_after[ii]=self.collect_pm_power_data()
            
            ## set power:
            # move to new power wheel position
            self.power_wheel_dev.write_steps_and_wait(self.step_size*self.direction[ii])
            time.sleep(0.5)
            self.power_wheel_hw.encoder_pos.read_from_hardware()


            
        # write data to h5 file on disk
        
        self.t0 = time.time()
        #self.fname = "%i_%s.h5" % (self.t0, self.name)
        #self.h5_file = h5_io.h5_base_file(self.app, self.fname )
        self.h5_file = h5_io.h5_base_file(app=self.app,measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
            #create h5 data arrays

            H['pm_powers'] = self.pm_powers
            H['pm_powers_after'] = self.pm_powers_after
            H['power_wheel_position'] = self.power_wheel_position
            H['direction'] = self.direction
        finally:
            self.log.info("data saved "+self.h5_file.filename)
            self.h5_file.close()
            
            
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
                        print("failed to collect power meter sample:", err)
                        break
                    time.sleep(0.010)
         
        if samp_count > 0:              
            pm_power = pm_power/samp_count
        else:
            print("  Failed to read power")
            pm_power = 10000.  

        
        return pm_power    
