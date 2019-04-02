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
        self.debug = True
        
        # Create logged quantities
        self.oo_spec_int_time = self.add_logged_quantity(
                                            name="int_time", 
                                            dtype=float,
                                            ro = False,
                                            vmin = 0.0001,
                                            vmax = 1000,
                                            unit = 'sec',
                                            initial = 0.1,
                                            )
        self.settings.New('dev_id', dtype=int, initial=-1)
        self.settings.New('dev_type', dtype=str, ro=True)



    def connect(self):

        #connect to hardware        
        spec = self.oo_spectrometer = OceanOpticsSpectrometer(debug=self.debug)
        
        self.settings['dev_id'] = spec.dev_id
        self.settings['dev_type'] = spec.dev_type
                        
        # Connect logged quantities to hardware
        self.oo_spec_int_time.hardware_set_func=self.oo_spectrometer.set_integration_time_sec

    def disconnect(self):
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'oo_spectrometer'):
            #disconnect hardware
            self.oo_spectrometer.close()
            
            # clean up hardware object
            del self.oo_spectrometer
            