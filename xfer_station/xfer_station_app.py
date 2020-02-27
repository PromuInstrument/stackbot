from ScopeFoundry import BaseMicroscopeApp

from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
from xfer_station.powermate_listener import PowermateListener
from ScopeFoundryHW.thorlabs_elliptec.elliptec_hw import ThorlabsElliptecSingleHW


class XferStationApp(BaseMicroscopeApp):
    
    name ='xfer_station'
    
    def setup(self):
        
        self.add_hardware(ASIStageHW(self, name='stage_top',  swap_xy=True))
        self.add_hardware(ASIStageHW(self, name='stage_bottom',  swap_xy=True))
        
        self.add_measurement(ASIStageControlMeasure(self, name='top_stage_ctrl',  hw_name='stage_top',))
        self.add_measurement(ASIStageControlMeasure(self, name='bottom_stage_ctrl', hw_name='stage_bottom'))
        
        self.add_measurement(PowermateListener(self))
        
        
        self.add_hardware(ThorlabsElliptecSingleHW(self))
        
        self.settings_load_ini("xfer_station_defaults.ini")

if __name__ == '__main__':
    import sys
    app = XferStationApp(sys.argv)
    app.exec_()