import numpy as np
from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan
import time
from h5py import h5
import pyqtgraph as pg
from qtpy import QtCore
import glob
import os

class AndorHyperSpecASIScan(ASIStage2DScan):
    
    name = "asi_hyperspec_scan"
    #name = "ASI_2DHyperspecscan"
    
    def scan_specific_setup(self):
        #Hardware
        self.stage = self.app.hardware['asi_stage']
        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']
        
        

    def pre_scan_setup(self):
        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        time.sleep(0.01)
    
    def collect_pixel(self, pixel_num, k, j, i):
        print("collect_pixel", pixel_num, k,j,i)
        self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called

        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        self.andor_ccd_readout.run()
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.andor_ccd_readout.spectra_data.shape
            
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                 'spec_map', spec_map_shape, dtype=np.float)

            self.wls = np.array(self.andor_ccd_readout.wls)
            self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = self.andor_ccd_readout.spectra_data
        self.spec_map[k,j,i,:] = spec
        if self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = spec
  
        self.display_image_map[k,j,i] = spec.sum()


    def post_scan_cleanup(self):
        self.andor_ccd_readout.settings['save_h5'] = True
        
    def update_display(self):
        ASIStage2DScan.update_display(self)
        self.andor_ccd_readout.update_display()
            
    def insert_bg_from_folder(self, folder=None):
        if folder is None:
            folder = self.app.settings['save_dir']
            print(folder)
        bg_files = glob.glob(os.path.join(folder, '*toupcam*'))
        print(bg_files)
        for fname in bg_files:
            #try:
            self.insert_bg_img(os.path.join(folder, fname))
            #except:
                #print('failed to import:',fname)
                   
    def clear_bg_img(self):
        if hasattr(self, 'img_bkg_items') and hasattr(self, 'img_plot'):
            for item in self.img_bkg_items:
                self.img_plot.removeItem(item)
                            
    def insert_bg_img(self, fname=None):         
        #self.bkg_data = load_image('C:\\Users\\lab\\Documents\\image_100.tif')
        # remove existing
        #if hasattr(self, 'img_bkg'):
        #    self.img_plot.removeItem(self.img_bkg)
        import h5py
        with h5py.File(fname, mode='r') as H:
            self.bg_im = np.array(H['measurement/toupcam_live/image'])
            try:
                x_center_stage = H['hardware/asi_stage/settings'].attrs['x_position']
                y_center_stage = H['hardware/asi_stage/settings'].attrs['y_position']
            except:
                x_center = 0.
                y_center = 0.
                print('no coordinates found, loading image at (zero, zero)')
                
            x_center, y_center = H['hardware/toupcam/settings'].attrs['centerx_micron'],H['hardware/toupcam/settings'].attrs['centery_micron']
            width, height = H['hardware/toupcam/settings'].attrs['width_micron'], H['hardware/toupcam/settings'].attrs['height_micron']
            
        if  self.h_unit == 'mm':
            width /= 1000.
            height /= 1000.
            x_center /= 1000.
            y_center /= 1000.
            
        print(np.shape(self.bg_im))
        
        x0_bkg = x_center_stage - x_center
        y0_bkg = y_center_stage - y_center
        
        print('|center:', x_center_stage,y_center_stage, '|corner:', x0_bkg,y0_bkg, '|size:', width,height)
        
        self.img_bkg = pg.ImageItem(self.bg_im)
        if hasattr(self, 'img_bkg_items'):
            self.img_bkg_items.append(self.img_bkg)
        else:
            self.img_bkg_items = [self.img_bkg]
        self.img_bkg_rect = QtCore.QRectF(x0_bkg, y0_bkg, width, height)
        print("Rect: ", self.img_bkg_rect)
        self.img_plot.addItem(self.img_bkg)
        self.img_bkg.setRect(self.img_bkg_rect)
        self.img_bkg.setZValue(-1)
        
        
        
