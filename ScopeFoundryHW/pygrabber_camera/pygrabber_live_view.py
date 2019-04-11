from ScopeFoundry.measurement import Measurement
import pyqtgraph as pg
import time
class PyGrabberCameraLiveMeasure(Measurement):
    
    name = 'pygrabber_camera_live'
    
    def setup(self):
        
        self.ui = self.img_view = pg.ImageView()
        
    def run(self):
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
            
    def update_display(self):
        self.img_view.setImage(self.app.hardware['pygrabber_camera'].img_buffer[-1])