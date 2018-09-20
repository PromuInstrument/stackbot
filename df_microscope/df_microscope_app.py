from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp

class DFMicroscopeApp(BaseMicroscopeApp):

    name = 'df_microscope'
    
    def setup(self):
        
        print("Adding Hardware Components")
        
        from ScopeFoundryHW.apd_counter import APDCounterHW
        self.add_hardware_component(APDCounterHW(self))

        from ScopeFoundryHW.mcl_stage.mcl_xyz_stage import MclXYZStageHW
        self.add_hardware_component(MclXYZStageHW(self))
        
        from ScopeFoundryHW.picoharp import PicoHarpHW
        self.add_hardware_component(PicoHarpHW(self))
        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteClientHW
        self.add_hardware_component(WinSpecRemoteClientHW(self))

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))

        from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        self.power_wheel = self.add_hardware_component(PowerWheelArduinoHW(self))
        
        from ScopeFoundryHW.newport_esp300 import ESP300AxisHW
        self.add_hardware(ESP300AxisHW(self))

        from ScopeFoundryHW.thorlabs_integrated_stepper.thorlabs_integrated_stepper_motor_hw import ThorlabsIntegratedStepperMottorHW
        self.add_hardware(ThorlabsIntegratedStepperMottorHW(self))
        
        from ScopeFoundryHW.shutter_servo_arduino.shutter_servo_arduino_hc import ShutterServoHW
        self.add_hardware(ShutterServoHW(self))

        print("Adding Measurement Components")
        
        # hardware specific measurements
        from ScopeFoundryHW.apd_counter import APDOptimizerMeasure
        self.add_measurement_component(APDOptimizerMeasure(self))
        
        from ScopeFoundryHW.winspec_remote import WinSpecRemoteReadoutMeasure
        self.add_measurement_component(WinSpecRemoteReadoutMeasure(self))

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement_component(PowerMeterOptimizerMeasure(self))
        
        # combined measurements
        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement_component(PowerScanMeasure(self))
        

        # Mapping measurements
        from confocal_measure import APD_MCL_2DSlowScan
        self.add_measurement_component(APD_MCL_2DSlowScan(self))        
        
        from confocal_measure import Picoharp_MCL_2DSlowScan
        self.add_measurement_component(Picoharp_MCL_2DSlowScan(self))
        
        from confocal_measure import WinSpecMCL2DSlowScan
        self.add_measurement_component(WinSpecMCL2DSlowScan(self))
                
        from confocal_measure.polarized_hyperspec_scan_measure import PolarizedHyperspecScanMeasure
        self.add_measurement(PolarizedHyperspecScanMeasure(self))
        
        # load default settings 
        self.settings_load_ini('df_microscope_defaults.ini')

        
if __name__ == '__main__':
    import sys
    app = DFMicroscopeApp(sys.argv)
    sys.exit(app.exec_())