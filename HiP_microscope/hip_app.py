import sys
from ScopeFoundry import BaseMicroscopeApp
import time
# Import Hardware Components
#from hardware_components.dummy_xy_stage import DummyXYStage

# Import Measurement Components

#from HiP_microscope.measure.hip_dual_temperature import HiPMicroscopeDualTemperature

class HiPMicroscopeApp(BaseMicroscopeApp):

    name = "HiP_Microscope"

    #ui_filename = "base_gui.ui"

    def setup(self):
        
        #Add hardware components
        from ScopeFoundryHW.mcl_stage import MclXYZStageHW
        self.add_hardware_component(MclXYZStageHW(self))

        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware_component(ActonSpectrometerHW(self))
        
        from ScopeFoundryHW.picam import PicamHW, PicamReadoutMeasure
        self.add_hardware_component(PicamHW(self))
        self.add_measurement_component(PicamReadoutMeasure(self))
        
        from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
        self.add_hardware(ASIStageHW(self))
        from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
        self.add_measurement(ASIStageControlMeasure(self))


        #from hardware_components.omega_pt_pid_controller import OmegaPtPIDControllerHardware        
        #self.add_hardware_component(OmegaPtPIDControllerHardware(self))
        
        #Add measurement components
        print("Create Measurement objects")
        from HiP_microscope.measure.hyperspec_picam_mcl import HyperSpecPicam2DScan, HyperSpecPicam3DStack
        self.add_measurement_component(HyperSpecPicam2DScan(self))
        #self.add_measurement_component(HiPMicroscopeDualTemperature(self))
        self.add_measurement_component(HyperSpecPicam3DStack(self))
        
        
        from HiP_microscope.measure.picam_calibration_sweep import PicamCalibrationSweep
        self.add_measurement(PicamCalibrationSweep(self))        
                
        
        #set some default logged quantities
        #self.hardware_components['apd_counter'].debug_mode.update_value(True)
        #self.hardware_components['apd_counter'].dummy_mode.update_value(True)
        #self.hardware_components['apd_counter'].connected.update_value(True)

        # load default settings from file
        self.settings_load_ini("hip_settings.ini")

        self.hardware['mcl_xyz_stage'].settings['connected']=True
        self.hardware['picam'].settings['connected']=True
        time.sleep(0.5)
        self.hardware['picam'].settings['roi_y_bin'] = 100
        self.hardware['picam'].commit_parameters()
        self.hardware['acton_spectrometer'].settings['connected']=True
        
        self.set_subwindow_mode()


if __name__ == '__main__':

    app = HiPMicroscopeApp(sys.argv)
    app.tile_layout()
    sys.exit(app.exec_())