import numpy as np
from ScopeFoundry import Measurement
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import os
from ScopeFoundry import h5_io
import time


class OOSpecLive(Measurement):

    name = "oo_spec_live"
    
    def setup(self):
        self.display_update_period = 0.050 #seconds
        self.hw = self.app.hardware['ocean_optics_spec']
        
        self.settings.New("continuous", dtype=bool, initial=True)
        self.settings.New('save_h5', dtype=bool, initial=False, ro=False)
        self.settings.New('spec_units',dtype=str, initial='nm', ro=True)
        self.settings.New('bg_subtract', dtype=bool, initial=False, ro=False)
        self.settings.New('baseline_subtract', dtype=bool, initial=True, ro=False)
        self.settings.New('baseline_val', dtype=float, initial=2070.0, ro=False)
        self.add_operation('Use as BG', self.set_current_spec_as_bg)
        self.add_operation('save_data',self.save_data)
        self.settings.New('roi_min',dtype=float, initial=300.0, ro=False)
        self.settings.New('roi_max',dtype=float, initial=700.0, ro=False)

        
    def setup_figure(self):
               
        self.ui = load_qt_ui_file(sibling_path(__file__, 'oo_spec_live.ui'))
        
        
        ### Plot
        self.plot = pg.PlotWidget()
        self.ui.plot_groupBox.layout().addWidget(self.plot)

        self.plotline = self.plot.plot()
        
        self.plot.setLabel('bottom', 'wavelength (nm)')
        #ax.set_xlabel("wavelengths (nm)")
        #ax.set_ylabel("Laser Spectrum (counts)")
        
        self.roi = pg.LinearRegionItem(values=(self.settings.roi_min.val,self.settings.roi_max.val))
        self.plot.addItem(self.roi)
        
        def update_roi():
            (rmin, rmax) = self.roi.getRegion()
            self.settings.roi_min.update_value(rmin)
            self.settings.roi_max.update_value(rmax)
        self.roi.sigRegionChanged.connect(update_roi)
        
        ### Controls
        self.hw.settings.int_time.connect_to_widget(self.ui.int_time_doubleSpinBox)
        self.hw.settings.connected.connect_to_widget(self.ui.hw_connect_checkBox)
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        
        self.settings.continuous.connect_to_widget(self.ui.continuous_checkBox)
        
        self.settings.bg_subtract.connect_to_widget(self.ui.bg_subtract_checkBox)
        self.ui.set_bg_pushButton.clicked.connect(self.set_current_spec_as_bg)
        
        self.ui.save_h5_pushButton.clicked.connect(self.save_data)
        
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        self.settings.baseline_subtract.connect_to_widget(self.ui.baseline_sub_checkBox)
        self.settings.baseline_val.connect_to_widget(self.ui.baseline_val_doubleSpinBox)
        
        
    def startstop(self):
        self.settings.activation.update_value(new_val= ~self.settings.activation.val)
        
    def run(self):
        if self.settings['continuous']:
            while not self.interrupt_measurement_called:    
                self.hw.acquire_spectrum()
                self.wls = self.hw.wavelengths
                self.spectrum = self.hw.get_spectrum()
        else:
            self.hw.acquire_spectrum()
            self.wls = self.hw.wavelengths
            self.spectrum = self.hw.get_spectrum()
            if self.settings['save_h5']:
                self.save_data(self)
                
    
    def update_display(self):
        spec = np.array(self.spectrum)
        
        spec[self.hw.get_dark_indices()] = np.nan
        if spec.sum() is None:
            print('spec sum not a number')

        if self.settings['bg_subtract']:
            spec = spec - self.bg_spec
        
        if self.settings['baseline_subtract']:
            spec = spec - self.settings.baseline_val.value
        
        self.plotline.setData(self.hw.wavelengths, spec)

    def set_current_spec_as_bg(self):
        self.bg_spec = self.hw.get_spectrum()
        
    def save_data(self):
        t = time.localtime(time.time())
        t_string = "{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(int(str(t[0])[:-2]), t[1], t[2], t[3], t[4], t[5])
        fname = os.path.join(self.app.settings['save_dir'], "%s_%s" % (t_string, self.name))
        with h5_io.h5_base_file(self.app,  fname = fname + ".h5") as H:
                print("Saving " + fname + ".h5")
                M = h5_io.h5_create_measurement_group(measurement=self, h5group=H)
                M.create_dataset('spectrum', data=self.spectrum, compression='gzip')
                M.create_dataset('wavelengths',data=self.wavelengths, compression='gzip')
