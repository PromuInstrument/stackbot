'''Ed Barnard, Alan Buckley'''

from __future__ import division
from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
from qtpy import QtWidgets

class AugerChanHistory(Measurement):
    
    name = "auger_chan_history"
    display_chans = 7
   
    
    def setup(self):
        
        self.settings.New('history_length', dtype=int, initial=1000,vmin=1)
        self.settings.New('dwell', dtype=float, si=True, initial=.05,vmin=1e-5)
        
            #setup gui
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QHBoxLayout()
        self.ui.setLayout(self.layout)
        self.control_widget = QtWidgets.QGroupBox(self.name)
        self.layout.addWidget(self.control_widget, stretch=0)
        self.control_widget.setLayout(QtWidgets.QVBoxLayout())

        self.start_button= QtWidgets.QPushButton("Start")
        self.control_widget.layout().addWidget(self.start_button)
        self.stop_button= QtWidgets.QPushButton("Stop")
        self.control_widget.layout().addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        ui_list=('dwell','history_length')
        self.control_widget.layout().addWidget(self.settings.New_UI(include=ui_list))
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))        
        self.layout.addWidget(self.graph_layout,stretch=1)
        
        self.ui.show()
        self.ui.setWindowTitle("AugerAnalyzerChannelHistory")
        
        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS
        
        self.first_pixel = True
        self.plots = []
        for i in range(1):
            plot = self.graph_layout.addPlot(title="Auger Counts")
            self.graph_layout.nextRow()
            self.plots.append(plot)
            
        self.plot_lines = []
        for i in range(self.display_chans):
            color = pg.intColor(i)
            plot_line = self.plots[0].plot([0], pen=color)
            self.plot_lines.append(plot_line)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.plots[0].addItem(self.vLine)
        
        self.CHAN_HIST_LEN = 1000
        self.history_i = 0
        
    def run(self):
        print(self.name, 'run')
        
        self.first_pixel = True
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
        self.auger_fpga_hw.settings['period'] = self.settings['dwell']

        try:
            while not self.interrupt_measurement_called:    
                self.dwell_time = self.app.hardware['auger_fpga'].settings['int_trig_sample_period']/40e6
    
                buf_reshaped = self.auger_fpga_hw.read_fifo()                
                depth = buf_reshaped.shape[0]
                if depth > 0 and self.first_pixel: #discard first pixel with accumulated counts
                    self.first_pixel = False
                    buf_reshaped = buf_reshaped[1:]
                    depth = buf_reshaped.shape[0]   
                
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
        
        self.vLine.setPos(self.history_i)
        for i in range(self.display_chans):
            self.plot_lines[i].setData(self.chan_history_Hz[i,:])
            #self.plots[i].setTitle("Channel {}: {}".format(i, self.chan_history[i,self.history_i]))
        #self.plot_lines[NUM_CHANS-1].setData(np.bitwise_and(self.chan_history[NUM_CHANS-1,:], 0x7FFFFFFF))
        
        #self.app.qtapp.processEvents()
