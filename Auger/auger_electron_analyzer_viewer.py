from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class AugerElectronAnalyzerViewer(Measurement):
    
    name = 'auger_e_analyzer_view'
    
    def setup(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "auger_electron_analyzer_viewer.ui"))

        self.e_analyzer_hw = self.app.hardware['auger_electron_analyzer']

        widget_connections = [
         ('multiplier', 'multiplier_checkBox'),
         ('KE', 'KE_doubleSpinBox'),
         ('pass_energy', 'pass_energy_doubleSpinBox'),
         ('crr_ratio', 'crr_ratio_doubleSpinBox'),
         ('resolution', 'resolution_doubleSpinBox'),
         ('CAE_mode', 'cae_checkBox'),
         ('quad_X1', 'qX1_doubleSpinBox'),
         ('quad_Y1', 'qY1_doubleSpinBox'),
         ('quad_X2', 'qX2_doubleSpinBox'),
         ('quad_Y2', 'qY2_doubleSpinBox'),
         ]
        for lq_name, widget_name in widget_connections:
            lq = self.e_analyzer_hw.settings.get_lq(lq_name)
            lq.connect_to_widget(
                getattr(self.ui, widget_name))

    def run(self):
        analyzer = self.app.hardware['auger_electron_analyzer']

        from ScopeFoundryHW.ni_daq import NI_AdcTask
        import numpy as np
        import time
        
        try:
            self.app.measurements['auger_spectrum'].setup_analyzer()
            time.sleep(3.0) #let electronics settle

            
            self.adc_task = NI_AdcTask('/X-6368/ai4', range=10.0, name='adc_monitor', terminalConfig='default')
            #self.adc_task.set_rate(rate=2e6, count=100000, finite=False, clk_source="")
            #print("rate", self.adc_task.get_rate())
            #self.adc_task.start()
            
            adc_data = np.zeros(65536, dtype=float)
            for i in range(65536):
                analyzer.analyzer.write_KE_binary(i)
                #time.sleep(0.010)
                #buf = self.adc_task.read_buffer()
                adc_data[i] = self.adc_task.get() #buf.mean()
                if i % 64  == 0:
                    print(i, adc_data[i])
                    if self.interrupt_measurement_called:
                        break
        finally:
            self.adc_task.close()
            np.savetxt('outer_vsKEbinary.txt', adc_data)