from __future__ import division, print_function
from ScopeFoundry import HardwareComponent
from Auger.hardware.auger_electron_analyzer_dev import AugerElectronAnalyzer

class AugerElectronAnalyzerHW(HardwareComponent):
    
    name = 'auger_electron_analyzer'

    def setup(self):
        self.settings.New("CAE_mode", dtype=bool, initial = True    )
        self.settings.New("multiplier", dtype=bool, initial = False)
        self.settings.New("KE", dtype=float, unit='eV', vmin=0, vmax=2200, initial = 200)
        self.settings.New("work_function", dtype=float, unit='eV', vmin=0, vmax=10, initial=4.5)
        self.settings.New("pass_energy", dtype=float, unit='V', vmin=5, vmax=500, initial = 100)
        self.settings.New("crr_ratio", dtype=float, vmin=1.5, vmax=20, initial = 5.0)
        self.settings.New("resolution", dtype=float, ro=True, unit='eV')
        quad_lq_settings = dict( dtype=float, vmin=-100, vmax=+100, initial=0, unit='%', si=False)
        self.settings.New("quad_X1", **quad_lq_settings)
        self.settings.New("quad_Y1", **quad_lq_settings)
        self.settings.New("quad_X2", **quad_lq_settings)
        self.settings.New("quad_Y2", **quad_lq_settings)
                          
    def connect(self):
        E = self.analyzer = AugerElectronAnalyzer(debug=self.debug_mode.val)
                
        self.settings.CAE_mode.hardware_read_func = E.get_retarding_mode
        self.settings.CAE_mode.hardware_set_func = E.write_retarding_mode
        
        self.settings.multiplier.hardware_read_func = E.get_multiplier
        self.settings.multiplier.hardware_set_func = E.write_multiplier
        
        self.settings.KE.hardware_read_func = E.get_KE
        self.settings.KE.hardware_set_func  = E.write_KE

        self.settings.work_function.hardware_read_func = E.get_work_function
        self.settings.work_function.hardware_set_func = E.set_work_function
        
        self.settings.pass_energy.hardware_read_func = E.get_pass_energy
        self.settings.pass_energy.hardware_set_func = E.write_pass_energy
        
        self.settings.crr_ratio.hardware_read_func = E.get_crr_ratio
        self.settings.crr_ratio.hardware_set_func = E.write_crr_ratio

        self.settings.resolution.hardware_read_func = E.get_resolution
        
        self.settings.quad_X1.hardware_set_func = lambda val, E=E: E.write_quad('X1', val) 
        self.settings.quad_Y1.hardware_set_func = lambda val, E=E: E.write_quad('Y1', val) 
        self.settings.quad_X2.hardware_set_func = lambda val, E=E: E.write_quad('X2', val) 
        self.settings.quad_Y2.hardware_set_func = lambda val, E=E: E.write_quad('Y2', val)        
        
        for lqname in ['KE', 'pass_energy', 'crr_ratio']:
            getattr(self.settings, lqname).add_listener(self.settings.resolution.read_from_hardware)
            
        # write state to hardware
        for lq in self.settings.as_list(): 
            lq.write_to_hardware()
    
    def disconnect(self):

        
        # disconnect lq's
        # TODO

        if hasattr(self, 'analyzer'):
            self.analyzer.close()        
            del self.analyzer
        




from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class AugerElectronAnalyzerTestApp(BaseMicroscopeApp):
    
    name = 'AugerElectronAnalyzerTestApp'
    
    def setup(self):
        
        AEA = self.add_hardware_component(AugerElectronAnalyzerHW(self))

        self.ui.show()
        
        self.ui_analyzer = load_qt_ui_file(sibling_path(__file__, "auger_electron_analyzer_viewer.ui"))
                
        widget_connections = [
         ('CAE_mode', 'cae_checkBox'),
         ('multiplier', 'multiplier_checkBox'),
         ('KE', 'KE_doubleSpinBox'),
         ('work_function', 'work_func_doubleSpinBox'),
         ('pass_energy', 'pass_energy_doubleSpinBox'),
         ('crr_ratio', 'crr_ratio_doubleSpinBox'),
         ('resolution', 'resolution_doubleSpinBox'),
         ('quad_X1', 'qX1_doubleSpinBox'),
         ('quad_Y1', 'qY1_doubleSpinBox'),
         ('quad_X2', 'qX2_doubleSpinBox'),
         ('quad_Y2', 'qY2_doubleSpinBox'),
         ]
        for lq_name, widget_name in widget_connections:
            AEA.settings.get_lq(lq_name).connect_bidir_to_widget(getattr(self.ui_analyzer, widget_name))
        
        #self.ui_analyzer.show()
        self.ui.centralwidget.layout().addWidget(self.ui_analyzer)
        self.ui.setWindowTitle(self.name)
        AEA.settings['debug_mode'] = True
        AEA.settings.connected.update_value(True)
        
if __name__ == '__main__':
    app = AugerElectronAnalyzerTestApp([])
    app.exec_()
    