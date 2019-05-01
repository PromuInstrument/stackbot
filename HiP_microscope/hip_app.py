import sys
from ScopeFoundry import BaseMicroscopeApp
import time
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import numpy as np
# Import Hardware Components
#from hardware_components.dummy_xy_stage import DummyXYStage

# Import Measurement Components

#from HiP_microscope.measure.hip_dual_temperature import HiPMicroscopeDualTemperature

class HiPMicroscopeApp(BaseMicroscopeApp):

    name = "HiP_Microscope"

    #ui_filename = "base_gui.ui"

    def setup(self):
        
        #Add hardware components
        from ScopeFoundryHW.mcl_stage import MclXYZStageHW
        self.add_hardware_component(MclXYZStageHW(self))

        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware_component(ActonSpectrometerHW(self))
        
        from ScopeFoundryHW.picam import PicamHW, PicamReadoutMeasure
        self.add_hardware_component(PicamHW(self))
        self.add_measurement_component(PicamReadoutMeasure(self))
        
        from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
        asi_stage = self.add_hardware(ASIStageHW(self))
        from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
        asi_control = self.add_measurement(ASIStageControlMeasure(self))

        from ScopeFoundryHW.pololu_servo.single_servo_hw import PololuMaestroServoHW
        self.add_hardware(PololuMaestroServoHW(self, name='power_wheel'))
        
        #from hardware_components.omega_pt_pid_controller import OmegaPtPIDControllerHardware        
        #self.add_hardware_component(OmegaPtPIDControllerHardware(self))
        
        #Add measurement components
        print("Create Measurement objects")
        from HiP_microscope.measure.hyperspec_picam_mcl import HyperSpecPicam2DScan, HyperSpecPicam3DStack
        self.add_measurement(HyperSpecPicam2DScan(self))
        #self.add_measurement_component(HiPMicroscopeDualTemperature(self))
        self.add_measurement(HyperSpecPicam3DStack(self))
        
        
        from HiP_microscope.measure.picam_calibration_sweep import PicamCalibrationSweep
        self.add_measurement(PicamCalibrationSweep(self))        
        
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW, PowerMeterOptimizerMeasure
        self.add_hardware(ThorlabsPowerMeterHW(self))
        self.add_measurement(PowerMeterOptimizerMeasure(self))

        from ScopeFoundryHW.pygrabber_camera import PyGrabberCameraHW, PyGrabberCameraLiveMeasure
        self.add_hardware(PyGrabberCameraHW(self))
        self.add_measurement(PyGrabberCameraLiveMeasure(self))
        

        from ScopeFoundryHW.toupcam import  ToupCamHW, ToupCamLiveMeasure
        self.add_hardware(ToupCamHW(self))
        self.add_measurement(ToupCamLiveMeasure(self))
        
        #set some default logged quantities
        #self.hardware_components['apd_counter'].debug_mode.update_value(True)
        #self.hardware_components['apd_counter'].dummy_mode.update_value(True)
        #self.hardware_components['apd_counter'].connected.update_value(True)

        
        ###### Quickbar connections #################################
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'hip_quick_access.ui')))
        Q = self.quickbar
         
        # 2D Scan Area
#         oo_scan.settings.h0.connect_to_widget(Q.h0_doubleSpinBox)
#         oo_scan.settings.h1.connect_to_widget(Q.h1_doubleSpinBox)
#         oo_scan.settings.v0.connect_to_widget(Q.v0_doubleSpinBox)
#         oo_scan.settings.v1.connect_to_widget(Q.v1_doubleSpinBox)
#         oo_scan.settings.h_span.connect_to_widget(Q.hspan_doubleSpinBox)
#         oo_scan.settings.v_span.connect_to_widget(Q.vspan_doubleSpinBox)
#        Q.center_pushButton.clicked.connect(oo_scan.center_on_pos)
#        scan_steps = [5e-3, 3e-3, 1e-3, 5e-4]
#        scan_steps_labels = ['5.0 um','3.0 um','1.0 um','0.5 um']
#         Q.scan_step_comboBox.addItems(scan_steps_labels)
#         def apply_scan_step_value():
#             oo_scan.settings.dh.update_value(scan_steps[Q.scan_step_comboBox.currentIndex()])
#             oo_scan.settings.dv.update_value(scan_steps[Q.scan_step_comboBox.currentIndex()])
#         Q.scan_step_comboBox.currentIndexChanged.connect(apply_scan_step_value)
        
        # MCL Stage
        mcl = self.hardware['mcl_xyz_stage']
        mcl.settings.x_position.connect_to_widget(Q.mcl_x_pos_doubleSpinBox)
        mcl.settings.y_position.connect_to_widget(Q.mcl_y_pos_doubleSpinBox)
        mcl.settings.z_position.connect_to_widget(Q.mcl_z_pos_doubleSpinBox)
        mcl.settings.x_target.connect_to_widget(Q.mcl_x_target_doubleSpinBox)
        mcl.settings.y_target.connect_to_widget(Q.mcl_y_target_doubleSpinBox)
        mcl.settings.z_target.connect_to_widget(Q.mcl_z_target_doubleSpinBox)
        mcl.settings.connected.connect_to_widget(Q.mcl_connect_checkBox)
        
        # ASI Stage
        asi_stage.settings.x_position.connect_to_widget(Q.x_pos_doubleSpinBox)
        Q.x_up_pushButton.clicked.connect(asi_control.x_up)
        Q.x_down_pushButton.clicked.connect(asi_control.x_down)
  
        asi_stage.settings.y_position.connect_to_widget(Q.y_pos_doubleSpinBox)
        Q.y_up_pushButton.clicked.connect(asi_control.y_up)
        Q.y_down_pushButton.clicked.connect(asi_control.y_down)
  
#         asi_stage.settings.z_position.connect_to_widget(Q.z_pos_doubleSpinBox)
#         Q.z_up_pushButton.clicked.connect(asi_control.z_up)
#         Q.z_down_pushButton.clicked.connect(asi_control.z_down)
         
        asi_control.settings.jog_step_xy.connect_to_widget(Q.xy_step_doubleSpinBox)
#         asi_control.settings.jog_step_z.connect_to_widget(Q.z_step_doubleSpinBox)
         
        stage_steps = np.array([5e-4, 1e-3, 1e-2, 1e-1, 1e0])
        stage_steps_labels = ['0.0005 mm','0.001 mm','0.010 mm','0.100 mm','1.000 mm']
        Q.xy_step_comboBox.addItems(stage_steps_labels)
#         Q.z_step_comboBox.addItems(stage_steps_labels)
         
        def apply_xy_step_value():
            asi_control.settings.jog_step_xy.update_value(stage_steps[Q.xy_step_comboBox.currentIndex()])
        Q.xy_step_comboBox.currentIndexChanged.connect(apply_xy_step_value)
         
        def apply_z_step_value():   
            asi_control.settings.jog_step_z.update_value(stage_steps[Q.z_step_comboBox.currentIndex()])
        #Q.z_step_comboBox.currentIndexChanged.connect(apply_z_step_value)
         
        def halt_stage_motion():
            asi_stage.halt_xy()
            asi_stage.halt_z()
        Q.stop_stage_pushButton.clicked.connect(halt_stage_motion)

        asi_stage.settings.x_target.connect_to_widget(Q.asi_x_target_doubleSpinBox)
        asi_stage.settings.y_target.connect_to_widget(Q.asi_y_target_doubleSpinBox)

        #Q.asi_xy_target_groupBox.toggled.connect(Q.asi_xy_target_groupBox.setEnabled)

        # Power Wheel
        #pw = self.hardware['power_wheel_arduino']
        pw = self.hardware['power_wheel']
        pw.settings.position.connect_to_widget(Q.power_wheel_encoder_pos_doubleSpinBox)
        pw.settings.jog_step.connect_to_widget(Q.powerwheel_move_steps_doubleSpinBox)
        Q.powerwheel_move_fwd_pushButton.clicked.connect(pw.jog_fwd)
        Q.powerwheel_move_bkwd_pushButton.clicked.connect(pw.jog_bkwd)


        # Picam
        picam = self.hardware['picam']
        picam.settings.ccd_status.connect_to_widget(Q.andor_ccd_status_label)
        picam.settings.SensorTemperatureReading.connect_to_widget(Q.andor_ccd_temp_doubleSpinBox)
        picam.settings.ExposureTime.connect_to_widget(Q.andor_ccd_int_time_doubleSpinBox)


        # Spectrometer
        aspec = self.hardware['acton_spectrometer']
        aspec.settings.center_wl.connect_to_widget(Q.acton_spec_center_wl_doubleSpinBox)
        aspec.settings.exit_mirror.connect_to_widget(Q.acton_spec_exitmirror_comboBox)
        aspec.settings.grating_name.connect_to_widget(Q.acton_spec_grating_lineEdit)        
        
        # power meter
        pm = self.hardware['thorlabs_powermeter']
        pm.settings.wavelength.connect_to_widget(Q.power_meter_wl_doubleSpinBox)
        pm.settings.power.connect_to_widget(Q.power_meter_power_label)
        
        pm_opt = self.measurements['powermeter_optimizer']
        pm_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)




        # load default settings from file
        self.settings_load_ini("hip_settings.ini")


    def setup_ui(self):
        self.hardware['mcl_xyz_stage'].settings['connected']=True
        #self.hardware['picam'].settings['connected']=True
        #time.sleep(0.5)
        #self.hardware['picam'].settings['roi_y_bin'] = 100
        #self.hardware['picam'].commit_parameters()
        
        #self.hardware['acton_spectrometer'].settings['connected']=True
        self.hardware['asi_stage'].settings['connected'] = True
        
        
        #self.set_subwindow_mode()


if __name__ == '__main__':

    app = HiPMicroscopeApp(sys.argv)
    #app.tile_layout()
    sys.exit(app.exec_())