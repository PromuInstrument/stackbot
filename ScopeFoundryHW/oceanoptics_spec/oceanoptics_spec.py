#         print "Initializing OceanOptics spectrometer functionality"
#         self.oo_spectrometer =     OceanOpticsSpectrometer(debug=self.HARDWARE_DEBUG)
#         self.oo_spec_int_time = self.add_logged_quantity(name="oo_spec_int_time", dtype=float,
#                                                 hardware_set_func=self.oo_spectrometer.set_integration_time_sec)
#         self.ui.oo_spec_int_time_doubleSpinBox.valueChanged[float].connect(self.oo_spec_int_time.update_value)
#         self.oo_spec_int_time.updated_value[float].connect(self.ui.oo_spec_int_time_doubleSpinBox.setValue)
#         self.oo_spec_int_time.update_value(0.1)
#         self.oo_spectrometer.start_threaded_acquisition()


from ScopeFoundry import HardwareComponent
try:
    from .ocean_optics_seabreeze import OceanOpticsSpectrometer
except Exception as err:
    print("Cannot load required modules for OceanOptics Spectrometer:", err)

class OceanOpticsSpectrometerHW(HardwareComponent):
    
    name = 'ocean_optics_spec'

    def setup(self):
        S = self.settings
        # Create logged quantities
        S.New(name="int_time", dtype=float, ro=False, vmin=0.0001, vmax=1000, unit='s', initial=0.1,)
        S.New('dev_id', dtype=int, initial=-1)
        S.New('dev_type', dtype=str, ro=True)

    def connect(self):
        #connect to hardware
        S = self.settings        
        self.spec = OceanOpticsSpectrometer(debug=self.debug_mode, dev_id=S['dev_id'])
        
        
        S['dev_id'] = self.spec.dev_id
        S['dev_type'] = self.spec.dev_type
                        
        # Connect logged quantities to hardware
        S.int_time.connect_to_hardware( write_func=self.spec.set_integration_time_sec )
        self.wavelengths = self.spec.wavelengths

    def disconnect(self):
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'oo_spectrometer'):
            #disconnect hardware
            self.spec.close()
            
            # clean up hardware object
            del self.spec
            
    def acquire_spectrum(self):
        self.spectrum = self.spec.acquire_spectrum()
        
    def get_spectrum(self):
        return self.spec.spectrum.copy()
        
    def get_dark_indices(self):
        return self.spec.dark_indices
            