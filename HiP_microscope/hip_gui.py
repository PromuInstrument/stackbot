import sys
from PySide import QtGui

from ScopeFoundry import BaseMicroscopeApp

# Import Hardware Components
from hardware_components.apd_counter import APDCounterHardwareComponent
#from hardware_components.dummy_xy_stage import DummyXYStage
from hardware_components.picam import PicamHW
from hardware_components.mcl_xyz_stage import MclXYZStage

# Import Measurement Components
from measurement_components.apd_optimizer_simple import APDOptimizerMeasurement
from measurement_components.picam_readout import PicamReadoutMeasure
from hardware_components.acton_spec import ActonSpectrometerHW
from hardware_components.omega_pt_pid_controller import OmegaPtPIDControllerHardware
from measurement_components.hip_dual_temperature import HiPMicroscopeDualTemperature
from HiP_microscope.hyperspec_picam_mcl import HyperSpecPicam2DScan, HyperSpecPicam3DStack

class HiPMicroscopeApp(BaseMicroscopeApp):

    name = "HiP_Microscope"

    #ui_filename = "base_gui.ui"

    def setup(self):
        
        #Add hardware components
        print "Adding Hardware Components"
        #self.add_hardware_component(APDCounterHardwareComponent(self))
        #self.add_hardware_component(DummyXYStage(self))
        self.add_hardware_component(MclXYZStage(self))
        self.add_hardware_component(PicamHW(self))
        self.add_hardware_component(ActonSpectrometerHW(self))
        self.add_hardware_component(OmegaPtPIDControllerHardware(self))
        #Add measurement components
        print "Create Measurement objects"
        #self.add_measurement_component(APDOptimizerMeasurement(self))
        #self.add_measurement_component(SimpleXYScan(self))
        self.add_measurement_component(PicamReadoutMeasure(self))
        self.add_measurement_component(HyperSpecPicam2DScan(self))
        self.add_measurement_component(HiPMicroscopeDualTemperature(self))
        self.add_measurement_component(HyperSpecPicam3DStack(self))
                
        #set some default logged quantities
        #self.hardware_components['apd_counter'].debug_mode.update_value(True)
        #self.hardware_components['apd_counter'].dummy_mode.update_value(True)
        #self.hardware_components['apd_counter'].connected.update_value(True)


        #Add additional logged quantities

        # Connect to custom gui
        
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':

    app = HiPMicroscopeApp(sys.argv)
    
    sys.exit(app.exec_())