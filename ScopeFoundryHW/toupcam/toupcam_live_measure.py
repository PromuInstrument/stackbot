from ScopeFoundry import Measurement
import pyqtgraph as pg
from qtpy import QtCore
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
        tcam.settings.auto_exposure.connect_to_widget(self.ui.auto_exp_checkBox)
        tcam.settings.magnification.connect_to_widget(self.ui.mag_doubleSpinBox)
        # connect to sliders 
        tcam.settings.ctemp.connect_to_widget(self.ui.ctemp_slider)
        tcam.settings.tint.connect_to_widget(self.ui.tint_slider)
        
        tcam.settings.contrast.connect_to_widget(self.ui.contrast_slider)
        tcam.settings.brightness.connect_to_widget(self.ui.brightness_slider)
        tcam.settings.gamma.connect_to_widget(self.ui.gamma_slider)
        
        #tcam.settings.ctemp.updated_value[int].connect(self.ui.ctemp_slider.setValue)
        #self.ui.ctemp_slider.sliderMoved[int].connect(tcam.settings.ctemp.update_value)
        
        #self.ui.ctemp_slider.valueChanged.connect(self.valuechange)
        #self.ui.ctemp_value.setText(str(self.ui.ctemp_slider.value()))
        
        # connect to spinboxes 
        tcam.settings.exposure.connect_to_widget(self.ui.exp_value)
        tcam.settings.ctemp.connect_to_widget(self.ui.ctemp_value)
        tcam.settings.tint.connect_to_widget(self.ui.tint_value)
        
        tcam.settings.contrast.connect_to_widget(self.ui.contrast_value)
        tcam.settings.brightness.connect_to_widget(self.ui.brightness_value)
        tcam.settings.gamma.connect_to_widget(self.ui.gamma_value)

        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.plot.setAspectLocked(lock=True, ratio=1)
        
        self.center_roi = pg.CircleROI((0-5,0-5), (10,10) , movable=False, pen=pg.mkPen('c', width=3))
        self.plot.addItem(self.center_roi)
        #\font = QFont()
        #font.setPointSize(14)
        #font.setBold(True)
        self.roi_label = pg.TextItem('')
        #self.roi_label.setFont(font)
        self.plot.addItem(self.roi_label)
        self.roi_label.setText(str(self.center_roi.size()[0]))
        
        self.ui.snap_pushButton.clicked.connect(self.snap_h5)
        ## to do add functionality that a double click on a position in the image moves the stage to the position.
    def run(self):
        
        tcam = self.app.hardware['toupcam']
        tcam.settings['connected'] = True
        
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
            if tcam.settings['auto_exposure']:
                tcam.settings.exposure.read_from_hardware()
        
    def update_display(self):
        tcam = self.app.hardware['toupcam']
        self.im = self.get_rgb_image()
        self.im = np.flip(self.im.swapaxes(0,1),0)
        self.img_item.setImage(self.im, autoLevels=self.settings['auto_level'])
        if not self.settings['auto_level']:
            self.img_item.setLevels((0, 255))
        
        
        width  = tcam.settings['width_micron']
        height = tcam.settings['height_micron']
        res_mode = tcam.settings['res_mode']
        x_center, y_center = tcam.settings['centerx_micron'], tcam.settings['centery_micron']
        
        x0 = -x_center
        y0 = -y_center
        
        self.img_rect = pg.QtCore.QRectF(x0, y0, width, height)
        self.img_item.setRect(self.img_rect)
        self.roi_label.setText('{:.2f} micron'.format(self.center_roi.size()[0]))
        
    def get_rgb_image(self):
        cam = self.app.hardware['toupcam'].cam

        data = cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        return bgr[..., ::-1]
#        image = Image.fromarray(bgr, 'RGB')
#        b, g, r = image.split()
#        return Image.merge('RGB', (r, g, b))


    def snap_h5(self):
        
        #
        from ScopeFoundry import h5_io
        self.app.hardware['asi_stage'].correct_backlash(0.02)
        
        try:
            self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
            im = self.get_rgb_image()
            im = np.flip(im.swapaxes(0,1),0)
            H['image'] = im
            self.update_display()
        finally:
            self.h5_file.close()
            print('saved file successfully')