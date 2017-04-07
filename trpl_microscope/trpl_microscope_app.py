from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

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


    
        ########################## MEASUREMENTS
        print("Adding Measurement Components")
        from confocal_measure.apd_mcl_2dslowscan import APD_MCL_2DSlowScan, APD_MCL_3DSlowScan
        self.add_measurement(APD_MCL_2DSlowScan)
        self.add_measurement(APD_MCL_3DSlowScan)
        
        #self.apd_optimizer_measure = self.add_measurement_component(APDOptimizerMeasurement(self))        
        #self.add_measurement_component(APD_MCL_2DSlowScan(self))
        
        
        #self.add_measurement_component(WinSpecRemoteReadout(self))
        #self.add_measurement_component(WinSpecMCL2DSlowScan(self))
        
        
        ####### Quickbar connections
        Q = self.quickbar
        
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
        
        
        # power meter
        pm = self.hardware['thorlabs_powermeter']
        pm.settings.wavelength.connect_to_widget(Q.power_meter_wl_doubleSpinBox)
        pm.settings.power.connect_to_widget(Q.power_meter_power_label)
        
        pm_opt = self.measurements['powermeter_optimizer']
        pm_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)
        
        
        # ANDOR
        #self.gui.ui.andor_ccd_acquire_cont_checkBox.stateChanged.connect(self.start_stop)
        #self.gui.ui.andor_ccd_acq_bg_pushButton.clicked.connect(self.acquire_bg_start)
        #self.gui.ui.andor_ccd_read_single_pushButton.clicked.connect(self.acquire_single_start)
        #        self.bg_subtract.connect_bidir_to_widget(self.gui.ui.andor_ccd_bgsub_checkBox)
        
        
        shutter = self.hardware['shutter_servo']
        shutter.settings.shutter_open.connect_to_widget(Q.shutter_open_checkBox)
        
        self.hardware['flip_mirror'].settings.mirror_position.connect_to_widget(Q.flip_mirror_checkBox)
        
        ##########
        self.settings_load_ini('trpl_defaults.ini')

if __name__ == '__main__':
    import sys
    app = TRPLMicroscopeApp(sys.argv)
    sys.exit(app.exec_())