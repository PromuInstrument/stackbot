from __future__ import division, print_function
import numpy as np
from ScopeFoundryHW.mcl_stage import MCLStage2DSlowScan
from ScopeFoundry import Measurement, LQRange
import time

class HyperSpecPicam2DScan(MCLStage2DSlowScan):
    
    name = "hyperspec_picam_mcl"
    
    def scan_specific_setup(self):
        #Hardware
        self.picam = self.app.hardware['picam']

    
    def pre_scan_setup(self):
        # FIXME hard-coded CCD dimension
        self.spec_map = np.zeros(self.scan_shape + (1340,), dtype=np.float)
        if self.settings['save_h5']:
            self.spec_map_h5 = self.h5_meas_group.create_dataset('spec_map', self.scan_shape + (1340,), dtype=np.float)
        self.app.measurements.picam_readout.interrupt()

        self.picam.commit_parameters()


        
    def collect_pixel(self, pixel_num, k, j, i):
        # collect data
        # store in arrays        
        print("collect_pixel:",  pixel_num, k, j, i)
        dat = self.picam.cam.acquire(readout_count=1, readout_timeout=-1)
            
        self.roi_data = self.picam.cam.reshape_frame_data(dat)
        self.spec_map[k,j,i, :] = self.spec =  self.roi_data[0].sum(axis=0)
        
        if self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = self.spec
        
        self.display_image_map[k,j,i] = np.sum(self.spec)

        tot_sec_to_go = (1.0 - self.settings.progress.val / 100) * self.Npixels * self.picam.settings['ExposureTime'] / 1000
        h_left = tot_sec_to_go / 3600
        min_left = (tot_sec_to_go % 3600) / 60
        sec_left = (tot_sec_to_go % 3600 ) % 60
        
        print('{0:1.0f}h {1:2.0f}min {2:2.0f}s left'.format(h_left, min_left, sec_left) )
        

        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")

            self.picam_measure = self.app.measurements['picam_readout']

            self.wls = np.array(self.picam_measure.wls)
            self.wave_numbers = np.array(self.picam_measure.wave_numbers)
            self.raman_shifts = np.array(self.picam_measure.raman_shifts)

            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls
                self.h5_meas_group['wave_numbers'] = self.wave_numbers
                self.h5_meas_group['raman_shifts'] = self.raman_shifts



    def post_scan_cleanup(self):
        #H['spec_map'] = self.h_array
        
        print(self.name, "post_scan_cleanup")
        #import scipy.io
        #scipy.io.savemat(file_name=self.h5_filename +".mat", mdict=dict(spec_map=self.spec_map))



    def update_display(self):
        
        if hasattr(self, 'roi_data'):
            self.app.measurements.picam_readout.roi_data = self.roi_data
            self.app.measurements.picam_readout.update_display()

        super().update_display()
    

class HyperSpecPicam3DStack(Measurement):
    
    name = 'HyperSpecPicam3DStack'
    
    def setup(self):
        lq_params = dict(dtype=float, vmin=0,vmax=100, ro=False, unit='um' )
        self.z0 = self.settings.New('z0',  initial=20, **lq_params  )
        self.z1 = self.settings.New('z1',  initial=30, **lq_params  )
        lq_params = dict(dtype=float, vmin=1e-9,vmax=100, ro=False, unit='um' )
        self.dz = self.settings.New('dz', initial=1, **lq_params)
        self.Nz = self.settings.New('Nz', dtype=int, initial=10, vmin=1)
        
        self.z_range = LQRange(min_lq=self.z0, max_lq=self.z1, step_lq=self.dz, num_lq=self.Nz)
    
    def run(self):
        
        self.scan2d = self.app.measurements["hyperspec_picam_mcl"]
        self.stage = self.app.hardware['mcl_xyz_stage']

        for kk, z in enumerate(self.z_range.array):
            if self.interrupt_measurement_called:
                self.scan2d.interrupt()
                break
            
            print(self.name, kk, z)
                        
            self.stage.settings['z_target'] = z
            time.sleep(1.)
            
            self.scan2d.start()
            while self.scan2d.is_measuring():
                if self.interrupt_measurement_called:
                    self.scan2d.interrupt()
                    break
                time.sleep(0.1)
        
    def update_display(self):
        self.scan2d.update_display()
        