from ScopeFoundryHW.sync_raster_daq import SyncRasterScan
import numpy as np
<<<<<<< HEAD
import time
=======
>>>>>>> d23eddb51984f311015483594899062df7612379

class HyperSpecCLMeasure(SyncRasterScan):
    
    name = "hyperspec_cl"
    
    def setup(self):
        SyncRasterScan.setup(self)
<<<<<<< HEAD
        self.settings['adc_oversample'] = 2500
        self.settings.adc_oversample.change_min_max(2500, 25e6)        
        # set reasonable limits for oversample rate (max pixel rate 275Hz) for mode
=======
        self.settings['adc_oversample'] = 2000
        
        # set reason limits for oversample rate (max pixel rate 275Hz) for mode
        
>>>>>>> d23eddb51984f311015483594899062df7612379
        # Tested up to 2.9+0.7ms per pixel on andor newton
        
        # quad viewer with spec plot and band pass image
        
        # data saving hdf5
        
<<<<<<< HEAD
        # compute wavelength array
        
        # data viewer 
        
        
        # ability to set exposure time shorter than pixel time
        
        
        
        
=======
        # data viewer 
        
        
>>>>>>> d23eddb51984f311015483594899062df7612379
        
        
    def pre_scan_setup(self):
        # hardware
        
        self.app.hardware['sem_remcon'].read_from_hardware()
        
        sync_raster_daq = self.app.hardware['sync_raster_daq']
        self.andor_ccd = ccd = self.app.hardware['andor_ccd']
<<<<<<< HEAD
        ccd.settings['acq_mode'] = 'run_till_abort'
        ccd.settings['trigger_mode'] = 'external'
        ccd.settings['readout_mode'] = 0 # FVB
        ccd.settings['num_kin'] = self.Npixels
        ccd.settings['exposure_time'] = (1.0 / sync_raster_daq.settings['dac_rate']) - 3.0e-3
        ccd.settings['kin_time'] = (1.0 / sync_raster_daq.settings['dac_rate'])
        # Other useful defaults
        ccd.settings['output_amp'] = 0
        ccd.settings['ad_chan'] = 1
        #ccd.settings['hs_speed_em'] = 0
        ccd.settings['vertical_shift_speed'] = 0
        
        ccd.set_readout()
        
        ccd_Ny, ccd_Nx = ccd.settings['readout_shape']
    
        assert ccd_Ny == 1
    
        # create data buffer
        self.spec_buffer = np.zeros(shape=(self.Npixels, ccd_Nx), dtype=np.int32) # buffer for spectra (for one spatial frame)
        self.spec_map = np.zeros( shape=self.scan_shape + (ccd_Nx,), dtype=np.int32) # spatial hyperspec data cube
        
        Nk, Nj, Ni = self.scan_shape
        
        self.andor_ccd_pixel_i = 0
        self.andor_ccd_total_i = 0
        if self.settings['save_h5']:
            self.spec_map_h5 = self.create_h5_framed_dataset('spec_map', self.spec_map, compression=None, chunks=(1, 1, 1, Ni, ccd_Nx))
            #self.h5_m['wls'] = 

        # start ccd camera, wait for trigger
        ccd.ccd_dev.start_acquisition()
        print(self.andor_ccd.settings.ccd_status.read_from_hardware())

=======
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
>>>>>>> d23eddb51984f311015483594899062df7612379
    
    def handle_new_data(self):
        """ Called during measurement thread wait loop"""
        SyncRasterScan.handle_new_data(self)
        
<<<<<<< HEAD
        ccd_dev = self.andor_ccd.ccd_dev
        #print("get_number_new_images", ccd_dev.get_number_new_images()
        #print("get_total_number_images_acquired", ccd_dev.get_total_number_images_acquired())
        if ccd_dev.get_total_number_images_acquired() > 0:
            #print("get_number_available_images", ccd_dev.get_number_available_images())
            #print("get_number_new_images", ccd_dev.get_number_new_images())
=======
        
        ccd_dev = self.andor_ccd.ccd_dev
#        print("get_number_new_images", ccd_dev.get_number_new_images()
        print("get_total_number_images_acquired", ccd_dev.get_total_number_images_acquired())
        if ccd_dev.get_total_number_images_acquired() > 0:
            print("get_number_available_images", ccd_dev.get_number_available_images())
            print("get_number_new_images", ccd_dev.get_number_new_images())
>>>>>>> d23eddb51984f311015483594899062df7612379
            
            #first, last = ccd_dev.get_number_new_images()
            
            #validfirst, validlast, buf = ccd_dev.get_images(first, last, self.buffer[first-1:last-1,:])
            #print("get_images", validfirst, validlast)

<<<<<<< HEAD
            # Loop through available images in Andor buffer
            while 1:
                self.andor_ccd.settings.ccd_status.read_from_hardware()

                if self.interrupt_measurement_called:
                    break
                
                # new frame
                frame_num = (self.andor_ccd_total_i // self.Npixels)
                if self.andor_ccd_pixel_i == 0:
                    # stop if new frame is past requested frames
                    if (not self.settings['continuous_scan']) and frame_num >= self.settings['n_frames']:
                        break
                    # extend H5 array to fit new frame
                    if self.settings['save_h5']:
                        self.extend_h5_framed_dataset(self.spec_map_h5, frame_num)

                
                # grab the next ccd image, place it into buffer
                t0 = time.time()
                arr = ccd_dev.get_oldest_image(
                            self.spec_buffer[self.andor_ccd_pixel_i,:])
                if arr is None:
                    break
                
                # copy data to image shaped map
                i = self.andor_ccd_pixel_i
                #x = self.scan_index_array[i,:]
                #self.spec_map[x[0], x[1], x[2],:] = arr
                kk, jj, ii = self.scan_index_array[i,:]
                self.spec_map[kk,jj,ii,:] = arr
                if self.settings['save_h5']:
                    #print('save h5', frame_num, kk,jj,ii, i)
                    self.spec_map_h5[frame_num, kk,jj,ii,:] = arr

                self.andor_ccd_pixel_i += 1
                self.andor_ccd_total_i += 1
                self.andor_ccd_pixel_i %= self.Npixels
                
                #print('oldest image', arr.shape, np.max(arr), "%f" % (time.time()-t0) )

             
=======
            while 1:
                arr = ccd_dev.get_oldest_image(self.buffer[self.andor_ccd_pixel_i,:])
                if arr is None:
                    break
                self.andor_ccd_pixel_i += 1
                print('oldest image', arr.shape, np.max(arr))
            
>>>>>>> d23eddb51984f311015483594899062df7612379
        
    def post_scan_cleanup(self):
        self.andor_ccd.interrupt_acquisition()
    
    def get_display_pixels(self):
<<<<<<< HEAD
        #self.display_pixels = self.spec_buffer.mean(axis=1)
=======
        #self.display_pixels = self.buffer.mean(axis=1)
>>>>>>> d23eddb51984f311015483594899062df7612379
        return SyncRasterScan.get_display_pixels(self)
