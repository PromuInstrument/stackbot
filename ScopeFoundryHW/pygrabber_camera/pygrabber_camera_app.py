from ScopeFoundry.base_app import BaseMicroscopeApp

class PyGrabberCameraApp(BaseMicroscopeApp):
    
    name = 'pygrabber_camera'
    
    def setup(self):
        from ScopeFoundryHW.pygrabber_camera.pygrabber_camera_hw import PyGrabberCameraHW
        self.add_hardware(PyGrabberCameraHW(self))
        from ScopeFoundryHW.pygrabber_camera.pygrabber_live_view import PyGrabberCameraLiveMeasure
        self.add_measurement(        PyGrabberCameraLiveMeasure(self))
        
        
    
if __name__ == '__main__':
    app = PyGrabberCameraApp([])
    app.exec_()