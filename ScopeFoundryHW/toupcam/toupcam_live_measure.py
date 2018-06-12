from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class ToupCamLiveMeasure(Measurement):
    
    name = 'toupcam_live'
    
    def setup(self):
        self.settings.New('auto_level', dtype=bool, initial=False)
    
    def setup_figure(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__,'toupcam_live_measure.ui'))
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        self.settings.activation.connect_to_widget(self.ui.live_checkBox)        
        self.settings.auto_level.connect_to_widget(self.ui.auto_level_checkBox)

        tcam = self.app.hardware['toupcam']        
        tcam.settings.connected.connect_to_widget(self.ui.cam_connect_checkBox)
        tcam.settings.cam_index.connect_to_widget(self.ui.cam_index_doubleSpinBox)
        tcam.settings.res_mode.connect_to_widget(self.ui.res_mode_doubleSpinBox)
        tcam.settings.exposure.connect_to_widget(self.ui.exp_doubleSpinBox)
        tcam.settings.auto_exposure.connect_to_widget(self.ui.auto_exp_checkBox)

                
        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.plot.setAspectLocked(lock=True, ratio=1)
        self.plot.invertY(True)

    
    def run(self):
        
        tcam = self.app.hardware['toupcam']
        tcam.settings['connected'] = True
        
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
            if tcam.settings['auto_exposure']:
                tcam.settings.exposure.read_from_hardware()
        
    def update_display(self):
        cam = self.app.hardware['toupcam'].cam
        im = np.array(cam.get_image_data())
        #print(im.shape, np.max(im), np.mean(im))

        im = self.get_rgb_image()
        self.img_item.setImage(im.swapaxes(0,1), autoLevels=self.settings['auto_level'])
        if not self.settings['auto_level']:
            self.img_item.setLevels((0, 255))


    def get_rgb_image(self):
        cam = self.app.hardware['toupcam'].cam

        data = cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        return bgr[..., ::-1]
#        image = Image.fromarray(bgr, 'RGB')
#        b, g, r = image.split()
#        return Image.merge('RGB', (r, g, b))