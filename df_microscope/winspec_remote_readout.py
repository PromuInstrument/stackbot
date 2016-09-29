from ScopeFoundry import Measurement
import time
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import pyqtgraph as pg
import numpy as np
from ScopeFoundry import h5_io

class WinSpecRemoteReadout(Measurement):
    
    name = "WinSpecRemoteReadout"
    
    def setup(self):
        self.SHOW_IMG_PLOT = False
        
        self.settings.New('save_h5', dtype=bool, initial=True)
        
    
    def setup_figure(self):

        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout

        #self.ui = self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        #self.ui.setWindowTitle(self.name)
        self.ui = load_qt_ui_file(sibling_path(__file__,"winspec_remote_readout.ui"))
        

        self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        self.spec_plot = self.graph_layout.addPlot()
        self.spec_plot_line = self.spec_plot.plot([1,3,2,4,3,5])
        self.spec_plot.enableAutoRange()
                
        self.graph_layout.nextRow()

        if self.SHOW_IMG_PLOT:
            self.img_plot = self.graph_layout.addPlot()
            self.img_item = pg.ImageItem()
            self.img_plot.addItem(self.img_item)
            self.img_plot.showGrid(x=True, y=True)
            self.img_plot.setAspectLocked(lock=True, ratio=1)
    
            self.hist_lut = pg.HistogramLUTItem()
            self.hist_lut.autoHistogramRange()
            self.hist_lut.setImageItem(self.img_item)
            self.graph_layout.addItem(self.hist_lut)

        #self.show_ui()
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.app.hardware.WinSpecRemoteClient.settings.acq_time.connect_bidir_to_widget(self.ui.acq_time_doubleSpinBox)
    
    def run(self):
        
        
        winspec_hc = self.app.hardware.WinSpecRemoteClient
        W = winspec_hc.winspec_client
        W.start_acq()
        
        while( W.get_status() ):
            if self.interrupt_measurement_called:
                break
            time.sleep(0.01)
        
        hdr, data = W.get_data()
        self.data = np.array(data).reshape(( hdr.frame_count, hdr.ydim, hdr.xdim) )
        
        #px = (np.arange(hdr.xdim) +1) # works with no binning
        px = np.linspace( 1 + 0.5*(hdr.bin_x-1), 1+ 0.5*((2*hdr.xdim-1)*(hdr.bin_x) + 1)-1, hdr.xdim)
        c = hdr.calib_coeffs
        for i in range(5):
            print(c[i])
        print(px)
        self.wls = c[0] + c[1]*(px) + c[2]*(px**2) # + c[3]*(px**3) + c[4]*(px**4)
        self.wls = np.polynomial.polynomial.polyval(px, hdr.calib_coeffs) # need to verify
        print(self.wls)

        if self.settings['save_h5']:
            self.t0 = time.time()
            self.h5_file = h5_io.h5_base_file(self.app, "%i_%s.h5" % (self.t0, self.name) )
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
        
            #create h5 data arrays
            H['wls'] = self.wls
            H['spectrum'] = self.data
        
            self.h5_file.close()

    def update_display(self):
        
        if self.SHOW_IMG_PLOT:
            self.img_item.setImage(self.data[0], autoLevels=False)
            self.hist_lut.imageChanged(autoLevel=True, autoRange=True)

        self.spec_plot_line.setData(self.wls, np.average(self.data[0,:,:], axis=0))
