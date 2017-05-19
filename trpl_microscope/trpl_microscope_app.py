from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='DEBUG')#, filename='m3_log.txt')
#logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)

class TRPLMicroscopeApp(BaseMicroscopeApp):

    name = 'trpl_microscope'
    
    def setup(self):
        
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'trpl_quick_access.ui')))
        
        print("Adding Hardware Components")
        from ScopeFoundryHW.picoharp import PicoHarpHW
        self.add_hardware(PicoHarpHW(self))
        
        from ScopeFoundryHW.apd_counter import APDCounterHW, APDOptimizerMeasure
        self.add_hardware(APDCounterHW(self))
        self.add_measurement(APDOptimizerMeasure(self))

        from ScopeFoundryHW.andor_camera import AndorCCDHW, AndorCCDReadoutMeasure
        self.add_hardware(AndorCCDHW(self))
        self.add_measurement(AndorCCDReadoutMeasure)

        
        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))
        
        from ScopeFoundryHW.flip_mirror_arduino import FlipMirrorHW
        self.add_hardware(FlipMirrorHW(self))
        
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW, PowerMeterOptimizerMeasure
        self.add_hardware(ThorlabsPowerMeterHW(self))
        self.add_measurement(PowerMeterOptimizerMeasure(self))
                
        #self.thorlabs_powermeter_analog_readout_hc = self.add_hardware_component(ThorlabsPowerMeterAnalogReadOut(self))

        from ScopeFoundryHW.mcl_stage.mcl_xyz_stage import MclXYZStageHW
        self.add_hardware(MclXYZStageHW(self))
        
        #from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        #self.add_hardware(KeithleySourceMeterComponent)

        
        #self.srs_lockin_hc = self.add_hardware_component(SRSLockinComponent(self))
        
        #self.thorlabs_optical_chopper_hc = self.add_hardware_component(ThorlabsOpticalChopperComponent(self))        
        
        from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        self.power_wheel = self.add_hardware_component(PowerWheelArduinoHW(self))
        
        #self.oceanoptics_spec_hc = self.add_hardware_component(OceanOpticsSpectrometerHC(self))
        
        #self.crystaltech_aotf_hc = self.add_hardware_component(CrystalTechAOTF(self))
        
        from ScopeFoundryHW.shutter_servo_arduino.shutter_servo_arduino_hc import ShutterServoHW
        self.add_hardware(ShutterServoHW(self))
        
        from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))


    
        ########################## MEASUREMENTS
        print("Adding Measurement Components")
        
        
        # hardware specific measurements
        
        from ScopeFoundryHW.picoharp.picoharp_hist_measure import PicoHarpHistogramMeasure
        self.add_measurement(PicoHarpHistogramMeasure(self))

        # Combined Measurements
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement_component(PowerScanMeasure(self))        

        # Mapping Measurements        
        from confocal_measure.apd_mcl_2dslowscan import APD_MCL_2DSlowScan, APD_MCL_3DSlowScan
        self.add_measurement(APD_MCL_2DSlowScan)
        self.add_measurement(APD_MCL_3DSlowScan)
        
        from confocal_measure import Picoharp_MCL_2DSlowScan
        self.add_measurement_component(Picoharp_MCL_2DSlowScan(self))
                
        ####### Quickbar connections #################################
        
        Q = self.quickbar
        
        
        # MadCity Labs
        mcl = self.hardware['mcl_xyz_stage']

        mcl.settings.x_position.connect_to_widget(Q.cx_doubleSpinBox)
        Q.x_set_lineEdit.returnPressed.connect(mcl.settings.x_target.update_value)
        Q.x_set_lineEdit.returnPressed.connect(lambda: Q.x_set_lineEdit.setText(""))

        mcl.settings.y_position.connect_to_widget(Q.cy_doubleSpinBox)
        Q.y_set_lineEdit.returnPressed.connect(mcl.settings.y_target.update_value)
        Q.y_set_lineEdit.returnPressed.connect(lambda: Q.y_set_lineEdit.setText(""))

        mcl.settings.z_position.connect_to_widget(Q.cz_doubleSpinBox)
        Q.z_set_lineEdit.returnPressed.connect(mcl.settings.z_target.update_value)
        Q.z_set_lineEdit.returnPressed.connect(lambda: Q.z_set_lineEdit.setText(""))

        mcl.settings.move_speed.connect_to_widget(Q.nanodrive_move_slow_doubleSpinBox)        
        
        # Power Wheel
        pw = self.hardware['power_wheel_arduino']
        pw.settings.encoder_pos.connect_to_widget(Q.power_wheel_encoder_pos_doubleSpinBox)
        pw.settings.move_steps.connect_to_widget(Q.powerwheel_move_steps_doubleSpinBox)
        Q.powerwheel_move_fwd_pushButton.clicked.connect(pw.move_fwd)
        Q.powerwheel_move_bkwd_pushButton.clicked.connect(pw.move_bkwd)

        #connect events
        apd = self.hardware['apd_counter']
        apd.settings.int_time.connect_to_widget(Q.apd_counter_int_doubleSpinBox)
        apd.settings.apd_count_rate.updated_text_value.connect(
                                           Q.apd_counter_output_lineEdit.setText)
        

        apd_opt = self.measurements['apd_optimizer']
        #apd.settings
        apd_opt.settings.activation.connect_to_widget(Q.apd_optimize_startstop_checkBox)
        #self.measurement_state_changed[bool].connect(self.gui.ui.apd_optimize_startstop_checkBox.setChecked)
        
        # Spectrometer
        aspec = self.hardware['acton_spectrometer']
        aspec.settings.center_wl.connect_to_widget(Q.acton_spec_center_wl_doubleSpinBox)
        aspec.settings.exit_mirror.connect_to_widget(Q.acton_spec_exitmirror_comboBox)
        aspec.settings.grating_name.connect_to_widget(Q.acton_spec_grating_lineEdit)        
        
        # Andor CCD
        andor = self.hardware['andor_ccd']
        andor.settings.exposure_time.connect_to_widget(Q.andor_ccd_int_time_doubleSpinBox)
        andor.settings.em_gain.connect_to_widget(Q.andor_ccd_emgain_doubleSpinBox)
        andor.settings.temperature.connect_to_widget(Q.andor_ccd_temp_doubleSpinBox)
        andor.settings.ccd_status.connect_to_widget(Q.andor_ccd_status_label)
        andor.settings.shutter_open.connect_to_widget(Q.andor_ccd_shutter_open_checkBox)

        
        # Andor Readout
        aro = self.measurements['andor_ccd_readout']
        aro.settings.bg_subtract.connect_to_widget(Q.andor_ccd_bgsub_checkBox)
        Q.andor_ccd_acquire_cont_checkBox.stateChanged.connect(aro.start_stop)
        Q.andor_ccd_acq_bg_pushButton.clicked.connect(aro.acquire_bg_start)
        Q.andor_ccd_read_single_pushButton.clicked.connect(aro.acquire_single_start)
        
        
        
        # power meter
        pm = self.hardware['thorlabs_powermeter']
        pm.settings.wavelength.connect_to_widget(Q.power_meter_wl_doubleSpinBox)
        pm.settings.power.connect_to_widget(Q.power_meter_power_label)
        
        pm_opt = self.measurements['powermeter_optimizer']
        pm_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)
        
        
        
        shutter = self.hardware['shutter_servo']
        shutter.settings.shutter_open.connect_to_widget(Q.shutter_open_checkBox)
        
        self.hardware['flip_mirror'].settings.mirror_position.connect_to_widget(Q.flip_mirror_checkBox)
        
        ##########
        self.settings_load_ini('trpl_defaults.ini')

if __name__ == '__main__':
    import sys
    app = TRPLMicroscopeApp(sys.argv)
    sys.exit(app.exec_())