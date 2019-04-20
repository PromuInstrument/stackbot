import numpy as np
from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan
from ScopeFoundry.scanning import BaseRaster2DScan
from qtpy.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton
import time


class AndorAsiHyperSpec2DScan(ASIStage2DScan):
    
    name = "andor_asi_hyperspec_scan"
    
    def scan_specific_setup(self):
        #Hardware
        self.stage = self.app.hardware['asi_stage']

        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']

        self.add_operation('center_on_pos',self.center_on_pos)
        self.add_operation('center view on position', self.center_view_on_pos)
        
        details_widget = QWidget()
        details = QVBoxLayout()
        details.addWidget(self.app.settings.New_UI(include=['save_dir','sample']))
        details.addWidget(self.settings.New_UI(include=['h_span','v_span']))
        pushButtons_widget = QWidget()
        pushButtons = QHBoxLayout()
        for key in list(self.operations.keys()):
            op_pushButton = QPushButton(text=key)
            op_pushButton.clicked.connect(self.operations[key])
            pushButtons.addWidget(op_pushButton)
        pushButtons_widget.setLayout(pushButtons)
        details.addWidget(pushButtons_widget)
        details_widget.setLayout(details)
        self.set_details_widget(widget=details_widget)


    def pre_scan_setup(self):
        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        self.stage.other_observer = True
        time.sleep(0.01)
    
    def collect_pixel(self, pixel_num, k, j, i):
        print("collect_pixel", pixel_num, k,j,i)
        self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called

        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        #self.andor_ccd_readout.settings['activation'] = True
        # wait until done
        #while self.andor_ccd_readout.is_measuring():
        #    self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called
        #    time.sleep(0.01)
        self.start_nested_measure_and_wait(self.andor_ccd_readout)
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.andor_ccd_readout.spectra_data.shape
            
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                     'spec_map', spec_map_shape, dtype=np.float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)

            self.wls = np.array(self.andor_ccd_readout.wls)
            
            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = self.andor_ccd_readout.spectra_data
        self.spec_map[k,j,i,:] = spec
        if self.settings['save_h5']:
            self.spec_map_h5[k,j,i,:] = spec
  
        self.display_image_map[k,j,i] = spec.sum()


    def post_scan_cleanup(self):
        self.andor_ccd_readout.settings['save_h5'] = True
        self.stage.other_observer = False
        
    def update_display(self):
        ASIStage2DScan.update_display(self)
        self.andor_ccd_readout.update_display()
        
    def center_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
        
    def center_view_on_pos(self):
        delta = 0.2
        del_h = self.h_span.val*delta
        del_v = self.v_span.val*delta
        self.img_plot.setRange(xRange=(self.h0.val-del_h, self.h1.val+del_h), yRange=(self.v0.val-del_v, self.v1.val+del_v))
        
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=True)
#         # DISABLE below because of crashing TODO - fix this?
#         non_zero_index = np.nonzero(self.disp_img)
#         if len(non_zero_index[0]) > 0:
#             self.hist_lut.setLevels(*np.percentile(self.disp_img[non_zero_index],(1,99)))
        
