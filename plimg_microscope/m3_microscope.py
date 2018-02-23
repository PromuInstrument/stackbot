from __future__ import print_function, absolute_import, division

from ScopeFoundry import BaseMicroscopeApp

import logging
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

logging.basicConfig(level='DEBUG')#, filename='m3_log.txt')
#logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)

logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)

class M3MicroscopeApp(BaseMicroscopeApp):

    name = "m3_microscope"

    def setup(self):
        
        #Add hardware components
        print("Adding Hardware Components")
        
        #from ScopeFoundryHW.apd_counter.apd_counter import APDCounterHW
        #self.add_hardware_component(APDCounterHW(self))
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        
        from ScopeFoundryHW.mcl_stage.mcl_xyz_stage import MclXYZStageHW
        self.add_hardware_component(MclXYZStageHW(self))
        
        #self.add_hardware_component(SEMSlowscanVoutStage(self)) 
        
        from ScopeFoundryHW.picoharp import PicoHarpHW
        self.add_hardware_component(PicoHarpHW(self))
        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteClientHW
        self.add_hardware_component(WinSpecRemoteClientHW(self))
        
        from ScopeFoundryHW.ascom_camera import ASCOMCameraHW
        self.add_hardware_component(ASCOMCameraHW(self))
        
        from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        self.add_hardware_component(PowerWheelArduinoHW(self))
        
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))

#         from ScopeFoundryHW.attocube_ecc100 import AttoCubeXYZStageHW
#         self.add_hardware_component(AttoCubeXYZStageHW(self))

#         from ScopeFoundryHW.newport_esp300 import ESP300AxisHW
#         self.add_hardware_component(ESP300AxisHW(self))
        
        from ScopeFoundryHW.thorlabs_stepper_motors import ThorlabsStepperControllerHW
        self.add_hardware_component(ThorlabsStepperControllerHW)
        
        from ScopeFoundryHW.ni_daq.hw.ni_digital_out import NIDigitalOutHW
        self.add_hardware(NIDigitalOutHW(self, name='flip_mirrors', line_names=['apd_flip', '_', '_', '_', '_', '_', '_', '_']))
        
        #Add measurement components
        print("Create Measurement objects")

        # hardware specific measurements
        #from ScopeFoundryHW.apd_counter import APDOptimizerMeasure
        #self.add_measurement_component(APDOptimizerMeasure(self))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement_component(APDOptimizerCBMeasurement(self))
        
        from ScopeFoundryHW.ascom_camera import ASCOMCameraCaptureMeasure
        self.add_measurement_component(ASCOMCameraCaptureMeasure(self))

        from ScopeFoundryHW.winspec_remote import WinSpecRemoteReadoutMeasure
        self.add_measurement_component(WinSpecRemoteReadoutMeasure(self))

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement_component(PowerMeterOptimizerMeasure(self))
        
        from ScopeFoundryHW.picoharp.picoharp_hist_measure import PicoHarpHistogramMeasure
        self.add_measurement(PicoHarpHistogramMeasure(self))
        
        # combined measurements
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement_component(PowerScanMeasure(self))
        
        # Mapping measurements
        from ScopeFoundryHW.mcl_stage.mcl_stage_slowscan import Delay_MCL_2DSlowScan
        self.add_measurement(Delay_MCL_2DSlowScan(self))
        
        from confocal_measure import APD_MCL_2DSlowScan
        self.add_measurement_component(APD_MCL_2DSlowScan(self))        
        
        from confocal_measure import Picoharp_MCL_2DSlowScan
        self.add_measurement_component(Picoharp_MCL_2DSlowScan(self))
        
        from confocal_measure import WinSpecMCL2DSlowScan
        self.add_measurement_component(WinSpecMCL2DSlowScan(self))
        
#         from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
#         self.add_measurement(AttoCubeStageControlMeasure(self))
#         
#         from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan
#         self.add_measurement(AttoCube2DSlowScan(self))

        from  plimg_microscope import fiber_scan 
        self.add_measurement(fiber_scan.FiberPowerMeterScan(self))
        self.add_measurement(fiber_scan.FiberAPDScan(self))
        self.add_measurement(fiber_scan.FiberPicoharpScan(self))
        self.add_measurement(fiber_scan.FiberWinSpecScan(self))
        
        from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))
        
        
        from plimg_microscope.auto_focus_measure import AutoFocusMeasure
        self.add_measurement(AutoFocusMeasure(self))
        
        from plimg_microscope.power_scan_maps import PowerScanMapMeasurement
        self.add_measurement(PowerScanMapMeasurement(self))
        
        #set some default logged quantities
        #
        
        #Add additional app-wide logged quantities
        # 
        

        ####### Quickbar connections #################################
        
        self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'm3_quick_access.ui')))
        Q = self.quickbar
        
        
        # 2D Scan Area
        Q.groupBox_scanarea.hide() # temporarily hide
#         apd_scan.settings.h0.connect_to_widget(Q.h0_doubleSpinBox)
#         apd_scan.settings.h1.connect_to_widget(Q.h1_doubleSpinBox)
#         apd_scan.settings.v0.connect_to_widget(Q.v0_doubleSpinBox)
#         apd_scan.settings.v1.connect_to_widget(Q.v1_doubleSpinBox)
#         apd_scan.settings.dh.connect_to_widget(Q.dh_doubleSpinBox)
#         apd_scan.settings.dv.connect_to_widget(Q.dv_doubleSpinBox)
#         apd_scan.settings.h_axis.connect_to_widget(Q.h_axis_comboBox)
#         apd_scan.settings.v_axis.connect_to_widget(Q.v_axis_comboBox)
                
        
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
        #apd.settings.count_rate.updated_text_value.connect(
        #                                   Q.apd_counter_output_lineEdit.setText)
        apd.settings.count_rate.connect_to_widget(Q.apd_counter_output_lineEdit)

        apd_opt = self.measurements['apd_optimizer']
        #apd.settings
        apd_opt.settings.activation.connect_to_widget(Q.apd_optimize_startstop_checkBox)
        #self.measurement_state_changed[bool].connect(self.gui.ui.apd_optimize_startstop_checkBox.setChecked)
        
        # Spectrometer
#         aspec = self.hardware['acton_spectrometer']
#         aspec.settings.center_wl.connect_to_widget(Q.acton_spec_center_wl_doubleSpinBox)
#         aspec.settings.exit_mirror.connect_to_widget(Q.acton_spec_exitmirror_comboBox)
#         aspec.settings.grating_name.connect_to_widget(Q.acton_spec_grating_lineEdit)        
#                
        
        # power meter
        pm = self.hardware['thorlabs_powermeter']
        pm.settings.wavelength.connect_to_widget(Q.power_meter_wl_doubleSpinBox)
        pm.settings.power.connect_to_widget(Q.power_meter_power_label)
        
        pm_opt = self.measurements['powermeter_optimizer']
        pm_opt.settings.activation.connect_to_widget(Q.power_meter_acquire_cont_checkBox)
        
        
        
#         shutter = self.hardware['shutter_servo']
#         shutter.settings.shutter_open.connect_to_widget(Q.shutter_open_checkBox)
#         
#         self.hardware['flip_mirror'].settings.mirror_position.connect_to_widget(Q.flip_mirror_checkBox)
        
        # load default settings from file
        self.settings_load_ini("m3_settings.ini")


if __name__ == '__main__':
    import sys
    app = M3MicroscopeApp(sys.argv)
    sys.exit(app.exec_())