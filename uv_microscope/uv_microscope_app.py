from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from qtpy.QtWidgets import QVBoxLayout
import numpy as np

class UVMicroscopeApp(BaseMicroscopeApp):

    name = 'uv_microscope'
    
    def __init__(self, *args, **kwargs):
        if 'oo_not_andor' in kwargs.keys():
            self.oo_not_andor = kwargs['oo_not_andor']
        else:
            self.oo_not_andor = True
        BaseMicroscopeApp.__init__(self)
    
    def setup(self):
        # - renamed libiomp5md.dll to libiomp5md.dll.bak in Spinnaker
        
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'uv_quick_access.ui')))
        
        #### HARDWARE
        from ScopeFoundryHW.asi_stage import ASIStageHW
        asi_stage = self.add_hardware(ASIStageHW(self,swap_xy=False,invert_x=False,invert_y=True))
         
        from ScopeFoundryHW.oceanoptics_spec import OceanOpticsSpectrometerHW
        oo_spec = self.add_hardware(OceanOpticsSpectrometerHW(self))
        
#         from ScopeFoundryHW.thorcam import ThorCamHW
#         thorcamhw = self.add_hardware(ThorCamHW(self))
        
        from ScopeFoundryHW.flircam import FlirCamHW
        flircamhw = self.add_hardware(FlirCamHW(self))
        
        from ScopeFoundryHW.thorlabs_dc4100 import ThorlabsDC4100HW
        led_ctrl = self.add_hardware(ThorlabsDC4100HW(self))
        
        from ScopeFoundryHW.andor_camera import AndorCCDHW
        self.add_hardware(AndorCCDHW(self))
        
        from ScopeFoundryHW.andor_spec.andor_spec_hw import AndorShamrockSpecHW
        self.add_hardware(AndorShamrockSpecHW(self))
        
        from ScopeFoundryHW.lakeshore_331 import Lakeshore331HW
        self.add_hardware(Lakeshore331HW(self))
        
#         from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW, PowerMeterOptimizerMeasure
#         self.add_hardware(ThorlabsPowerMeterHW(self))
#         self.add_measurement(PowerMeterOptimizerMeasure(self))

        #### MEASUREMENTS
#         from ScopeFoundryHW.thorcam import ThorCamCaptureMeasure
#         thorcam = self.add_measurement(ThorCamCaptureMeasure(self))
        
        from ScopeFoundryHW.asi_stage import ASIStageControlMeasure
        asi_control = self.add_measurement(ASIStageControlMeasure(self))
        
        from ScopeFoundryHW.oceanoptics_spec import OOSpecLive, OOSpecOptimizerMeasure
        oo_spec_measure = self.add_measurement(OOSpecLive(self))
        oo_spec_opt = self.add_measurement(OOSpecOptimizerMeasure(self))
        
        from ScopeFoundryHW.andor_camera import AndorCCDReadoutMeasure
        self.add_measurement(AndorCCDReadoutMeasure)
           
        from confocal_measure.oceanoptics_asi_hyperspec_scan import OOHyperSpecASIScan
        oo_scan = self.add_measurement(OOHyperSpecASIScan(self))
           
        from ScopeFoundryHW.flircam import FlirCamLiveMeasure
        flircam = self.add_measurement(FlirCamLiveMeasure(self))
        
        from confocal_measure.andor_asi_hyperspec_scan import AndorAsiHyperSpec2DScan
        andor_scan = self.add_measurement(AndorAsiHyperSpec2DScan(self))

        
        ###### Quickbar connections #################################
        Q = self.quickbar
         
        # 2D Scan Area
        if self.oo_not_andor:
            oo_scan.settings.h0.connect_to_widget(Q.h0_doubleSpinBox)
            oo_scan.settings.h1.connect_to_widget(Q.h1_doubleSpinBox)
            oo_scan.settings.v0.connect_to_widget(Q.v0_doubleSpinBox)
            oo_scan.settings.v1.connect_to_widget(Q.v1_doubleSpinBox)
            oo_scan.settings.h_span.connect_to_widget(Q.hspan_doubleSpinBox)
            oo_scan.settings.v_span.connect_to_widget(Q.vspan_doubleSpinBox)
            Q.center_pushButton.clicked.connect(oo_scan.center_on_pos)
        else:
            andor_scan.settings.h0.connect_to_widget(Q.h0_doubleSpinBox)
            andor_scan.settings.h1.connect_to_widget(Q.h1_doubleSpinBox)
            andor_scan.settings.v0.connect_to_widget(Q.v0_doubleSpinBox)
            andor_scan.settings.v1.connect_to_widget(Q.v1_doubleSpinBox)
            andor_scan.settings.h_span.connect_to_widget(Q.hspan_doubleSpinBox)
            andor_scan.settings.v_span.connect_to_widget(Q.vspan_doubleSpinBox)
            Q.center_pushButton.clicked.connect(andor_scan.center_on_pos)
            
        scan_steps = [5e-3, 3e-3, 1e-3, 5e-4]
        scan_steps_labels = ['5.0 um','3.0 um','1.0 um','0.5 um']
        Q.scan_step_comboBox.addItems(scan_steps_labels)
        def apply_scan_step_value():
            if self.oo_not_andor:
                oo_scan.settings.dh.update_value(scan_steps[Q.scan_step_comboBox.currentIndex()])
                oo_scan.settings.dv.update_value(scan_steps[Q.scan_step_comboBox.currentIndex()])
            else:
                andor_scan.settings.dh.update_value(scan_steps[Q.scan_step_comboBox.currentIndex()])
                andor_scan.settings.dv.update_value(scan_steps[Q.scan_step_comboBox.currentIndex()])
        
        Q.scan_step_comboBox.currentIndexChanged.connect(apply_scan_step_value)
         
        # ASI Stage
        asi_stage.settings.x_position.connect_to_widget(Q.x_pos_doubleSpinBox)
        Q.x_up_pushButton.clicked.connect(asi_control.x_up)
        Q.x_down_pushButton.clicked.connect(asi_control.x_down)
  
        asi_stage.settings.y_position.connect_to_widget(Q.y_pos_doubleSpinBox)
        Q.y_up_pushButton.clicked.connect(asi_control.y_up)
        Q.y_down_pushButton.clicked.connect(asi_control.y_down)
  
        asi_stage.settings.z_position.connect_to_widget(Q.z_pos_doubleSpinBox)
        Q.z_up_pushButton.clicked.connect(asi_control.z_up)
        Q.z_down_pushButton.clicked.connect(asi_control.z_down)
         
        asi_control.settings.jog_step_xy.connect_to_widget(Q.xy_step_doubleSpinBox)
        asi_control.settings.jog_step_z.connect_to_widget(Q.z_step_doubleSpinBox)
         
        stage_steps = np.array([5e-4, 1e-3, 1e-2, 1e-1, 1e0])
        stage_steps_labels = ['0.0005 mm','0.001 mm','0.010 mm','0.100 mm','1.000 mm']
        Q.xy_step_comboBox.addItems(stage_steps_labels)
        Q.z_step_comboBox.addItems(stage_steps_labels)
         
        def apply_xy_step_value():
            asi_control.settings.jog_step_xy.update_value(stage_steps[Q.xy_step_comboBox.currentIndex()])
        Q.xy_step_comboBox.currentIndexChanged.connect(apply_xy_step_value)
         
        def apply_z_step_value():   
            asi_control.settings.jog_step_z.update_value(stage_steps[Q.z_step_comboBox.currentIndex()])
        Q.z_step_comboBox.currentIndexChanged.connect(apply_z_step_value)
         
        def halt_stage_motion():
            asi_stage.halt_xy()
            asi_stage.halt_z()
        Q.stop_stage_pushButton.clicked.connect(halt_stage_motion)
     
        # OO Spectrometer
        oo_spec.settings.int_time.connect_to_widget(Q.oo_spec_int_time_doubleSpinBox)
        oo_spec_measure.settings.continuous.connect_to_widget(Q.oo_spec_acquire_cont_checkBox)
        Q.oo_spec_set_bg_pushButton.clicked.connect(oo_spec_measure.set_current_spec_as_bg)
        Q.oo_spec_save_pushButton.clicked.connect(oo_spec_measure.save_data)
        Q.oo_spec_startstop_pushButton.clicked.connect(oo_spec_measure.start_stop)
         
        # OO Spectrometer Optimizer
        oo_spec_opt.settings.power_reading.connect_to_widget(Q.power_meter_power_label)
        oo_spec_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)
                 
        # Flircam
        flircam.settings.activation.connect_to_widget(Q.flircam_live_checkBox)
        flircam.settings.auto_level.connect_to_widget(Q.flircam_autolevel_checkBox)
        flircamhw.settings.exposure.connect_to_widget(Q.flircam_int_time_doubleSpinBox)
        
        Q.flircam_auto_exp_comboBox.addItems(["Off","Once","Continuous"])
        Q.flircam_auto_exp_comboBox.setCurrentIndex(2)
        def apply_auto_exposure_index():
            flircam.ui.auto_exposure_comboBox.setCurrentIndex(Q.flircam_auto_exp_comboBox.currentIndex())
        Q.flircam_auto_exp_comboBox.currentIndexChanged.connect(apply_auto_exposure_index)
        
        self.imlayout = QVBoxLayout()
        def switch_camera_view():
            self.imlayout.addWidget(flircam.imview)
            flircam.imview.show() 
        Q.flircam_show_pushButton.clicked.connect(switch_camera_view)
        Q.groupBox_image.setLayout(self.imlayout)
        
        # Thorlabs DC4100 LED controller
        led_ctrl.settings.LED1.connect_to_widget(Q.led1_checkBox)
        led_ctrl.settings.get_lq('LED1 wavelength').connect_to_widget(Q.led1_lineEdit)
        led_ctrl.settings.get_lq('LED1 brightness').connect_to_widget(Q.led1_doubleSpinBox)
        led_ctrl.settings.get_lq('LED1 brightness').connect_to_widget(Q.led1_horizontalSlider)
        led_ctrl.settings.LED2.connect_to_widget(Q.led2_checkBox)
        led_ctrl.settings.get_lq('LED2 wavelength').connect_to_widget(Q.led2_lineEdit)
        led_ctrl.settings.get_lq('LED2 brightness').connect_to_widget(Q.led2_doubleSpinBox)
        led_ctrl.settings.get_lq('LED2 brightness').connect_to_widget(Q.led2_horizontalSlider)

        
        '''
        # Thorcam
        Q.thorcam_start_pushButton.clicked.connect(thorcam.start)
        Q.thorcam_stop_pushButton.clicked.connect(thorcam.interrupt)
        thorcam.settings.img_max.connect_to_widget(Q.thorcam_max_doubleSpinBox)
        thorcam.settings.img_min.connect_to_widget(Q.thorcam_min_doubleSpinBox)
        thorcamhw.settings.exp_time.connect_to_widget(Q.thorcam_int_time_doubleSpinBox)
        thorcamhw.settings.gain.connect_to_widget(Q.thorcam_gain_doubleSpinBox)
        thorcamhw.settings.pixel_clock.connect_to_widget(Q.thorcam_clock_doubleSpinBox)
         
        self.imlayout = QVBoxLayout()
        def switch_camera_view():
            self.imlayout.addWidget(thorcam.imview)
            thorcam.imview.show() 
        Q.thorcam_show_pushButton.clicked.connect(switch_camera_view)
        Q.groupBox_image.setLayout(self.imlayout)
        '''
                 
        self.settings_load_ini('uv_defaults.ini')

if __name__ == '__main__':
    import sys
    app = UVMicroscopeApp(sys.argv, oo_not_andor=True)
    sys.exit(app.exec_())