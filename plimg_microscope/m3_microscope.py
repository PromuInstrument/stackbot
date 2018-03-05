from __future__ import print_function, absolute_import, division

from ScopeFoundry import BaseMicroscopeApp

import logging

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

        from ScopeFoundryHW.attocube_ecc100 import AttoCubeXYZStageHW
        self.add_hardware_component(AttoCubeXYZStageHW(self))

        from ScopeFoundryHW.newport_esp300 import ESP300AxisHW
        self.add_hardware_component(ESP300AxisHW(self))
        
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

#         from  plimg_microscope import fiber_scan 
#         self.add_measurement(fiber_scan.FiberPowerMeterScan(self))
#         self.add_measurement(fiber_scan.FiberAPDScan(self))
#         self.add_measurement(fiber_scan.FiberPicoharpScan(self))
#         self.add_measurement(fiber_scan.FiberWinSpecScan(self))
        
        from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))
        
        #set some default logged quantities
        #
        
        #Add additional app-wide logged quantities
        # 
        
        # Connect to custom gui
        
        # show gui
        self.ui.show()
        self.ui.activateWindow()
        
        # load default settings from file
        self.settings_load_ini("m3_settings.ini")


if __name__ == '__main__':
    import sys
    app = M3MicroscopeApp(sys.argv)
    sys.exit(app.exec_())