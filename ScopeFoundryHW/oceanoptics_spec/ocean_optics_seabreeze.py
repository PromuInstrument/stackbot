import ctypes
from ctypes import c_long, byref, c_double
import numpy as np
import threading
import time


SEABREEZE_DLL_PATH = r"C:\Program Files\Ocean Optics\SeaBreeze\Library\SeaBreeze.dll"

_S = sbapi = ctypes.cdll.LoadLibrary(SEABREEZE_DLL_PATH)

TRIG_NORMAL = 0
TRIG_SOFTWARE = 1
TRIG_SYNC = 2
TRIG_EXT = 3


# NOTE errors are not checked at this time

class OceanOpticsSpectrometer(object):

    def __init__(self, dev_id=-1, trigger_mode = TRIG_NORMAL, debug=False):
        
        self.debug = debug

        self.lock = threading.Lock()
        
        self.trigger_mode = trigger_mode
        self.err_code = err_code = c_long(0)
        
        
        try:
            with self.lock:
                _S.sbapi_initialize()
        
        
                # get total number of devices, will pick the first one
                ndevs = _S.sbapi_probe_devices()
                ndev_ids = _S.sbapi_get_number_of_device_ids()
                
                if ndev_ids < 1:
                    raise IOError("No OceanOptics devices found")
                                  
                if self.debug: print( "ndevs", ndevs, ndev_ids)
                
                #get dev_id
                dev_ids = np.empty( ndev_ids, dtype=ctypes.c_long) # long
                
                _S.sbapi_get_device_ids( dev_ids.ctypes, ndev_ids )
                
                if self.debug: print("dev_ids", dev_ids)
        
                if dev_id < 0: 
                    if self.debug: print("Devices Found. Will pick the first one")
                    self.dev_id = dev_id = int(dev_ids[0])
                else:
                    if self.debug: print("Devices Found. Will try to pick the dev_id={}".format(dev_id))
                    #assert dev_id in dev_ids
                    self.dev_id = int(dev_id)
                if debug: print("--> dev_id", dev_id)
                
                # open device
                retcode = _S.sbapi_open_device(dev_id, byref(err_code))
                if retcode != 0: self._handle_sbapi_error()
                if debug: print('opened device', dev_id)
        
                # get device type
                dev_type_buffer = ctypes.create_string_buffer(b'', 255)
                _S.sbapi_get_device_type(dev_id, byref(err_code), dev_type_buffer, 255)
                self._handle_sbapi_error()
                self.dev_type = dev_type_buffer.raw.strip(b'\x00').decode()
                if debug: print("dev_type", repr(self.dev_type))
                
                # get features for device, will pick the first one
                # This function returns the total number of spectrometer instances available in the indicated device. Each instance refers to a single optical bench.
                n_features = _S.sbapi_get_number_of_spectrometer_features(int(dev_id), byref(err_code))
                self._handle_sbapi_error() 
                if self.debug: print("Num Spectrometer Features", repr(n_features))
        
                feature_ids = np.empty( n_features, dtype=int)
                _S.sbapi_get_spectrometer_features(dev_id, byref(err_code), feature_ids.ctypes, n_features)
                self._handle_sbapi_error() 
                self.spec_feature_id = spec_feature_id = int(feature_ids[0])
                if debug: print("Spectrometer features", n_features, feature_ids)
        
                # set trigger mode
                #   Mode (Input) a trigger mode
                # (0 = normal, 1 = software, 2 = synchronization, 3 = external hardware, etc
                # - check your particular spectrometer's Data Sheet)
                _S.sbapi_spectrometer_set_trigger_mode(dev_id,spec_feature_id, byref(err_code), self.trigger_mode)       
        
                # get minimum integration time
                self.min_int_time = _S.sbapi_spectrometer_get_minimum_integration_time_micros(dev_id, spec_feature_id, byref(err_code) )
                if debug: print("min_int_time", self.min_int_time, "microsec")
                
                # get spectrum parameters
                self.Nspec = Nspec = _S.sbapi_spectrometer_get_formatted_spectrum_length( dev_id, spec_feature_id, byref(err_code) )
                self.wavelengths = np.zeros( Nspec, dtype=float )
                _S.sbapi_spectrometer_get_wavelengths(dev_id, spec_feature_id, byref(err_code), self.wavelengths.ctypes, Nspec)
                if debug: print("Spectrum wavelength", Nspec, self.wavelengths[[0,1,-2,-1]])
                
                # read dark pixels
                ndark = _S.sbapi_spectrometer_get_electric_dark_pixel_count(dev_id, spec_feature_id, byref(err_code))
                self.dark_indices = np.zeros(ndark, dtype=int)
                _S.sbapi_spectrometer_get_electric_dark_pixel_indices(dev_id, spec_feature_id, byref(err_code), self.dark_indices.ctypes, ndark)
                if debug: print("dark pixels", ndark, self.dark_indices)
        
                # set integration to minimum by default
                self.int_time = self.min_int_time
                _S.sbapi_spectrometer_set_integration_time_micros(dev_id, spec_feature_id, byref(err_code), self.int_time)
        
        except Exception as ex:
            print('Error- could not complete connection to Ocean Optics Spectrometer.', ex)
            self.close()
            return
        
        self.spectrum = np.zeros(Nspec, dtype=float)
                
    def close(self):
        with self.lock:
            _S.sbapi_close_device(self.dev_id, byref(self.err_code))
            _S.sbapi_shutdown()
        
    def set_integration_time(self,int_time):
        """ Set the integration time in microseconds"""
        assert int_time > self.min_int_time
        self.int_time = int(int_time)
        with self.lock:
            _S.sbapi_spectrometer_set_integration_time_micros(
                self.dev_id, self.spec_feature_id, byref(self.err_code), self.int_time)

            
    def set_integration_time_sec(self,int_time):
        return self.set_integration_time(int_time*1e6)
    
    
    ### TEC
    def tec_info(self):
        with self.lock:
            number_of_tec = _S.sbapi_get_number_of_thermo_electric_features(self.dev_id, byref(self.err_code))
            self._handle_sbapi_error()
    
            print('number_of_tec', number_of_tec)
            
            tec_feature_ids = np.zeros(number_of_tec, dtype=c_long)
            n_features_copied = _S.sbapi_get_thermo_electric_features(self.dev_id, byref(self.err_code),
                                                                      tec_feature_ids.ctypes, number_of_tec)
            self._handle_sbapi_error()
    
            
            print('tec feature_ids', tec_feature_ids)
            
            for i in range(number_of_tec):
                tec_feature_id = int(tec_feature_ids[i])
                
                _S.sbapi_tec_read_temperature_degrees_C.restype = ctypes.c_double
                
                temp = _S.sbapi_tec_read_temperature_degrees_C(self.dev_id, tec_feature_id, byref(self.err_code))
                self._handle_sbapi_error()
                print("Read Temperature {} {} {}".format(i, tec_feature_id, temp))
                
    
                #_S.sbapi_tec_set_enable(self.dev_id, feature_id, byref(self.err_code), 1)
                print("ASdf")
                self._handle_sbapi_error()
                #_S.sbapi_tec_set_temperature_setpoint_degrees_C(self.dev_id, feature_id, byref(self.err_code), c_double(-10.0))
                self._handle_sbapi_error()
    
                
                for j in range(100):
                    temp = _S.sbapi_tec_read_temperature_degrees_C(self.dev_id, tec_feature_id, byref(self.err_code))
                    self._handle_sbapi_error()
    
                    print("Read Temperature {} {} {}".format(i, tec_feature_id, temp))
                    time.sleep(0.5)
                
    # 
    #         number_of_tec = _S.sbapi_get_thermo_electric_features(self.dev_id, byref(self.err_code),
    #                 tec_ids, number_of_tec);
    
    def acquire_spectrum(self):
        with self.lock:
            _S.sbapi_spectrometer_get_formatted_spectrum(self.dev_id, self.spec_feature_id, byref(self.err_code), self.spectrum.ctypes, self.Nspec)
            self._handle_sbapi_error()
            return self.spectrum.copy()

    def _handle_sbapi_error(self):
            _S.sbapi_get_error_string.restype  = ctypes.c_char_p
            
            if self.err_code.value == 0:
                return
            error_str = _S.sbapi_get_error_string(self.err_code).decode()
            raise IOError(error_str)

        
    def start_threaded_acquisition(self):
        self.acq_thread = threading.Thread(target=self.acquire_spectrum)
        self.acq_thread.start()
        self.t_start = time.time()

    def is_threaded_acquisition_complete(self):
        return not self.acq_thread.is_alive()
    
    def threaded_time_elapsed_remaining(self):
        now = time.time()
        time_elapsed = now - self.t_start
        time_remaining = self.int_time - time_elapsed
        return time_elapsed, time_remaining
        
if __name__ == '__main__':
    # Live testing
    import pylab as pl
    
    TEST_INT_TIME = 1e4 # microseconds
    
    
    oospec = OceanOpticsSpectrometer(dev_id=-1, debug=True)
    
    oospec.set_integration_time(TEST_INT_TIME)
    
    oospec.tec_info()
     
    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_title("(%i,%i) %s" % (oospec.dev_id, oospec.feature_id, oospec.dev_type))
     
    oospec.acquire_spectrum()
     
    plotline, = pl.plot( oospec.wavelengths, oospec.spectrum )
#     
#     oospec.start_threaded_acquisition()
#     
#     def update_fig(ax):
#         if oospec.is_threaded_acquisition_complete():
#             #print "new data!"
#             plotline.set_ydata( oospec.spectrum )
#             oospec.start_threaded_acquisition()
#             fig.canvas.draw()
#         else:
#             print(oospec.threaded_time_elapsed_remaining())
#     
#     timer = fig.canvas.new_timer( interval= 250)
#     timer.add_callback( update_fig, ax)
#     timer.start()
#     
#     #fig.show()
#     pl.show()