'''Ed Barnard, Alan Buckley'''

from __future__ import division
from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
from qtpy import QtWidgets

class AugerAnalyzerChannelHistory(Measurement):
    
    name = "auger_chan_hist"
    
   
    
    def setup(self):
        
        self.settings.New('chan_history_len', dtype=int, initial=5000,vmin=1)
        
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.ui.setLayout(self.layout)
        self.start_button= QtWidgets.QPushButton("Start")
        self.layout.addWidget(self.start_button)
        self.stop_button= QtWidgets.QPushButton("Stop")
        self.layout.addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        
        self.layout.addWidget(self.graph_layout)
        
        self.ui.show()
        self.ui.setWindowTitle("AugerAnalyzerChannelHistory")
        
        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS
        
        self.plots = []
        for i in range(NUM_CHANS):
            plot = self.graph_layout.addPlot(title="Channel %i" % i)
            self.graph_layout.nextRow()
            self.plots.append(plot)
            
        self.plot_lines = []
        for i in range(NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.plots[i].plot([0], pen=color)
            self.plot_lines.append(plot_line)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.plots[0].addItem(self.vLine)
        
        self.CHAN_HIST_LEN = 8000
        self.history_i = 0
        
    def run(self):
        print(self.name, 'run')
        
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS

        # Set continuous internal triggering
        self.auger_fpga_hw.settings['int_trig_sample_count'] = 0 
        # Reset trigger count
        self.auger_fpga_hw.settings['trigger_mode'] = 'off' 
        time.sleep(0.01)
        self.auger_fpga_hw.flush_fifo()
        
        self.CHAN_HIST_LEN = self.settings['chan_history_len']
        
        self.chan_history = np.zeros( (NUM_CHANS, self.CHAN_HIST_LEN), dtype=np.uint32 )
        self.chan_history_Hz = np.zeros( (NUM_CHANS, self.CHAN_HIST_LEN) )
        
        self.history_i = 0
         
        # start triggering
        self.auger_fpga_hw.settings['trigger_mode'] = 'int'

        try:
            while not self.interrupt_measurement_called:
    
                self.dwell_time = self.app.hardware['auger_fpga'].settings['int_trig_sample_period']/40e6
    
                buf_reshaped = self.auger_fpga_hw.read_fifo()
                
                depth = buf_reshaped.shape[0]
                
                #print(buf_reshaped)
    
                if depth >0:
                    
                    ring_buf_index_array = (self.history_i + np.arange(depth, dtype=int)) % self.CHAN_HIST_LEN
                    
                    self.chan_history[:, ring_buf_index_array] = buf_reshaped.T
                    self.chan_history_Hz[:,ring_buf_index_array] = buf_reshaped.T / self.dwell_time
                    
                    self.history_i = ring_buf_index_array[-1]
                
                time.sleep(self.display_update_period)
        finally:
            self.auger_fpga_hw.settings['trigger_mode'] = 'off'
        
            
    def update_display(self):
        #print("chan_history shape", self.chan_history.shape)
        
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS
        
        self.vLine.setPos(self.history_i)
        for i in range(NUM_CHANS):
            self.plot_lines[i].setData(self.chan_history_Hz[i,:])
            self.plots[i].setTitle("Channel {}: {}".format(i, self.chan_history[i,self.history_i]))
        self.plot_lines[NUM_CHANS-1].setData(np.bitwise_and(self.chan_history[NUM_CHANS-1,:], 0x7FFFFFFF))
        
        #self.app.qtapp.processEvents()
