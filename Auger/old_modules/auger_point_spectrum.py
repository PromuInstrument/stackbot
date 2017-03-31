from __future__ import division, print_function
from ScopeFoundry import Measurement, LQRange
import pyqtgraph as pg
import numpy as np
import time

class AugerPointSpectrum(Measurement):
    
    name = "AugerPointSpectrum"

    def setup(self):
        
        
        # settings
        lq_settings = dict(dtype=float, ro=False, vmin=0, vmax=2200, unit='V')
        self.settings.New('Energy_min', initial=0, **lq_settings)
        self.settings.New('Energy_max', initial=2000, **lq_settings)
        self.settings.New('Energy_step', **lq_settings)
        self.settings.New('Energy_num_steps', initial=10, dtype=int)
        
        self.settings.New('Dwell_time', initial=0.05, dtype=float, ro=False, vmin=0, unit='s')
        S = self.settings
        
        self.energy_range = LQRange(S.Energy_min, S.Energy_max, 
                                    S.Energy_step, S.Energy_num_steps)
        
        #self.counter_dac_hc = self.app.hardware['Counter_DAC_FPGA_VI_HC']
        #NUM_CHANS = self.counter_dac_hc.NUM_CHANS
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.graph_layout.show()
        self.graph_layout.setWindowTitle("AugerPointSpectrum")
        
        self.plot = self.graph_layout.addPlot(title="AugerPointSpectrum")
        
        self.plot_lines = []
        for i in range(7):
            color = pg.intColor(i)
            plot_line = self.plot.plot([0], pen=color)
            self.plot_lines.append(plot_line)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.plot.addItem(self.vLine)
        
    def run(self):
        print("="*80)
  
        self.e_analyzer = self.app.hardware['auger_electron_analyzer']
        self.counter_dac_hc = self.app.hardware['Counter_DAC_FPGA_VI_HC']
        
        self.counter_dac_hc.engage_FIFO()
              
        N = self.settings["Energy_num_steps"]
        self.chan_spectra = np.zeros((N, 7), dtype=float)
        
        for ii in range(N):
            if self.interrupt_measurement_called:
                break
            
            energy = self.energy_range.array[ii]
            self.e_analyzer.settings['KE'] = energy 
            time.sleep(0.025)
            self.counter_dac_hc.flush_FIFO()
            
            time.sleep(self.settings['Dwell_time'])
            buf_reshaped = self.counter_dac_hc.read_FIFO()
            self.chan_spectra[ii, :] = np.sum(buf_reshaped[0:7,:],axis=1)#/self.settings['Dwell_time']
            
            self.settings['progress'] = 100.*(ii/N)   
            
        self.counter_dac_hc.disengage_FIFO()

            
    def update_display(self):
        self.vLine.setPos(self.e_analyzer.settings['KE'])
            
        for i in range(7):
            self.plot_lines[i].setData(self.energy_range.array, 0*i + self.chan_spectra[:,i])
        self.app.qtapp.processEvents()
