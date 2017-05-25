from ScopeFoundryHW.sync_raster_daq import SyncRasterScan
import numpy as np

class HyperSpecCLMeasure(SyncRasterScan):
    
    name = "hyperspec_cl"
    
    def setup(self):
        SyncRasterScan.setup(self)
        self.settings['adc_oversample'] = 2000
        
        # set reason limits for oversample rate (max pixel rate 275Hz) for mode
        
        # Tested up to 2.9+0.7ms per pixel on andor newton
        
        # quad viewer with spec plot and band pass image
        
        # data saving hdf5
        
        # data viewer 
        
        
        
        
    def pre_scan_setup(self):
        # hardware
        
        self.app.hardware['sem_remcon'].read_from_hardware()
        
        sync_raster_daq = self.app.hardware['sync_raster_daq']
        self.andor_ccd = ccd = self.app.hardware['andor_ccd']
        ccd.settings['acq_mode'] = 'kinetic'
        ccd.settings['trigger_mode'] = 'external'
        ccd.settings['readout_mode'] = 0
        ccd.settings['num_kin'] = self.Npixels
        ccd.settings['exposure_time'] = (1.0 / sync_raster_daq.settings['dac_rate']) - 3.0e-3
        ccd.set_readout()
        
        
    
        Ny, Nx = ccd.settings['readout_shape']
    
        assert Ny == 1
    
        # create data buffer (h5)
        self.buffer = np.zeros(shape=(self.Npixels, Nx), dtype=np.int32)  
        self.andor_ccd_pixel_i = 0

        # start ccd camera
        ccd.ccd_dev.start_acquisition()
    
    def handle_new_data(self):
        """ Called during measurement thread wait loop"""
        SyncRasterScan.handle_new_data(self)
        
        
        ccd_dev = self.andor_ccd.ccd_dev
#        print("get_number_new_images", ccd_dev.get_number_new_images()
        print("get_total_number_images_acquired", ccd_dev.get_total_number_images_acquired())
        if ccd_dev.get_total_number_images_acquired() > 0:
            print("get_number_available_images", ccd_dev.get_number_available_images())
            print("get_number_new_images", ccd_dev.get_number_new_images())
            
            #first, last = ccd_dev.get_number_new_images()
            
            #validfirst, validlast, buf = ccd_dev.get_images(first, last, self.buffer[first-1:last-1,:])
            #print("get_images", validfirst, validlast)

            while 1:
                arr = ccd_dev.get_oldest_image(self.buffer[self.andor_ccd_pixel_i,:])
                if arr is None:
                    break
                self.andor_ccd_pixel_i += 1
                print('oldest image', arr.shape, np.max(arr))
            
        
    def post_scan_cleanup(self):
        self.andor_ccd.interrupt_acquisition()
    
    def get_display_pixels(self):
        #self.display_pixels = self.buffer.mean(axis=1)
        return SyncRasterScan.get_display_pixels(self)
