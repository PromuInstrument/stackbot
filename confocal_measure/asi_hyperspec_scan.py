import numpy as np
from ScopeFoundryHW.asi_stage.asi_stage_raster import ASIStage2DScan, ASIStage3DScan
from qtpy.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton
import math
import time


class ASIHyperSpec2DScan(ASIStage2DScan):
    
    def __init__(self, app):
        ASIStage2DScan.__init__(self, app)
        
    def setup(self):
        self.settings.New('debug',dtype=bool,initial=False)
        ASIStage2DScan.setup(self)
    
    def scan_specific_setup(self):
        #Hardware                  
        self.stage = self.app.hardware['asi_stage']
        self.add_operation('center scan on position',self.center_scan_on_pos)
        self.add_operation('center view on scan', self.center_view_on_scan)
        
        details_widget = QWidget()
        details = QVBoxLayout()
        details.addWidget(self.app.settings.New_UI(include=['save_dir','sample']))
        details.addWidget(self.settings.New_UI(include=['h_span','v_span']))
        pushButtons_widget = QWidget()
        pushButtons = QGridLayout()
        ii = 1
        ni = 3
        for key in list(self.operations.keys()):
            col = (ii - 1) % ni
            row = math.ceil(ii / ni) - 1
            op_pushButton = QPushButton(text=key)
            op_pushButton.clicked.connect(self.operations[key])
            pushButtons.addWidget(op_pushButton,row,col)
            ii += 1
        pushButtons_widget.setLayout(pushButtons)
        details.addWidget(pushButtons_widget)
        details_widget.setLayout(details)
        self.set_details_widget(widget=details_widget)
        
    def pre_scan_setup(self):
        self.settings.save_h5.change_readonly(True)
        self.spec.settings['bg_subtract'] = False
        self.spec.settings['continuous'] = False
        self.spec.settings['save_h5'] = False
        time.sleep(0.01)
        self.stage.other_observer = True
    
    def collect_pixel(self, pixel_num, k, j, i):
        if self.settings['debug']: print("collect_pixel", pixel_num, k,j,i)
        self.spec.interrupt_measurement_called = self.interrupt_measurement_called

        self.start_nested_measure_and_wait(self.spec)
        # self.spec.run()
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.spec.spectrum.shape
              
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                      'spec_map', spec_map_shape, dtype=np.float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)
 
            self.wls = np.array(self.spec.wls)
            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = np.array(self.spec.spectrum)
        self.spec_map[k,j,i,:] = spec
        self.spec_map_h5[k,j,i,:] = spec
        self.display_image_map[k,j,i] = spec.sum()
        
    def post_scan_cleanup(self):
        self.settings.save_h5.change_readonly(False)
        self.stage.other_observer = False

        
    def center_scan_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
        
    def center_view_on_scan(self):
        delta = 0.2
        del_h = self.h_span.val*delta
        del_v = self.v_span.val*delta
        self.img_plot.setRange(xRange=(self.h0.val-del_h, self.h1.val+del_h), yRange=(self.v0.val-del_v, self.v1.val+del_v))

    def interrupt(self):
        ASIStage2DScan.interrupt(self)
        self.spec.interrupt()
    
    def update_display(self):
        ASIStage2DScan.update_display(self)
        self.spec.update_display()
    
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=True)
#         # DISABLE below because of crashing TODO - fix this?
#         non_zero_index = np.nonzero(self.disp_img)
#         if len(non_zero_index[0]) > 0:
#             self.hist_lut.setLevels(*np.percentile(self.disp_img[non_zero_index],(1,99)))


class ASIHyperSpec3DScan(ASIStage3DScan):
    
    def __init__(self, app):
        ASIStage3DScan.__init__(self, app)
        
    def setup(self):
        self.settings.New('debug',dtype=bool,initial=False)
        ASIStage3DScan.setup(self)
    
    def scan_specific_setup(self):
        #Hardware                  
        self.stage = self.app.hardware['asi_stage']
        self.add_operation('center scan on position',self.center_scan_on_pos)
        self.add_operation('center view on scan', self.center_view_on_scan)
        
        details_widget = QWidget()
        details = QVBoxLayout()
        details.addWidget(self.app.settings.New_UI(include=['save_dir','sample']))
        details.addWidget(self.settings.New_UI(include=['h_span','v_span','z_span']))
        pushButtons_widget = QWidget()
        pushButtons = QGridLayout()
        ii = 1
        ni = 3
        for key in list(self.operations.keys()):
            col = (ii - 1) % ni
            row = math.ceil(ii / ni) - 1
            op_pushButton = QPushButton(text=key)
            op_pushButton.clicked.connect(self.operations[key])
            pushButtons.addWidget(op_pushButton,row,col)
            ii += 1
        pushButtons_widget.setLayout(pushButtons)
        details.addWidget(pushButtons_widget)
        details_widget.setLayout(details)
        self.set_details_widget(widget=details_widget)
        
    def pre_scan_setup(self):
        self.settings.save_h5.change_readonly(True)
        self.spec.settings['bg_subtract'] = False
        self.spec.settings['continuous'] = False
        self.spec.settings['save_h5'] = False
        time.sleep(0.01)
        self.stage.other_observer = True
    
    def collect_pixel(self, pixel_num, k, j, i):
        if self.settings['debug']: print("collect_pixel", pixel_num, k,j,i)
        self.spec.interrupt_measurement_called = self.interrupt_measurement_called

        #self.start_nested_measure_and_wait(self.spec)
        self.spec.run()
        
        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            spec_map_shape = self.scan_shape + self.spec.spectrum.shape
              
            self.spec_map = np.zeros(spec_map_shape, dtype=np.float)
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                      'spec_map', spec_map_shape, dtype=np.float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)
 
            self.wls = np.array(self.spec.wls)
            if self.settings['save_h5']:
                self.h5_meas_group['wls'] = self.wls

        # store in arrays
        spec = np.array(self.spec.spectrum)
        self.spec_map[k,j,i,:] = spec
        self.spec_map_h5[k,j,i,:] = spec
        self.display_image_map[k,j,i] = spec.sum()
        
    def post_scan_cleanup(self):
        self.settings.save_h5.change_readonly(False)
        self.stage.other_observer = False

    def center_scan_on_pos(self):
        self.settings.h_center.update_value(new_val=self.stage.settings.x_position.val)
        self.settings.v_center.update_value(new_val=self.stage.settings.y_position.val)
        self.settings.z_center.update_value(new_val=self.stage.settings.z_position.val)
        
    def center_view_on_scan(self):
        delta = 0.2
        del_h = self.h_span.val*delta
        del_v = self.v_span.val*delta
        self.img_plot.setRange(xRange=(self.h0.val-del_h, self.h1.val+del_h), yRange=(self.v0.val-del_v, self.v1.val+del_v))

    def interrupt(self):
        ASIStage2DScan.interrupt(self)
        self.spec.interrupt()
    
    def update_display(self):
        ASIStage3DScan.update_display(self)
        self.spec.update_display()
    
    def update_LUT(self):
        ''' override this function to control display LUT scaling'''
        self.hist_lut.imageChanged(autoLevel=True)
#         # DISABLE below because of crashing TODO - fix this?
#         non_zero_index = np.nonzero(self.disp_img)
#         if len(non_zero_index[0]) > 0:
#             self.hist_lut.setLevels(*np.percentile(self.disp_img[non_zero_index],(1,99)))


class AndorHyperSpecASIScan(ASIStage2DScan):
    
    name = "asi_hyperspec_scan"
    
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
        

