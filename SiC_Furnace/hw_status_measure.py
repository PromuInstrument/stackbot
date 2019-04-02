from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class HWStatusMeasure(Measurement):
    name = 'hw_status'
    
    
    def setup(self):
        pass
    def setup_figure(self):
        ui  = self.ui = load_qt_ui_file(sibling_path(__file__, 'hw_status_measure.ui'))

        self.settings.activation.connect_to_widget(ui.run_checkBox)
        
        hw = self.app.hardware
        
        hw['MFC_N2'].settings.setpoint.connect_to_widget(
            ui.mfc_n2_setpoint_doubleSpinBox)
        hw['MFC_N2'].settings.mass_flow.connect_to_widget(
            ui.mfc_n2_flow_doubleSpinBox)        
        hw['MFC_Ar'].settings.setpoint.connect_to_widget(
            ui.mfc_ar_setpoint_doubleSpinBox)
        hw['MFC_Ar'].settings.mass_flow.connect_to_widget(
            ui.mfc_ar_flow_doubleSpinBox)
        hw['MFC_H2'].settings.setpoint.connect_to_widget(
            ui.mfc_h2_setpoint_doubleSpinBox)
        hw['MFC_H2'].settings.mass_flow.connect_to_widget(
            ui.mfc_h2_flow_doubleSpinBox)
                
        hw['alicat_pc'].settings.setpoint.connect_to_widget(
            ui.pc_setpoint_doubleSpinBox)

        hw['alicat_pc'].settings.pressure.connect_to_widget(
            ui.pc_pressure_doubleSpinBox)
        
        
        hw['optris_pyrometer'].settings.temp.connect_to_widget(ui.pyro_temp_doubleSpinBox)
        
        hw['pid_pyro'].settings.pv_temp.connect_to_widget(
            ui.pyro_pv_doubleSpinBox)
        hw['pid_pyro'].settings.sv_setpoint.connect_to_widget(
            ui.pyro_sv_doubleSpinBox)
        hw['pid_pyro'].settings.output1.connect_to_widget(
            ui.pyro_outp_doubleSpinBox)
        
        hw['pid_outside'].settings.pv_temp.connect_to_widget(
            ui.outside_pv_doubleSpinBox)
        
        
    def run(self):
        
        while not self.interrupt_measurement_called:
            for hw in ['MFC_N2', 'MFC_Ar', 'MFC_H2', 'alicat_pc']:
                self.app.hardware[hw].read_state()
            self.app.hardware['pid_pyro'].read_from_hardware()
            self.app.hardware['pid_outside'].read_from_hardware()            