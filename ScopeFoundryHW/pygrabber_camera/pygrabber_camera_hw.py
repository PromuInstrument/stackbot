from ScopeFoundry import HardwareComponent
import time

class PyGrabberCameraHW(HardwareComponent):
    
    name = 'pygrabber_camera'
    
    def setup(self):
        
        self.settings.New('cam_id', dtype=int, initial=0, choices=(0,))
        self.settings.New('cam_name', dtype=str, ro=True)
        self.settings.New('format', dtype=int, choices=(0,))
    
        self.add_operation('Refresh_Cameras', self.refresh_camera_list)
    
    def connect(self):
        S =self.settings
        from pygrabber.dshow_graph import FilterGraph

        self.graph = FilterGraph()
        
        self.graph.add_input_device(S['cam_id'])

        S['cam_name'] = self.graph.get_input_devices()[S['cam_id']]
        formats = [("{}: {} {}x{} {}bit".format(*x), x[0])
                     for x in self.graph.get_formats()]
        
        S.format.change_choice_list(formats)
        self.graph.set_format(S['format'])
        
        self.img_buffer = []

        self.graph.add_sample_grabber(self.image_callback)
        self.graph.add_null_render()
        self.graph.prepare()
        self.graph.run()

    def threaded_update(self):
        self.graph.grab_frame()
        time.sleep(0.1)
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'graph'):
            del self.graph
            
    def refresh_camera_list(self):
        from pygrabber.dshow_graph import FilterGraph

        graph = FilterGraph()
            
        cams = graph.get_input_devices()
        camera_choices = [("{}: {}".format(cam_id, cam_name), cam_id) 
                          for cam_id, cam_name in enumerate(cams)]
        self.settings.cam_id.change_choice_list(camera_choices)
        
        del graph

    def image_callback(self, img):
        self.img_buffer.append(img)
        if len(self.img_buffer) > 20:
            self.img_buffer = self.img_buffer[-20:]
