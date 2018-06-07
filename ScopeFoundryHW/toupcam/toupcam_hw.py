from ScopeFoundry import HardwareComponent


class ToupCamHW(HardwareComponent):
    
    name = 'toupcam'
    
    def setup(self):
        S = self.settings
        
        S.New('cam_index', dtype=int, initial=0)
        S.New('res_mode', dtype=int, initial=2)
        
        S.New('auto_exposure', dtype=bool)
        S.New('exposure', dtype=float, unit='s', spinbox_decimals=3)
        
    def connect(self):
        from .toupcam.camera import ToupCamCamera, get_number_cameras
        
        S = self.settings
        self.cam = ToupCamCamera(resolution=S['res_mode'], cam_index=S['cam_index'])
        self.cam.open()
        
        S.auto_exposure.connect_to_hardware(
            read_func = self.cam.get_auto_exposure,
            write_func = self.cam.set_auto_exposure
            )
        S.auto_exposure.read_from_hardware()
        S.exposure.connect_to_hardware(
            read_func = self.get_exposure_time,
            write_func = self.set_exposure_time
            )
        S.exposure.read_from_hardware()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'cam'):
            self.cam.close()
            del self.cam
            
    def get_exposure_time(self):
        return 1e-6 * self.cam.get_exposure_time()
    
    def set_exposure_time(self, exp_time):
        self.cam.set_exposure_time( int(1e6*exp_time))