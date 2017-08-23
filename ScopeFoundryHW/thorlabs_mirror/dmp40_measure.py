'''
Created on Aug 22, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class ThorlabsDMP40_Measure(Measurement):
    
    name = 'dmp40_measure'
    
    def setup(self):

        self.dmp40_hw = self.app.hardware['dmp40_hw']
        self.ui_filename = sibling_path(__file__, "mirror.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        self.dmp40_hw.settings.get_lq('Z4_Astigmatism_45').connect_to_widget(
            self.ui.Z4_checkBox)
        self.dmp40_hw.settings.get_lq('Z5_Defocus').connect_to_widget(
            self.ui.Z5_checkBox)
        self.dmp40_hw.settings.get_lq('Z6_Astigmatism_0').connect_to_widget(
            self.ui.Z6_checkBox)
        self.dmp40_hw.settings.get_lq('Z7_Trefoil_Y').connect_to_widget(
            self.ui.Z7_checkBox)
        self.dmp40_hw.settings.get_lq('Z8_Coma_X').connect_to_widget(
            self.ui.Z8_checkBox)
        self.dmp40_hw.settings.get_lq('Z9_Coma_Y').connect_to_widget(
            self.ui.Z9_checkBox)
        self.dmp40_hw.settings.get_lq('Z10_Trefoil_X').connect_to_widget(
            self.ui.Z10_checkBox)
        self.dmp40_hw.settings.get_lq('Z11_Tetrafoil_Y').connect_to_widget(
            self.ui.Z11_checkBox)
        self.dmp40_hw.settings.get_lq('Z12_Sec_Astig_Y').connect_to_widget(
            self.ui.Z12_checkBox)
        self.dmp40_hw.settings.get_lq('Z13_3O_Sph_Abberation').connect_to_widget(
            self.ui.Z13_checkBox)
        self.dmp40_hw.settings.get_lq('Z14_Sec_Astig_X').connect_to_widget(
            self.ui.Z14_checkBox)
        self.dmp40_hw.settings.get_lq('Z15_Tetrafoil_X').connect_to_widget(
            self.ui.Z15_checkBox)
        
        self.dmp40_hw.settings.get_lq("Z4_Amplitude").connect_to_widget(self.ui.Z4_Astigmatism_45)
        self.dmp40_hw.settings.get_lq("Z5_Amplitude").connect_to_widget(self.ui.Z5_Defocus)
        self.dmp40_hw.settings.get_lq("Z6_Amplitude").connect_to_widget(self.ui.Z6_Astigmatism_0)
        self.dmp40_hw.settings.get_lq("Z7_Amplitude").connect_to_widget(self.ui.Z7_Trefoil_Y)
        self.dmp40_hw.settings.get_lq("Z8_Amplitude").connect_to_widget(self.ui.Z8_Coma_X)
        self.dmp40_hw.settings.get_lq("Z9_Amplitude").connect_to_widget(self.ui.Z9_Coma_Y)
        self.dmp40_hw.settings.get_lq("Z10_Amplitude").connect_to_widget(self.ui.Z10_Trefoil_X)
        self.dmp40_hw.settings.get_lq("Z11_Amplitude").connect_to_widget(self.ui.Z11_Tetrafoil_Y)
        self.dmp40_hw.settings.get_lq("Z12_Amplitude").connect_to_widget(self.ui.Z12_Sec_Astig_Y)
        self.dmp40_hw.settings.get_lq("Z13_Amplitude").connect_to_widget(self.ui.Z13_3O_Sph_Abberation)
        self.dmp40_hw.settings.get_lq("Z14_Amplitude").connect_to_widget(self.ui.Z14_Sec_Astig_X)
        self.dmp40_hw.settings.get_lq("Z15_Amplitude").connect_to_widget(self.ui.Z15_Tetrafoil_X)
        
        
        