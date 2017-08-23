'''
Created on Aug 22, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import HardwareComponent
from operator import itemgetter
from ScopeFoundryHW.thorlabs_mirror.dmp40_dev import ThorlabsDMP40
import ctypes
import numpy as np

class ThorlabsDMP40_HW(HardwareComponent):
    
    name = "dmp40_hw"
    
    zernike = {
            'Z4_Astigmatism_45': 0x00000001,
            'Z5_Defocus': 0x00000002,
            'Z6_Astigmatism_0': 0x00000004,
            'Z7_Trefoil_Y': 0x00000008,
            'Z8_Coma_X': 0x00000010,
            'Z9_Coma_Y': 0x00000020,
            'Z10_Trefoil_X': 0x00000040,
            'Z11_Tetrafoil_Y': 0x00000080,
            'Z12_Sec_Astig_Y': 0x00000100,
            'Z13_3O_Sph_Abberation': 0x00000200,
            'Z14_Sec_Astig_X': 0x00000400,
            'Z15_Tetrafoil_X': 0x00000800}
    
    def setup(self):
        self.settings.New(name="Z4_Astigmatism_45", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z5_Defocus", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z6_Astigmatism_0", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z7_Trefoil_Y", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z8_Coma_X", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z9_Coma_Y", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z10_Trefoil_X", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z11_Tetrafoil_Y", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z12_Sec_Astig_Y", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z13_3O_Sph_Abberation", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z14_Sec_Astig_X", dtype=bool, initial=False, ro=False)
        self.settings.New(name="Z15_Tetrafoil_X", dtype=bool, initial=False, ro=False)
    
        for i in range(4,16):
            self.settings.New(name="Z{}_Amplitude".format(i), dtype=float, fmt="%.3f", initial=0.0, vmin=-1.0, vmax=1.0, ro=False)
        self.add_operation(name="apply_Zernike_pattern", op_func=self.set_zernike_patterns)
        self.add_operation(name="reset", op_func=self.reset)
                   
    def connect(self):
        self.dev = ThorlabsDMP40(debug=self.debug_mode)
        
    
    def zernike_active_readout(self):
        self.read_from_hardware()
        selected = []
        for k, _ in self.zernike.items():
            if self.settings[k]:
                print(k)
                selected.append(k)
        return selected
            
    def reset(self):
        if self.dev:
            self.dev.reset()
        else:
            pass
    
    def calculate_zernike_integer(self):
        selected_zernikes = self.zernike_active_readout()
        print(selected_zernikes, self.zernike)
        print(itemgetter(*selected_zernikes))
        zernike_integers = itemgetter(*selected_zernikes)(self.zernike)
#         print(zernike_integers, len(zernike_integers))
        if isinstance(zernike_integers, int):
            return zernike_integers
        else:
            return sum(zernike_integers)
        
    def set_zernike_patterns(self):
        amplitudes = []
        for i in range(4,16):
            amplitudes.append(self.settings['Z{}_Amplitude'.format(i)])
        np_ampl = np.asarray(amplitudes)
        ct_ampl = self.dev.np64_to_ctypes64(np_ampl)
        mirror_pattern = (ctypes.c_double * 40)()
        zern_int = self.calculate_zernike_integer()
        self.dev.dll_ext.TLDFMX_calculate_zernike_pattern(self.dev.instHandle, 
                                                          ctypes.c_uint32(zern_int), ct_ampl, 
                                                          ctypes.byref(mirror_pattern))
        self.dev.set_segment_voltages(np.frombuffer(mirror_pattern)) 
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
        
#         self.dev.close()
#         del self.dev