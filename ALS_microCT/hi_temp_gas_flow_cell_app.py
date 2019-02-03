from ScopeFoundry import BaseMicroscopeApp
from ALS_microCT.analog_pressure_gauge_hw import AnalogPressureGaugeHW
from ScopeFoundryHW.lambda_zup.lamba_zup_hw import LambdaZupHW
from ScopeFoundryHW.sierra_mfc.sierra_mfc_hw import SierraMFC_HW
#from ALS_microCT.tc_reader_hw import TcReaderHW
from ALS_microCT.tc_reader_steam_hw import TcReaderStreamHW
from ALS_microCT.data_log_measure import ChamberDataLogMeasure
from ALS_microCT.control_panel_measure import ControlPanelMeasure
from ALS_microCT.process_measure import ChamberProcessMeasure
from ALS_microCT.process_xls_measure import ChamberProcessXLSMeasure


class HiTempGasFlowCellApp(BaseMicroscopeApp):
    
    name= 'hi_temp_gas_flow_cell'
    
    def setup(self):
        pass
    
        ### Sierra MFC at COM3
        
        ### Pressure gauge -- connected to Ain of NI USB-6001
        
        self.add_hardware(AnalogPressureGaugeHW(self))
    
        ### Power supply lambda Zup 
    
        ps1 = self.add_hardware(LambdaZupHW(self, name='lambda_zup1'))
        ps2 = self.add_hardware(LambdaZupHW(self, name='lambda_zup2'))
        
        ps1.settings['port'] = 'COM5'
        ps2.settings['port'] = 'COM6'

        for ps in (ps1, ps2):
            ps.settings['always_send_address'] = False
            ps.settings['live_update'] = True

        
        #### MFC
        
        mfc = self.add_hardware(SierraMFC_HW(self))
        mfc.settings['port'] = 'COM4'
        
        #### Temperature monitor
        # self.add_hardware(TcReaderHW(self))
        self.add_hardware(TcReaderStreamHW(self))
        
        
        ###
        
        self.add_measurement(ChamberDataLogMeasure(self))
        self.add_measurement(ControlPanelMeasure(self))
        self.add_measurement(ChamberProcessMeasure(self))
        self.add_measurement(ChamberProcessXLSMeasure(self))
        
        for hw in self.hardware.values():
            try:
                hw.settings['connected'] = True
            except Exception as err:
                print(err)
if __name__ == '__main__':
    
    app = HiTempGasFlowCellApp()
    
    app.exec_()