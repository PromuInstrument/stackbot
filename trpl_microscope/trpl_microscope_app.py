from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='WARNING')#, filename='m3_log.txt')
#logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class TRPLMicroscopeApp(BaseMicroscopeApp):

    name = 'trpl_microscope'
    
    def setup(self):
        
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'trpl_quick_access.ui')))
        
        print("Adding Hardware Components")
        from ScopeFoundryHW.picoharp import PicoHarpHW
        self.add_hardware(PicoHarpHW(self))
        
        #from ScopeFoundryHW.apd_counter import APDCounterHW, APDOptimizerMeasure
        #self.add_hardware(APDCounterHW(self))
        #self.add_measurement(APDOptimizerMeasure(self))
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement_component(APDOptimizerCBMeasurement(self))

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
        
        from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        self.add_hardware(KeithleySourceMeterComponent(self))

        
        #self.srs_lockin_hc = self.add_hardware_component(SRSLockinComponent(self))
        
        #self.thorlabs_optical_chopper_hc = self.add_hardware_component(ThorlabsOpticalChopperComponent(self))        
        
        #from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        #self.power_wheel = self.add_hardware_component(PowerWheelArduinoHW(self))
        from ScopeFoundryHW.pololu_servo.single_servo_hw import PololuMaestroServoHW
        self.add_hardware(PololuMaestroServoHW(self, name='power_wheel'))
        
        from ScopeFoundryHW.oceanoptics_spec.oceanoptics_spec import OceanOpticsSpectrometerHW
        self.add_hardware_component(OceanOpticsSpectrometerHW(self))
        
        #self.crystaltech_aotf_hc = self.add_hardware_component(CrystalTechAOTF(self))
        
        from ScopeFoundryHW.shutter_servo_arduino.shutter_servo_arduino_hc import ShutterServoHW
        self.add_hardware(ShutterServoHW(self))
        
        from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))

        from ScopeFoundryHW.quantum_composer import QuantumComposerHW
        self.add_hardware(QuantumComposerHW(self))

        from ScopeFoundryHW.toupcam import ToupCamHW, ToupCamLiveMeasure
        self.add_hardware_component(ToupCamHW(self))
        
        from ScopeFoundryHW.powermate.powermate_hw import PowermateHW
        self.add_hardware(PowermateHW(self))
        
        from ScopeFoundryHW.asi_stage import ASIStageHW, ASIStageControlMeasure
        self.add_hardware(ASIStageHW(self))
        self.add_measurement(ASIStageControlMeasure(self))
        
        from xbox_trpl_measure import XboxControllerTRPLMeasure
        from ScopeFoundryHW.xbox_controller.xbox_controller_hw import XboxControllerHW
        self.add_hardware(XboxControllerHW(self))
        self.add_measurement(XboxControllerTRPLMeasure(self))

        from ScopeFoundryHW.crystaltech_aotf.crystaltech_aotf_hc import CrystalTechAOTF 
        self.add_hardware(CrystalTechAOTF(self))
        
        from ScopeFoundryHW.linkam_thermal_stage.linkam_temperature_controller import LinkamControllerHC
        self.add_hardware(LinkamControllerHC(self))   
    
        ########################## MEASUREMENTS
        print("Adding Measurement Components")
        
        
        # hardware specific measurements
        
        from ScopeFoundryHW.picoharp.picoharp_hist_measure import PicoHarpHistogramMeasure
        self.add_measurement(PicoHarpHistogramMeasure(self))

        from ScopeFoundryHW.oceanoptics_spec.oo_spec_measure import  OOSpecLive
        self.add_measurement(OOSpecLive(self))
        
        self.add_measurement(ToupCamLiveMeasure(self))

        powermate_lq_choices = [
                    'hardware/asi_stage/x_target',
                    'hardware/asi_stage/y_target',
                   '',
                   ]
        from ScopeFoundryHW.powermate.powermate_measure import PowermateMeasure
        self.add_measurement(PowermateMeasure(self, n_devs=2, dev_lq_choices=powermate_lq_choices))


        # Combined Measurements
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement_component(PowerScanMeasure(self))        

        # Current Measurements
        from ScopeFoundryHW.keithley_sourcemeter.photocurrent_iv import PhotocurrentIVMeasurement
        self.add_measurement(PhotocurrentIVMeasurement(self))

        # Mapping Measurements        
        from confocal_measure.apd_mcl_2dslowscan import APD_MCL_2DSlowScan, APD_MCL_3DSlowScan
        apd_scan = self.add_measurement(APD_MCL_2DSlowScan(self))
        self.add_measurement(APD_MCL_3DSlowScan(self))
        
        from confocal_measure import Picoharp_MCL_2DSlowScan
        picoharp_scan = self.add_measurement(Picoharp_MCL_2DSlowScan(self))
        
        from confocal_measure.andor_hyperspec_scan import AndorHyperSpec2DScan
        andor_scan = self.add_measurement(AndorHyperSpec2DScan(self))

        # connect mapping measurement settings        
        lq_names =  ['h0', 'h1', 'v0', 'v1',  'Nh', 'Nv', 'h_axis', 'v_axis']
        
        for scan in [picoharp_scan, andor_scan]:
            for lq_name in lq_names:
                master_scan_lq =  apd_scan.settings.get_lq(lq_name)
                scan.settings.get_lq(lq_name).connect_to_lq(master_scan_lq)     
                
        
        from trpl_microscope.step_and_glue_spec_measure import SpecStepAndGlue
        self.add_measurement(SpecStepAndGlue(self))
        
        from confocal_measure.apd_asi_2dslowscan import APD_ASI_2DSlowScan
        apd_asi = self.add_measurement(APD_ASI_2DSlowScan(self))
        
        from confocal_measure.asi_hyperspec_scan import AndorHyperSpecASIScan
        hyperspec_asi = self.add_measurement(AndorHyperSpecASIScan(self))
        
        # connect mapping measurement settings        
        lq_names =  ['h0', 'h1', 'v0', 'v1',  'Nh', 'Nv']
        
        for scan in [apd_asi, hyperspec_asi]:
            for lq_name in lq_names:
                master_scan_lq =  apd_asi.settings.get_lq(lq_name)
                scan.settings.get_lq(lq_name).connect_to_lq(master_scan_lq)         
                    
        
        ####### Quickbar connections #################################
        
        Q = self.quickbar
        
        # 2D Scan Area
        apd_scan.settings.h0.connect_to_widget(Q.h0_doubleSpinBox)
        apd_scan.settings.h1.connect_to_widget(Q.h1_doubleSpinBox)
        apd_scan.settings.v0.connect_to_widget(Q.v0_doubleSpinBox)
        apd_scan.settings.v1.connect_to_widget(Q.v1_doubleSpinBox)
        apd_scan.settings.dh.connect_to_widget(Q.dh_doubleSpinBox)
        apd_scan.settings.dv.connect_to_widget(Q.dv_doubleSpinBox)
        apd_scan.settings.h_axis.connect_to_widget(Q.h_axis_comboBox)
        apd_scan.settings.v_axis.connect_to_widget(Q.v_axis_comboBox)
                
        
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
        #pw = self.hardware['power_wheel_arduino']
        pw = self.hardware['power_wheel']
        pw.settings.position.connect_to_widget(Q.power_wheel_encoder_pos_doubleSpinBox)
        pw.settings.jog_step.connect_to_widget(Q.powerwheel_move_steps_doubleSpinBox)
        Q.powerwheel_move_fwd_pushButton.clicked.connect(pw.jog_fwd)
        Q.powerwheel_move_bkwd_pushButton.clicked.connect(pw.jog_bkwd)

        #connect events
        apd = self.hardware['apd_counter']
        apd.settings.int_time.connect_to_widget(Q.apd_counter_int_doubleSpinBox)
        #apd.settings.count_rate.updated_text_value.connect(
        #                                   Q.apd_counter_output_lineEdit.setText)
        apd.settings.count_rate.connect_to_widget(Q.apd_counter_output_lineEdit)

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
        andor.settings.output_amp.connect_to_widget(Q.andor_ccd_output_amp_comboBox)
        
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
        
        
        # AOTF
        aotf_hw = self.hardware['CrystalTechAOTF_DDS']
        aotf_hw.settings.freq0.connect_to_widget(Q.atof_freq_doubleSpinBox)
        aotf_hw.settings.pwr0.connect_to_widget(Q.aotf_power_doubleSpinBox)
        aotf_hw.settings.modulation_enable.connect_to_widget(Q.aotf_mod_enable_checkBox)        
        
        ################# Shared Settings for Map Measurements ########################
        
        
        
        
        ##########
        self.settings_load_ini('trpl_defaults.ini')

if __name__ == '__main__':
    import sys
    app = TRPLMicroscopeApp(sys.argv)
    sys.exit(app.exec_())