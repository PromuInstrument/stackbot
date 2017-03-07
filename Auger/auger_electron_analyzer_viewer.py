from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class AugerElectronAnalyzerViewer(Measurement):
    
    name = 'auger_e_analyzer_view'
    
    def setup(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "auger_electron_analyzer_viewer.ui"))

        self.e_analyzer_hw = self.app.hardware['auger_electron_analyzer']

        widget_connections = [
         ('mode', 'retarding_mode_comboBox'),
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
            lq = self.e_analyzer_hw.settings.get_lq(lq_name)
            lq.connect_to_widget(
                getattr(self.ui, widget_name))
