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
        self.add_hardware_component(ESP300AxisHW(self))


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
                
        # load default settings 
        self.hardware['thorlabs_powermeter'].settings['port'] = 'USB0::0x1313::0x8078::P0013111::INSTR'
        self.hardware['power_wheel_arduino'].settings['ser_port'] = 'COM5'
        self.hardware['esp300'].settings['port'] = 'COM6'

        
if __name__ == '__main__':
    import sys
    app = DFMicroscopeApp(sys.argv)
    sys.exit(app.exec_())