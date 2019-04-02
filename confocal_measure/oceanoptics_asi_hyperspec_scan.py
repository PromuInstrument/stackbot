import numpy as np
from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan
from ScopeFoundry.scanning import BaseRaster2DScan
from ScopeFoundry import Measurement
import time

class OOHyperSpecASIScan(ASIStage2DScan):
    
    name = "asi_OO_hyperspec_scan"
    
    def __init__(self, app):
        ASIStage2DScan.__init__(self, app)        
    
    def setup(self):
        ASIStage2DScan.setup(self)
    
    def setup_figure(self):
        BaseRaster2DScan.setup_figure(self)
        self.pt_roi.setSize((0.2,0.2))
        self.oo_spec.roi.sigRegionChanged.connect(self.recompute_image_map)
        
    def scan_specific_setup(self):
        #Hardware
        self.stage = self.app.hardware['asi_stage']
        self.oo_spec = self.app.measurements['oo_spec_live']
        self.add_operation('center_on_pos',self.center_on_pos)
        self.set_details_widget(
            widget=self.settings.New_UI(include=['h_span','v_span','h_center','v_center']))
        
        
    def pre_scan_setup(self):
        self.oo_spec.settings['bg_subtract'] = False
        self.oo_spec.settings['continuous'] = False
        self.oo_spec.settings['save_h5'] = False
        #self.oo_spec.settings['baseline_subtract'] = False
        time.sleep(0.01)
    
    def collect_pixel(self, pixel_num, k, j, i):
        print("collect_pixel", pixel_num, k,j,i)
        self.oo_spec.interrupt_measurement_called = self.interrupt_measurement_called

        self.oo_spec.settings['continuous'] = False
        self.oo_spec.settings['save_h5'] = False
        self.oo_spec.run()
        
        #self.continuous_scan = self.settings.New("continuous_scan", dtype=bool, initial=False)
        #self.settings.New('save_h5', dtype=bool, initial=True, ro=False)
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.oo_spec.oo_spec_dev.spectrum.shape
             
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                      'spec_map', spec_map_shape, dtype=np.float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)

            self.wls = np.array(self.oo_spec.oo_spec_dev.wavelengths)
            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = self.oo_spec.oo_spec_dev.spectrum
        if self.oo_spec.settings['baseline_subtract']:
            spec = spec - self.oo_spec.settings.baseline_val.value
        self.spec_map[k,j,i,:] = spec
        if True: #self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = spec
        
        ind_min = np.searchsorted(self.wls,self.oo_spec.settings.roi_min.val)
        ind_max = np.searchsorted(self.wls,self.oo_spec.settings.roi_max.val)
        self.display_image_map[k,j,i] = spec[ind_min:ind_max].sum()
    
    def recompute_image_map(self):
        self.display_image_map = np.zeros(self.scan_shape)
        ind_min = np.searchsorted(self.wls,self.oo_spec.settings.roi_min.val)
        ind_max = np.searchsorted(self.wls,self.oo_spec.settings.roi_max.val)
        #print("Min %d Max %d" % (ind_min,ind_max))
        self.display_image_map = np.sum(self.spec_map_h5[:,:,:,ind_min:ind_max],axis=-1)
        
    def update_display(self):
        ASIStage2DScan.update_display(self)
        self.oo_spec.update_display()
        
    def center_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
        
    def interrupt(self):
        Measurement.interrupt(self)
        self.oo_spec.interrupt()
        