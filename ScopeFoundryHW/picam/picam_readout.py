from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
from qtpy import QtWidgets
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class PicamReadoutMeasure(Measurement):

    name = "picam_readout"
    
    def setup(self):
        
        self.display_update_period = 0.050 #seconds
        self.hw  = self.app.hardware['picam']
        #connect events

        #local logged quantities

    def run(self):

        cam = self.hw.cam

        print("rois|-->", cam.read_rois())

        cam.commit_parameters()
        
        while not self.interrupt_measurement_called:
            dat = cam.acquire(readout_count=1, readout_timeout=-1)
            
            self.roi_data = cam.reshape_frame_data(dat)
            #print "roi_data shapes", [d.shape for d in self.roi_data]
        


    def setup_figure(self):


        self.ui = load_qt_ui_file(sibling_path(__file__, 'picam_readout.ui'))
        
        self.hw.settings.ExposureTime.connect_to_widget(self.ui.int_time_doubleSpinBox) 
        self.hw.settings.SensorTemperatureReading.connect_to_widget(self.ui.temp_doubleSpinBox) 

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.ui.commit_pushButton.clicked.connect(self.hw.commit_parameters)


        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget(border=(0,0,0))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.spec_plot = self.graph_layout.addPlot()
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])
        self.spec_plot.enableAutoRange()
                
        self.graph_layout.nextRow()

        self.img_plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.img_plot.addItem(self.img_item)
        self.img_plot.showGrid(x=True, y=True)
        self.img_plot.setAspectLocked(lock=True, ratio=1)

        self.hist_lut = pg.HistogramLUTItem()
        self.hist_lut.autoHistogramRange()
        self.hist_lut.setImageItem(self.img_item)
        self.graph_layout.addItem(self.hist_lut)

    def update_display(self):
        self.img_item.setImage(self.roi_data[0].T.astype(float), autoLevels=False)
        self.hist_lut.imageChanged(autoLevel=True, autoRange=True)

        self.spec_plot_line.setData(np.average(self.roi_data[0], axis=0))

