from ScopeFoundry import Measurement
import time
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import pyqtgraph as pg
import numpy as np
from ScopeFoundry import h5_io



class WinSpecRemoteReadoutMeasure(Measurement):
    
    name = "winspec_readout"
    
    def setup(self):
        self.SHOW_IMG_PLOT = False
        self.settings.New('continuous', dtype=bool, initial=True, ro=False)
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('wl_calib', dtype=str, initial='winspec', choices=('pixels','raw_pixels','winspec', 'acton_spectrometer'))

        
        
    def pre_run(self):
        self.winspec_hc = self.app.hardware['winspec_remote_client']
        time.sleep(0.05)
        self.winspec_hc.winspec_client

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
        
        self.infline = pg.InfiniteLine(movable=True, angle=90, label='x={value:0.2f}', 
                       labelOpts={'position':0.8, 'color': (200,200,100), 'fill': (200,200,200,50), 'movable': True})         
        self.spec_plot.addItem(self.infline)
                
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


        ### Widgets
        self.settings.continuous.connect_to_widget(self.ui.continuous_checkBox)
        self.settings.wl_calib.connect_to_widget(self.ui.wl_calib_comboBox)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)

        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.app.hardware['winspec_remote_client'].settings.acq_time.connect_bidir_to_widget(self.ui.acq_time_doubleSpinBox)

    def acquire_data(self, debug = False):
        "helper function - called multiple times i spectral maps"
        if debug:
            print(self.name,'acquire_data()')
        W = self.winspec_hc.winspec_client
        if debug:
            print(self.name, 'start acq')
        W.start_acq()
        
        while( W.get_status() ):
            #if debug: print(self.name, 'status', W.get_status())
            if self.interrupt_measurement_called:
                return (None, None)
            time.sleep(0.01)
            
        if debug:
            print(self.name, 'get_data')
        hdr, data = W.get_data()  
        #print("getting_data")
        return hdr,np.array(data).reshape(( hdr.frame_count, hdr.ydim, hdr.xdim) )
        
        
    def evaluate_wls_winspec(self,hdr,debug = False):
        "helper function - called onced in spectral maps"
        if debug:
            print(self.name,'evaluate_wls()')
        #px = (np.arange(hdr.xdim) +1) # works with no binning
        px = np.linspace( 1 + 0.5*(hdr.bin_x-1), 1+ 0.5*((2*hdr.xdim-1)*(hdr.bin_x) + 1)-1, hdr.xdim)
        c = hdr.calib_coeffs
        for i in range(5):
            print('coeff', c[i])
        #print(px)
        wls = c[0] + c[1]*(px) + c[2]*(px**2) # + c[3]*(px**3) + c[4]*(px**4)
        #self.wls = np.polynomial.polynomial.polyval(px, hdr.calib_coeffs) # need to verify, seems wrong
        #print(self.wls)       
        return wls 
    
    def evaluate_wls_acton_spectrometer(self, hdr, px_index):
        hbin = hdr.bin_x
        px_index = np.arange(self.data.shape[-1])
        spec_hw = self.app.hardware['acton_spectrometer']
        return spec_hw.get_wl_calibration(px_index, hbin)        

        
    def run(self):
        
        self.winspec_hc.settings['connected'] = False
        time.sleep(0.2)
        self.winspec_hc.settings['connected'] = True
        time.sleep(0.2)
        
        
        
        while not self.interrupt_measurement_called:
            #print("test")
            try:
                print("start acq")
                hdr,data = self.acquire_data()
                if hdr is None or data is None:
                    raise IOError("Failed to acquire Data (probably interrupted)")
                self.hdr = hdr
                self.data = data
                print("end acq")
                wl_calib = self.settings['wl_calib']
                px_index = np.arange(self.data.shape[-1])
                if wl_calib=='winspec':
                    self.wls = self.evaluate_wls_winspec(self.hdr)
                elif wl_calib=='acton_spectrometer':
                    hbin = self.hdr.bin_x
                    px_index = np.arange(self.data.shape[-1])
                    spec_hw = self.app.hardware['acton_spectrometer']
                    self.wls = self.evaluate_wls_acton_spectrometer(self.hdr, px_index)
                elif wl_calib=='pixels':
                    binning = self.hdr.bin_x
                    px_index = np.arange(self.data.shape[-1])
                    self.wls = binned_px = binning*px_index + 0.5*(binning-1)
                elif wl_calib=='raw_pixels':
                    self.wls = px_index
                else:
                    self.wls = px_index
                
                self.wls_mean = self.wls.mean()
                    
                if self.settings['save_h5']:
                    self.t0 = time.time()
                    self.h5_file = h5_io.h5_base_file(self.app, measurement=self )
                    self.h5_file.attrs['time_id'] = self.t0
                    H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
                
                    #create h5 data arrays
                    H['wls'] = self.wls
                    H['spectrum'] = self.data
                
                    self.h5_file.close()
            finally:
                if not self.settings['continuous']:
                    break
        
        
        
            
    def update_display(self):
        
        if self.SHOW_IMG_PLOT:
            self.img_item.setImage(self.data[0], autoLevels=False)
            self.hist_lut.imageChanged(autoLevel=True, autoRange=True)

        if not hasattr(self, 'data'):
            return
        self.spec_plot_line.setData(self.wls, np.average(self.data[0,:,:], axis=0))
        self.infline.setValue([self.wls_mean,0])