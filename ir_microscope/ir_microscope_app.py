from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging
from ScopeFoundryHW import attocube_ecc100
import ScopeFoundryHW
from ir_microscope.measurements import apd_scan, hyperspectral_scan,\
    picoharp_attocube_slow_scans
from ir_microscope import measurements


logging.basicConfig(level='DEBUG')#, filename='m3_log.txt')
#logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)


class IRMicroscopeApp(BaseMicroscopeApp):

    name = 'ir_microscope'
    
    def setup(self):
        
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'ir_quick_access.ui')))
        
        print("Adding Hardware Components")
        
        import ScopeFoundryHW.picoharp as ph
        self.add_hardware(ph.PicoHarpHW(self))

        from ScopeFoundryHW.winspec_remote import WinSpecRemoteClientHW
        self.add_hardware_component(WinSpecRemoteClientHW(self))
        
        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))
                
        from ScopeFoundryHW.tenma_power.tenma_hw import TenmaHW
        self.add_hardware(TenmaHW(self))


        #from ScopeFoundryHW.apd_counter import APDCounterHW
        #self.add_hardware(APDCounterHW(self))
        
        #from ScopeFoundryHW.acton_spec.acton_spec import ActonSpectrometerHW
        #self.add_hardware(ActonSpectrometerHW(self))


        from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        self.power_wheel = self.add_hardware_component(PowerWheelArduinoHW(self))    
        
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))

        from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))

        from ScopeFoundryHW.pololu_servo.pololu_hw import PololuHW
        self.add_hardware(PololuHW(self))        
        
        from ScopeFoundryHW.attocube_ecc100.attocube_xyz_hw import AttoCubeXYZStageHW
        self.add_hardware(AttoCubeXYZStageHW(self))                        
              
        from ScopeFoundryHW.powermate.powermate_hw import PowermateHW
        self.add_hardware(PowermateHW(self))
        
        from ScopeFoundryHW.thorlabs_motorized_filter_flipper.thorlabsMFF_hardware import ThorlabsMFFHW
        self.add_hardware_component(ThorlabsMFFHW(self))        
        
        from ScopeFoundryHW.xbox_controller.xbox_controller_hw import XboxControllerHW
        self.add_hardware(XboxControllerHW(self))
        
        
                        
        print("Adding Measurement Components")

        self.add_measurement(ph.PicoHarpChannelOptimizer(self))
        self.add_measurement(ph.PicoHarpHistogramMeasure(self))
        self.add_measurement(picoharp_attocube_slow_scans.Picoharp_AttoCube_2DSlowScan(self))
        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteReadoutMeasure
        self.add_measurement_component(WinSpecRemoteReadoutMeasure(self))
        self.add_measurement(hyperspectral_scan.M4Hyperspectral2DScan(self))
        
        #self.add_measurement(apd_scan.M4APDScanPhMeasure(self))
        
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement_component(PowerScanMeasure(self))
        
        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement_component(PowerMeterOptimizerMeasure(self))    
 
        from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
        self.add_measurement(AttoCubeStageControlMeasure(self))

        from ScopeFoundryHW.powermate.powermate_measure import PowermateMeasure
        self.add_measurement(PowermateMeasure(self))
        
        from ScopeFoundryHW.attocube_ecc100.attocube_home_axis_measurement import AttoCubeHomeAxisMeasurement
        self.add_measurement(AttoCubeHomeAxisMeasurement(self))
        from measurements.stage_motion_measure import StageHomeAxesMeasure
        self.add_measurement(StageHomeAxesMeasure(self))
        
        
        from measurements.xbox_controller_measure import XboxControllerMeasure
        self.add_measurement(XboxControllerMeasure(self))
        
        
        #from ScopeFoundryHW.xbox_controller.xbox_controller_test_measure import 
        
        ####### Quickbar connections #################################
        
        Q = self.quickbar
        
        # Powermate
        pm_measure = self.measurements['powermate_measure'] 
        pm_measure.settings.dev_0_lq_path_moved.connect_to_widget(Q.powermate_0_comboBox)
        pm_measure.settings.dev_1_lq_path_moved.connect_to_widget(Q.powermate_1_comboBox)

        # LED
        tenmaHW = self.hardware['tenma_powersupply']
        Q.tenma_power_on_pushButton.clicked.connect(lambda: tenmaHW.write_both(V=3.0,I=0.1,impose_connection=True))
        Q.tenma_power_off_pushButton.clicked.connect(tenmaHW.zero_both)
        
        tenmaHW.settings.actual_current.connect_to_widget(Q.tenma_power_current_doubleSpinBox)
        Q.tenma_power_current_plus_pushButton.clicked.connect(lambda: tenmaHW.write_delta_current(delta = 0.05))
        Q.tenma_power_current_minus_pushButton.clicked.connect(lambda: tenmaHW.write_delta_current(delta = -0.05))
        Q.tenma_power_current_lineEdit.returnPressed.connect(tenmaHW.settings.set_current.update_value)
        Q.tenma_power_current_lineEdit.returnPressed.connect(lambda: Q.tenma_power_current_lineEdit.setText(""))

        tenmaHW.settings.actual_voltage.connect_to_widget(Q.tenma_power_voltage_doubleSpinBox)
        Q.tenma_power_voltage_plus_pushButton.clicked.connect(lambda: tenmaHW.write_delta_voltage(delta = 0.2))
        Q.tenma_power_voltage_minus_pushButton.clicked.connect(lambda: tenmaHW.write_delta_voltage(delta = -0.2))
        Q.tenma_power_voltage_lineEdit.returnPressed.connect(tenmaHW.settings.set_voltage.update_value)
        Q.tenma_power_voltage_lineEdit.returnPressed.connect(lambda: Q.tenma_power_voltage_lineEdit.setText(""))
        
        # Atto Cube
        stage = self.hardware['attocube_xyz_stage']

        stage.settings.x_position.connect_to_widget(Q.cx_doubleSpinBox)
        Q.x_set_lineEdit.returnPressed.connect(stage.settings.x_target_position.update_value)
        Q.x_set_lineEdit.returnPressed.connect(lambda: Q.x_set_lineEdit.setText(""))

        stage.settings.y_position.connect_to_widget(Q.cy_doubleSpinBox)
        Q.y_set_lineEdit.returnPressed.connect(stage.settings.y_target_position.update_value)
        Q.y_set_lineEdit.returnPressed.connect(lambda: Q.y_set_lineEdit.setText(""))

        stage.settings.z_position.connect_to_widget(Q.cz_doubleSpinBox)
        Q.z_set_lineEdit.returnPressed.connect(stage.settings.z_target_position.update_value)
        Q.z_set_lineEdit.returnPressed.connect(lambda: Q.z_set_lineEdit.setText(""))

        self.measurements['AttoCubeStageControlMeasure'].settings.activation.connect_to_widget(Q.stage_live_update_checkBox)
        #stage.settings.move_speed.connect_to_widget(Q.nanodrive_move_slow_doubleSpinBox)   
        
        #acton spectrometer
        acton_spec = self.hardware['acton_spectrometer']
        acton_spec.settings.center_wl.connect_to_widget(Q.center_wl_doubleSpinBox)
        acton_spec.settings.grating_id.connect_to_widget(Q.grating_id_comboBox)
        
        #connect events
        #apd = self.hardware['apd_counter']
        #apd.settings.int_time.connect_to_widget(Q.apd_counter_int_doubleSpinBox)
        #apd.settings.apd_count_rate.updated_text_value.connect(
                                           #Q.apd_counter_output_lineEdit.setText)
        

        #apd_opt = self.measurements['apd_optimizer']
        #apd.settings
        #apd_opt.settings.activation.connect_to_widget(Q.apd_optimize_startstop_checkBox)
        #self.measurement_state_changed[bool].connect(self.gui.ui.apd_optimize_startstop_checkBox.setChecked)         
        
        # power meter
        pm = self.hardware['thorlabs_powermeter']
        pm.settings.wavelength.connect_to_widget(Q.power_meter_wl_doubleSpinBox)
        pm.settings.power.connect_to_widget(Q.power_meter_power_label)
        
        pm_opt = self.measurements['powermeter_optimizer']
        pm_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)
        
        # Power Wheel
        pw = self.hardware['power_wheel_arduino']
        pw.settings.encoder_pos.connect_to_widget(Q.power_wheel_encoder_pos_doubleSpinBox)
        pw.settings.move_steps.connect_to_widget(Q.powerwheel_move_steps_doubleSpinBox)
        Q.powerwheel_move_fwd_pushButton.clicked.connect(pw.move_fwd)
        Q.powerwheel_move_bkwd_pushButton.clicked.connect(pw.move_bkwd)


        # Thorlabs Flip Mirror
        MFF = self.hardware['thorlabs_MFF']
        MFF.settings.pos.connect_to_widget(Q.thorlabs_MFF_comboBox)
        
        # shutter
        shutter = self.hardware['pololu_servo_hw']
        shutter.settings.servo2_toggle.connect_to_widget(Q.shutter_open_checkBox)
               
        

        """
        # Andor CCD
        andor = self.hardware['andor_ccd']
        andor.settings.exposure_time.connect_to_widget(Q.andor_ccd_int_time_doubleSpinBox)
        andor.settings.em_gain.connect_to_widget(Q.andor_ccd_emgain_doubleSpinBox)
        andor.settings.temperature.connect_to_widget(Q.andor_ccd_temp_doubleSpinBox)
        andor.settings.ccd_status.connect_to_widget(Q.andor_ccd_status_label)
        andor.settings.shutter_open.connect_to_widget(Q.andor_ccd_shutter_open_checkBox)  
        
        # Spectrometer
        aspec = self.hardware['acton_spectrometer']
        aspec.settings.center_wl.connect_to_widget(Q.acton_spec_center_wl_doubleSpinBox)
        aspec.settings.exit_mirror.connect_to_widget(Q.acton_spec_exitmirror_comboBox)
        aspec.settings.grating_name.connect_to_widget(Q.acton_spec_grating_lineEdit)                
        
        
        #connect events
        apd = self.hardware['apd_counter']
        apd.settings.int_time.connect_to_widget(Q.apd_counter_int_doubleSpinBox)
        apd.settings.apd_count_rate.updated_text_value.connect(
                                           Q.apd_counter_output_lineEdit.setText)
        

        #apd_opt = self.measurements['apd_optimizer']
        #apd.settings
        #apd_opt.settings.activation.connect_to_widget(Q.apd_optimize_startstop_checkBox)
        #self.measurement_state_changed[bool].connect(self.gui.ui.apd_optimize_startstop_checkBox.setChecked)      
        """
        
        ##########
        self.settings_load_ini('ir_microscope_defaults.ini')

if __name__ == '__main__':
    import sys
    app = IRMicroscopeApp(sys.argv)
    sys.exit(app.exec_())