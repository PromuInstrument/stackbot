from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class DFMicroscopeApp(BaseMicroscopeApp):

    name = 'df_microscope'
    
    def setup(self):
        
        print("Adding Hardware Components")
        
        #from ScopeFoundryHW.apd_counter import APDCounterHW
        #self.add_hardware_component(APDCounterHW(self))
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))


        from ScopeFoundryHW.mcl_stage.mcl_xyz_stage import MclXYZStageHW
        self.add_hardware_component(MclXYZStageHW(self))
        
        from ScopeFoundryHW.picoharp import PicoHarpHW
        self.add_hardware_component(PicoHarpHW(self))
        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteClientHW
        self.add_hardware_component(WinSpecRemoteClientHW(self))

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))

        #from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        #self.power_wheel = self.add_hardware_component(PowerWheelArduinoHW(self))
        
        #from ScopeFoundryHW.pololu_servo.single_servo_hw import PololuMaestroServoHW # imports the power wheel
        #self.add_hardware_component(PololuMaestroServoHW(self))# adds the power wheel
        
        from ScopeFoundryHW.newport_esp300 import ESP300AxisHW
        self.add_hardware(ESP300AxisHW(self))
        
        from ScopeFoundryHW.shutter_servo_arduino.shutter_servo_arduino_hc import ShutterServoHW
        self.add_hardware(ShutterServoHW(self))

        from ScopeFoundryHW.thorlabs_integrated_stepper.thorlabs_integrated_stepper_motor_hw import ThorlabsIntegratedStepperMottorHW
        self.add_hardware(ThorlabsIntegratedStepperMottorHW(self))
        
#         from ScopeFoundryHW.pololu_servo.single_servo_hw import PololuMaestroServoHW
#         self.add_hardware(PololuMaestroServoHW(self, name='power_wheel'))


        #from ScopeFoundryHW.pololu_servo.multi_servo_hw import PololuMaestroHW
        #self.add_hardware(PololuMaestroHW(self, servo_names=[(1, "power_wheel"), 
        #                                                     (2, "polarizer")]))

        
        from ScopeFoundryHW.pololu_servo.multi_servo_hw import PololuMaestroHW, PololuMaestroWheelServoHW
        self.add_hardware(PololuMaestroHW(self, name='pololu_maestro'))
        self.add_hardware(PololuMaestroWheelServoHW(self, name='power_wheel', channel=1))
        self.add_hardware(PololuMaestroWheelServoHW(self, name='excitation_polarizer', channel=2))
        #self.add_hardware(PololuMaestroShutterServoHW(self, name='shutter', channel=2))


        print("Adding Measurement Components")
        
        # hardware specific measurements
        #from ScopeFoundryHW.apd_counter import APDOptimizerMeasure
        #self.add_measurement_component(APDOptimizerMeasure(self))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement_component(APDOptimizerCBMeasurement(self))

        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteReadoutMeasure
        self.add_measurement_component(WinSpecRemoteReadoutMeasure(self))

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement_component(PowerMeterOptimizerMeasure(self))
        
        # combined measurements
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement_component(PowerScanMeasure(self, 'hardware/shutter_servo/shutter_open'))
        

        # Mapping measurements
        from confocal_measure import APD_MCL_2DSlowScan
        self.add_measurement_component(APD_MCL_2DSlowScan(self))        
        
        from confocal_measure import Picoharp_MCL_2DSlowScan
        self.add_measurement_component(Picoharp_MCL_2DSlowScan(self))
        
        from confocal_measure import WinSpecMCL2DSlowScan
        self.add_measurement_component(WinSpecMCL2DSlowScan(self))
                
        from confocal_measure.polarized_hyperspec_scan_measure import PolarizedHyperspecScanMeasure
        self.add_measurement(PolarizedHyperspecScanMeasure(self))
        
        
        self.setup_quickbar()
        
        # load default settings 
        self.settings_load_ini('df_microscope_defaults.ini')
        
        
    def setup_quickbar(self):
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'df_sidepanel.ui')))
        
        ####### Quickbar connections #################################
        
        Q = self.quickbar
        
        # MadCity Labs
        mcl = self.hardware['mcl_xyz_stage']

        mcl.settings.x_position.connect_to_widget(Q.cx_doubleSpinBox)
        mcl.settings.x_target.connect_to_widget(Q.target_x_doubleSpinBox)

        mcl.settings.y_position.connect_to_widget(Q.cy_doubleSpinBox)
        mcl.settings.y_target.connect_to_widget(Q.target_y_doubleSpinBox)

        #mcl.settings.move_speed.connect_to_widget(Q.nanodrive_move_slow_doubleSpinBox)        

        p = self.hardware['power_wheel']
        p.settings.position.connect_to_widget(Q.powerwheel_encoder_pos_doubleSpinBox)
        p.settings.jog_step.connect_to_widget(Q.powerwheel_move_steps_doubleSpinBox)
        Q.powerwheel_move_fwd_pushButton.clicked.connect(p.jog_fwd)
        Q.powerwheel_move_bkwd_pushButton.clicked.connect(p.jog_bkwd)

        #
        pol = self.hardware['excitation_polarizer']
        pol.settings.position.connect_to_widget(Q.polarizer_pos_doubleSpinBox)

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
        
        
        # power meter
        pm = self.hardware['thorlabs_powermeter']
        pm.settings.wavelength.connect_to_widget(Q.power_meter_wl_doubleSpinBox)
        pm.settings.power.connect_to_widget(Q.power_meter_power_label)
        
        pm_opt = self.measurements['powermeter_optimizer']
        pm_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)
        
        
        shutter = self.hardware['shutter_servo']
        shutter.settings.shutter_open.connect_to_widget(Q.shutter_open_checkBox)
        
        
        self.open_shutter_before_scan = self.settings.New('open_shutter_before_scan', initial = True, dtype=bool)
        self.close_shutter_after_scan = self.settings.New('close_shutter_after_scan', initial = True, dtype=bool)
            
        self.open_shutter_before_scan.connect_to_widget(Q.open_shutter_on_run_checkBox)
        self.close_shutter_after_scan.connect_to_widget(Q.close_shutter_after_scan_checkBox)
        

        
if __name__ == '__main__':
    import sys
    app = DFMicroscopeApp(sys.argv)
    sys.exit(app.exec_())