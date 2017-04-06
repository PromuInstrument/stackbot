'''Frank Ogletree'''

from __future__ import division
from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
from qtpy import QtWidgets

from ScopeFoundryHW.ni_daq import NI_AdcTask

class AugerPressureHistory(Measurement):
    
    name = "auger_pressure_history"
    
    def setup(self):
        
        self.settings.New('history_length', dtype=int, initial=1000,vmin=1)
        
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
        
        ui_list=('history_length',)
        self.control_widget.layout().addWidget(self.settings.New_UI(include=ui_list))
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))        
        self.layout.addWidget(self.graph_layout,stretch=1)
        
        self.ui.show()
        self.ui.setWindowTitle("auger_pressure_history")
        
        self.HIST_LEN = 1000
        self.NUM_CHANS = 2
        self.history_i = 0
        
        self.plots = []
        for i in range(1):
            plot = self.graph_layout.addPlot(title="Pressure")
            plot.setLogMode(y=True)
            plot.setYRange(-12,-6)
            plot.showGrid(y=True,alpha=1.0)
            plot.addLegend()
            self.graph_layout.nextRow()
            self.plots.append(plot)
        
        names=('Nano','Prep')
        self.plot_lines = []
        for i in range(self.NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.plots[0].plot([1], pen=pg.mkPen(color, width=4), name=names[i])
            self.plot_lines.append(plot_line)
        
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.plots[0].addItem(self.vLine)
        
        self.HIST_LEN = 1000
        self.NUM_CHANS = 2
        self.history_i = 0
    
        
    def volts_to_pressure(self,volts):
        '''
        convert log output of ion gauge into mBarr)
        '''
        vmin=np.array([0.0,0.078])
        vmax=np.array([10.0,2.89])
        vhi=np.array([1.0,1.0])
        vlo=np.array([0.0,0.0])
        
        pmin=np.array([1e-11,1e-12])
        pmax=np.array([1e-2,0.2])
        vr = (volts-vmin)/(vmax-vmin)
        vr = np.minimum(1.0,np.maximum(vr,0.0))
        pr=np.log(pmax/pmin)
        return pmin*np.exp(vr*pr)           
            
    def run(self):
        print(self.name, 'run')
        
        self.HIST_LEN = self.settings['history_length']
        
        self.chan_history = np.zeros( (self.NUM_CHANS, self.HIST_LEN), dtype=float )
        self.chan_history_Hz = np.zeros( (self.NUM_CHANS, self.HIST_LEN) )
        
        self.history_i = 0
        self.ring_buf_index = 0
        
        chans='X-6368/ai5:6'
        self.adc = NI_AdcTask(chans,name='pressure')
        try:
            while not self.interrupt_measurement_called:
                self.ring_buf_index = self.history_i % self.HIST_LEN
                volts = self.adc.get()
                #print( self.ring_buf_index, pressure)
                self.chan_history[:, self.ring_buf_index] = volts
                self.chan_history_Hz[:,self.ring_buf_index] = self.volts_to_pressure(volts) 
                              
                self.history_i += 1       
        finally:
            self.adc.close()
            self.adc = None
        
            
    def update_display(self):
        #print("chan_history shape", self.chan_history.shape)
        
        self.vLine.setPos(self.ring_buf_index)
        for i in range(self.NUM_CHANS):
            self.plot_lines[i].setData(self.chan_history_Hz[i,:])
            #self.plots[i].setTitle("Channel {}: {}".format(i, self.chan_history[i,self.history_i]))
