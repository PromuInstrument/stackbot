import time
import numpy as np
from ScopeFoundry import Measurement


class SingleParticleBlink(Measurement):
    
    name = 'single_particle_blink'
    
    def setup(self):
        
        # LoggedQuantities
        self.apd_trace_max_time = self.add_logged_quantity(
                                      "apd_trace_max_time", 
                                     dtype=float, vmin=0.001, vmax=4*3600, initial=120)

    def setup_figure(self):
        pass

    def _run(self):
        self.display_update_period = 0.01 #seconds

        
        self.save_dict = dict()
        
        try:
             ## measure power
            self.gui.thorlabs_powermeter_hc.power_meter.measure_power()

            # Collect Spectrum
            print "spectrum_before"
            ## Flip mirror to Spec
            self.flip_to_spec()
            ## Open shutter
            self.open_shutter()
            ## acquire Spec
            self.gui.andor_ro_measure.read_single.update_value(True)
            self.gui.andor_ro_measure._run()
            #self.save_dict['wls'] = self.gui.andor_ro_measure.wls.copy()
           # self.save_dict['spectrum_before'] = self.gui.andor_ro_measure.spectrum.copy()
            ## Close shutter
            self.close_shutter()
    
            # Collect lifetime
            print "T3 measurement"
            ## Flip mirror to APD
            self.flip_to_apd()
            ## Open shutter
            self.open_shutter()
            

            ## acquire picoharp
            
            self.gui.picoharp_tttr_measure._run()
           # self.save_dict['ph_time_histogram_before'] = self.gui.picoharp_hc.picoharp.histogram_data.copy() # Make sure it copies!
            #self.save_dict['ph_time_array_before'] = self.gui.picoharp_hc.picoharp.time_array.copy() # Make sure it copies!
            #self.save_dict['ph_elapsed_meas_time'] = self.gui.picoharp_hc.picoharp.read_elapsed_meas_time()
            ## Close shutter
            self.close_shutter()
            
            # Collect apd_optimzer (look for blinking)
            #print "apd_trace"
            ## Open shutter
            #self.open_shutter()
            ## acquire apd_optimizer
            #self.apd_trace = [] 
            #self.save_dict['apd_trace'] =self.apd_trace
            #self.apd_trace_time = []
            #self.save_dict['apd_trace_time'] =self.apd_trace_time
            #self.t0 = time.time()
            #self.apd_trace_elapsed = 0
            #print self.apd_trace_max_time.val
            #while self.apd_trace_elapsed < self.apd_trace_max_time.val:
            #    if self.interrupt_measurement_called:
            #        break
            #    self.gui.apd_counter_hc.apd_count_rate.read_from_hardware()            
            #    self.apd_trace.append(self.gui.apd_counter_hc.apd_count_rate.val  )
            #    self.apd_trace_time.append(self.apd_trace_elapsed)
            #    self.apd_trace_elapsed = time.time() - self.t0
                #print self.apd_trace_elapsed
            ## close shutter
            #self.close_shutter()
            #print "apd_trace done"
            
            # Collect Spectrum
            
            #print "spectrum_after"
            ## Flip mirror to Spec
            #self.flip_to_spec()
            ## Open shutter
            #self.open_shutter()
            ## acquire Spec
            #self.gui.andor_ro_measure.read_single.update_value(True)
            #self.gui.andor_ro_measure._run()
            #self.save_dict['spectrum_after'] = self.gui.andor_ro_measure.spectrum.copy()
            ## Close shutter
            #self.close_shutter()
            
            # Collect lifetime
            #print "lifetime after"
            ## Flip mirror to APD
            #self.flip_to_apd()
            ## Open shutter
            #self.open_shutter()
            ## acquire picoharp
            #self.gui.picoharp_measure._run()
            #self.save_dict['ph_time_histogram_after'] = self.gui.picoharp_hc.picoharp.histogram_data.copy()
            #self.save_dict['ph_time_array_after'] = self.gui.picoharp_hc.picoharp.time_array.copy()
            #self.save_dict['ph_elapsed_meas_time_after'] = self.gui.picoharp_hc.picoharp.read_elapsed_meas_time()        
            ## Close shutter
            #self.close_shutter()
        
        finally:
            for lqname,lq in self.gui.logged_quantities.items():
                self.save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    self.save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                self.save_dict[self.name +"_"+ lqname] = lq.val
                
            self.fname = "%i_%s.npz" % (time.time(), self.name)
            np.savez_compressed(self.fname, **self.save_dict)
            print self.name, "saved:", self.fname


    def flip_to_spec(self):
        self.gui.flip_mirror_hc.flip_mirror_position.update_value(
                                          self.gui.flip_mirror_hc.POSITION_SPEC)
        time.sleep(0.2)
        
    def flip_to_apd(self):
        self.gui.flip_mirror_hc.flip_mirror_position.update_value(
                                          self.gui.flip_mirror_hc.POSITION_APD)
        time.sleep(0.2)

    def open_shutter(self):
        self.gui.shutter_servo_hc.shutter_open.update_value(True)
        time.sleep(0.2)

    def close_shutter(self):
        self.gui.shutter_servo_hc.shutter_open.update_value(False)
        time.sleep(0.2)

    def update_display(self):        
        pass
    
class SingleParticleBlinkSet(Measurement):
    
    name = 'single_particle_blink_set'
    
    def setup(self):
        pass
    
    def setup_figure(self):
        pass
    
    def _run(self):

        self.coords = [
(67.6235296643 ,67.7094017973, None),
(54.7560513256 ,64.5592722455, None),
(50.5914732741 ,57.7784849052, None),
(53.7416028259 ,51.1044816175, None),
(56.4645961673 ,54.5215713008, None),
(63.4589516128 ,52.2257141699, None),
        ]
        

        
        for ii, (x,y,z) in enumerate(self.coords):
            print self.name, x,y,z, ":", ii, "of", len(self.coords)
            if self.interrupt_measurement_called:
                break
                        
            #move to location
            self.gui.mcl_xyz_stage_hc.move_pos_slow(x,y,z)
            
            self.gui.single_particle_blink_measure.interrupt_measurement_called=False
            self.gui.single_particle_blink_measure._run()
            
        # rerun apd map
        self.gui.flip_mirror_hc.flip_mirror_position.update_value(
                                          self.gui.flip_mirror_hc.POSITION_APD)
        self.gui.apd_scan_measure.interrupt_measurement_called=False
        self.gui.apd_scan_measure._run()
            
        print self.name, "done"
            
    def update_display(self):
        pass
            

