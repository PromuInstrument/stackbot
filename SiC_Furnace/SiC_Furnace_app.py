from ScopeFoundry.base_app import BaseMicroscopeApp


class SiC_FurnaceApp(BaseMicroscopeApp):
    
    name = 'SiC_Furnace'
    
    def setup(self):
        
        from SiC_Furnace.optris_pyrometer_hw import OptrisPyrometerHW
        self.add_hardware(OptrisPyrometerHW(self))
        
        from ScopeFoundryHW.alicat_eip.alicat_eip_mfc_hw import Alicat_EIP_MFC_HW
        from ScopeFoundryHW.alicat_eip.alicat_eip_pc_hw import Alicat_EIP_PC_HW
        
        units = dict(pressure_unit='torrA', vol_flow_unit='LPM', mass_flow_unit='SLPM')
        self.add_hardware(Alicat_EIP_MFC_HW(self, name="MFC_N2", **units))
        self.add_hardware(Alicat_EIP_MFC_HW(self, name="MFC_Ar", **units))
        self.add_hardware(Alicat_EIP_MFC_HW(self, name="MFC_H2", **units))

        self.add_hardware(Alicat_EIP_PC_HW(self, pressure_unit='torrA'))
        
        from ScopeFoundryHW.omega_pid.omega_pid_hw import OmegaPIDHW
        pid1 = self.add_hardware(OmegaPIDHW(self, name='pid_pyro'))
        pid2 = self.add_hardware(OmegaPIDHW(self, name='pid_outside'))
        
        from SiC_Furnace.hw_status_measure import HWStatusMeasure
        self.add_measurement(HWStatusMeasure(self))
        
        
        
        
        self.settings_load_ini('lq_defaults.ini')
        
        for hw in self.hardware.values():
            try:
                hw.settings['connected'] = True
            except Exception as err:
                print("{} failled to connect: {}".format(hw.name, err))

        
if __name__ == '__main__':
    import sys
    app = SiC_FurnaceApp(sys.argv)
    sys.exit(app.exec_())    