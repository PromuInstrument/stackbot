from ScopeFoundry import Measurement
import time
import pyqtgraph as pg

class SpecStepAndGlue(Measurement):
    
    name = 'spec_step_and_glue'

    def setup(self):
        self.settings.New_Range('center_wl',dtype=float,ro=False)
    
    def setup_figure(self):
        self.ui = self.plot = pg.PlotWidget()\

    def pre_run(self):
        self.plot.clear()
        
        
    def run(self):
        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']
        
        self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called

        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['read_single'] = True
        self.andor_ccd_readout.settings['save_h5'] = False
        time.sleep(0.01)

        center_wls = self.settings.ranges['center_wl'].array
        for ii, center_wl in enumerate(center_wls):
            self.set_progress(100*(ii+1)/len(center_wls+1))
            
            self.app.hardware['acton_spectrometer'].settings['center_wl'] = center_wl
            
            self.andor_ccd_readout.run()
            self.andor_ccd_readout.settings['read_single'] = True
            
            self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called
            
            spec = self.andor_ccd_readout.spectra_data
            time.sleep(0.5)
            import numpy as np

            W = 12
            N = len(spec)
            self.plot.plot(np.linspace(-0.5,0.5,N)*W+center_wl, spec)
            if self.interrupt_measurement_called:
                break
            
    def post_run(self):
        self.andor_ccd_readout.settings['save_h5'] = True
        
    def update_display(self):
        self.andor_ccd_readout.update_display()
