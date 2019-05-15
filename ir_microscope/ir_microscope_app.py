from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging
from ScopeFoundryHW import attocube_ecc100
import ScopeFoundryHW
from ir_microscope.measurements import apd_scan, hyperspectral_scan, trpl_scan
from ir_microscope import measurements
import numpy as np
from ScopeFoundry import LQRange


logging.basicConfig(level='DEBUG')#, filename='m3_log.txt')
#logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


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


        #from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        #self.power_wheel = self.add_hardware_component(PowerWheelArduinoHW(self))
        from ScopeFoundryHW.pololu_servo.single_servo_hw import PololuMaestroServoHW
        self.add_hardware(PololuMaestroServoHW(self, name='power_wheel'))
        
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))
        
        from ScopeFoundryHW.thorlabs_powermeter.thorlabs_powermeter_analog_readout import ThorlabsPowerMeterAnalogReadOut
        self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))

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
        
        from ScopeFoundryHW.filter_wheel_arduino.filter_wheel_arduino_hw import FilterWheelArduinoHW
        self.add_hardware(FilterWheelArduinoHW(self))
        
        from ScopeFoundryHW.arduino_tc4.arduino_tc4_hw import ArduinoTc4HW
        self.add_hardware(ArduinoTc4HW(self))
        
                        
        print("Adding Measurement Components")

        self.add_measurement(ph.PicoHarpChannelOptimizer(self))
        self.add_measurement(ph.PicoHarpHistogramMeasure(self))
        self.add_measurement(trpl_scan.TRPL2DScan(self))
        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteReadoutMeasure
        self.add_measurement(WinSpecRemoteReadoutMeasure(self))
        self.add_measurement(hyperspectral_scan.Hyperspectral2DScan(self))
        
        #self.add_measurement(apd_scan.M4APDScanPhMeasure(self))
        
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement(PowerScanMeasure(self))       
        
        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))    
 
        from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
        self.add_measurement(AttoCubeStageControlMeasure(self))

        from ScopeFoundryHW.powermate.powermate_measure import PowermateMeasure
        choices = ['hardware/attocube_xyz_stage/z_target_position',
                   'hardware/attocube_xyz_stage/x_target_position',
                   'hardware/attocube_xyz_stage/y_target_position',
                   '',
                   ]
        self.add_measurement(PowermateMeasure(self, n_devs=3, dev_lq_choices=choices))
        
        from ScopeFoundryHW.attocube_ecc100.attocube_home_axis_measurement import AttoCubeHomeAxisMeasurement
        self.add_measurement(AttoCubeHomeAxisMeasurement(self))
        
        #from measurements.stage_motion_measure import StageHomeAxesMeasure
        #self.add_measurement(StageHomeAxesMeasure(self))
        
        
        #from measurements.xbox_controller_measure import XboxControllerMeasure
        #self.add_measurement(XboxControllerMeasure(self))
        
        #from measurements.laser_line_writer import LaserLineWriter
        #self.add_measurement(LaserLineWriter(self))
        
        
        from ir_microscope.measurements.laser_power_feedback_control import LaserPowerFeedbackControl
        self.add_measurement(LaserPowerFeedbackControl(self))
        
        
        from ir_microscope.measurements.position_recipe_control import PositionRecipeControl
        self.add_measurement(PositionRecipeControl(self))
        #from ir_microscope.measurements.focus_recipe_control import FocusRecipeControl
        #self.add_measurement(FocusRecipeControl(self))
        
        
        from ir_microscope.measurements.nested_trpl_scans import NestedTrplScans
        self.add_measurement(NestedTrplScans(self))
        
        
        from ir_microscope.measurements.apd_scan import PicoharpApdScan
        self.add_measurement(PicoharpApdScan(self, use_external_range_sync=True))
        
        
        from ir_microscope.measurements.calibration_sweep import CalibrationSweep
        self.add_measurement(CalibrationSweep(self, spectrometer_hw_name='acton_spectrometer', 
                                                    camera_readout_measure_name='winspec_readout') )
        
        #from ir_microscope.measurements.trpl_parallelogram_scan import TRPLParallelogramScan
        #self.add_measurement(TRPLParallelogramScan(self, use_external_range_sync=False))
        
        
        #from ScopeFoundryHW.xbox_controller.xbox_controller_test_measure import 
        
        ####### Quickbar connections #################################
        
        Q = self.quickbar
        
        
        #power mate
        self.measurements['powermate_measure'].settings.fine.connect_to_widget(Q.fine_checkBox)

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

        self.measurements['attocube_stage_control_measure'].settings.activation.connect_to_widget(Q.stage_live_update_checkBox)
        self.measurements['attocube_stage_control_measure'].settings.wobble.connect_to_widget(Q.stage_wobble_checkBox)
        
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
        
        # laser power feedback
        lpfc = self.measurements['laser_power_feedback_control']
        lpfc.settings.setpoint_power.connect_to_widget(Q.laser_power_feedback_control_setpoint_doubleSpinBox)
        lpfc.settings.p_gain.connect_to_widget(Q.laser_power_feedback_control_p_gain_doubleSpinBox)
        lpfc.settings.activation.connect_to_widget(Q.laser_power_feedback_control_activation_checkBox)
        
        # Power Wheel
        #pw = self.hardware['power_wheel_arduino']
        pw = self.hardware['power_wheel']
        pw.settings.position.connect_to_widget(Q.power_wheel_encoder_pos_doubleSpinBox)
        pw.settings.jog_step.connect_to_widget(Q.powerwheel_move_steps_doubleSpinBox)
        Q.powerwheel_move_fwd_pushButton.clicked.connect(pw.jog_fwd)
        Q.powerwheel_move_bkwd_pushButton.clicked.connect(pw.jog_bkwd)

        # Filter Wheel
        fw = self.hardware['filter_wheel']
        fw.settings.current_filter.connect_to_widget(Q.current_filter_doubleSpinBox)
        Q.target_filter_lineEdit.returnPressed.connect(fw.settings.target_filter.update_value)
        Q.target_filter_lineEdit.returnPressed.connect(lambda: Q.target_filter_lineEdit.setText(""))

        #Q.move_filter_fwd_pushButton.clicked.connect(fw.increase_target_filter)
        #Q.move_filter_bkwd_pushButton.clicked.connect(fw.decrease_target_filter)
        Q.zero_filter_pushButton.clicked.connect(fw.zero_filter)
        
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
        # app level settings
        S = self.settings
        
        
        # 2d scan
        _2D_scans = ['trpl_2d_scan', 'hyperspectral_2d_scan', 'apd_scan']
        
        #Create and connect logged quantities to widget and equivalent lqs measurements
        for ii,lq_name in enumerate(["h_axis","v_axis"]):
            S.New(lq_name, dtype=str, initial='xy'[ii], choices=("x", "y", "z"), ro=False)
            getattr(S, lq_name).connect_to_widget(\
                                    getattr(Q, lq_name+'_comboBox'))
            for m in _2D_scans:
                getattr(S, lq_name).connect_to_lq( \
                                    getattr(self.measurements[m].settings,lq_name) )

        for lq_name in ['h0','h1','v0','v1','dh','dv']:
            S.New(lq_name, dtype=float, unit='mm', ro=False, spinbox_decimals=6, spinbox_step=0.001,)
            getattr(S, lq_name).connect_to_widget(\
                                    getattr(Q, lq_name+'_doubleSpinBox'))
            for m in _2D_scans:
                getattr(S, lq_name).connect_to_lq( \
                                        getattr(self.measurements[m].settings,lq_name))
                    
        
        for lq_name in ['Nh', 'Nv']:
            S.New(lq_name, dtype=int, ro=False, vmin=2, initial=11)
            getattr(S, lq_name).connect_to_widget(\
                                    getattr(Q, lq_name+'_doubleSpinBox'))
            for m in _2D_scans:
                getattr(S, lq_name).connect_to_lq( \
                                        getattr(self.measurements[m].settings,lq_name))

        for lq_name in ['h_center', 'v_center', 'h_span', 'v_span']:
            S.New(lq_name, dtype=float, unit='mm', initial=0.005, ro=False, spinbox_decimals=6, spinbox_step=0.001,)
            getattr(S, lq_name).connect_to_widget(\
                                                    getattr(Q, lq_name+'_doubleSpinBox'))
            for m in _2D_scans:
                getattr(S, lq_name).connect_to_lq( \
                                        getattr(self.measurements[m].settings,lq_name))

        
                
        #make connected ranges
        self.h_range=LQRange(S.get_lq('h0'),S.get_lq('h1'),S.get_lq('dh'),S.get_lq('Nh'),
                             S.get_lq('h_center'), S.get_lq('h_span'))
        self.v_range=LQRange(S.get_lq('v0'),S.get_lq('v1'),S.get_lq('dv'),S.get_lq('Nv'),
                             S.get_lq('v_center'), S.get_lq('v_span'))

        self.coppy_current_position_to_2d_scan_center()
                
        Q.copy_current_position_to_2d_scan_center_pushButton.clicked.connect(
            lambda:self.coppy_current_position_to_2d_scan_center(decimal_places=3.0))
    

        ##########
        self.settings_load_ini('ir_microscope_defaults.ini')                        
        
    def coppy_current_position_to_2d_scan_center(self, decimal_places=3.0):
        S_stage = self.hardware['attocube_xyz_stage'].settings
        current_postions = {'x':S_stage['x_position'],
                            'y':S_stage['y_position'],
                            'z':S_stage['z_position']}
        if decimal_places >= 0:
            for ax in 'xyz':
                val = np.ceil(current_postions[ax]*10**decimal_places)/(10.0**decimal_places)
                current_postions[ax] = val
        
        S = self.settings
        S['h_center'] = current_postions[S['h_axis']]
        S['v_center'] = current_postions[S['v_axis']]

        
        

if __name__ == '__main__':
    import sys
    app = IRMicroscopeApp(sys.argv)
    sys.exit(app.exec_())