from ScopeFoundry.measurement import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class ControlPanelMeasure(Measurement):
    
    name = 'control_panel'
    
    def setup_figure(self):
        
        ui = self.ui = load_qt_ui_file(sibling_path(__file__, 'control_panel.ui'))
        
        self.app.measurements['chamber_data_log'].settings.activation.connect_to_widget(
            ui.data_logging_checkBox)
        
        self.app.measurements['chamber_process_xls'].settings.activation.connect_to_widget(
            ui.xls_go_checkBox)
        
        self.app.measurements['chamber_process_xls'].settings.xls_fname.connect_to_browse_widgets(
            ui.xls_lineEdit, ui.xls_browse_pushButton)
        
        prg = self.app.hardware['pressure_gauge']
        prg.settings.pressure.connect_to_widget(ui.pressure_doubleSpinBox)

        
        ps1 = self.app.hardware['lambda_zup1']
        ps1.settings.current_actual.connect_to_widget(ui.ps1_i_act_doubleSpinBox)
        ps1.settings.current_setpoint.connect_to_widget(ui.ps1_i_set_doubleSpinBox)
        ps1.settings.voltage_actual.connect_to_widget(ui.ps1_v_act_doubleSpinBox)
        ps1.settings.voltage_setpoint.connect_to_widget(ui.ps1_v_set_doubleSpinBox)
        ps1.settings.output_enable.connect_to_widget(ui.ps1_output_checkBox)
        
        ps2 = self.app.hardware['lambda_zup2']
        ps2.settings.current_actual.connect_to_widget(ui.ps2_i_act_doubleSpinBox)
        ps2.settings.current_setpoint.connect_to_widget(ui.ps2_i_set_doubleSpinBox)
        ps2.settings.voltage_actual.connect_to_widget(ui.ps2_v_act_doubleSpinBox)
        ps2.settings.voltage_setpoint.connect_to_widget(ui.ps2_v_set_doubleSpinBox)
        ps2.settings.output_enable.connect_to_widget(ui.ps2_output_checkBox)

        
        ui.lamp_on_pushButton.clicked.connect(self.lamp_on)
        ui.lamp_off_pushButton.clicked.connect(self.lamp_off)        
        
        mfc = self.app.hardware['sierra_mfc']
        mfc.settings.flow.connect_to_widget(ui.mfc_flow_doubleSpinBox)
        mfc.settings.setpoint.connect_to_widget(ui.mfc_setpoint_doubleSpinBox)        
        
        tc = self.app.hardware['tc_reader_stream']
        tc.settings.temp0.connect_to_widget(ui.temp_doubleSpinBox)
        
    def lamp_on(self):
        self.app.hardware['lambda_zup1'].settings['output_enable'] = True
        self.app.hardware['lambda_zup2'].settings['output_enable'] = True        

    def lamp_off(self):
        self.app.hardware['lambda_zup1'].settings['output_enable'] = False
        self.app.hardware['lambda_zup2'].settings['output_enable'] = False        