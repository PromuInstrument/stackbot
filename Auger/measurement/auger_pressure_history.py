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
        
        self.settings.New('delta_t', dtype=float, vmin=0.0, initial=1.0)
        #self.settings.New('start_time', dtype=str, )
        
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
        
        self.control_widget.layout().addWidget(self.settings.New_UI())
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))        
        self.layout.addWidget(self.graph_layout,stretch=1)
        
        self.ui.show()
        self.ui.setWindowTitle("auger_pressure_history")
        
        self.NUM_CHANS = 2
        
        self.plots = []
        for i in range(1):
            plot = self.graph_layout.addPlot(title="Pressure")
            plot.setLogMode(y=True)
            plot.setYRange(-11,-6)
            plot.showGrid(y=True,alpha=1.0)
            plot.addLegend()
            self.graph_layout.nextRow()
            self.plots.append(plot)
        
        names=('Prep','Nano')
        self.plot_lines = []
        for i in range(self.NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.plots[0].plot([1], pen=pg.mkPen(color, width=4), name=names[i])
            self.plot_lines.append(plot_line)
        
        
    def volts_to_pressure(self,volts):
        '''
        convert log output of ion gauge into mBarr)
        FIX not working for prep ion gauge, vmin or vmax must be wrong...
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
        
        block = 20
        self.chan_history_pressure = np.zeros( (self.NUM_CHANS, block) )
        self.chan_history_pressure[:,:] = 1e-11
        self.history_i = 0
        
        chans='X-6368/ai5:6'
        self.adc = NI_AdcTask(chans,name='pressure')
        try:
            while not self.interrupt_measurement_called:
                volts=0.0
                i_ave = 0
                start = time.time()
                while (time.time() - start) < self.settings['delta_t'] or i_ave == 0:
                    i_ave += 1
                    volts += self.adc.get()
                volts /= i_ave
                pressure = self.volts_to_pressure(volts)
                if self.history_i < block:
                    self.chan_history_pressure[:,self.history_i] = pressure
                else:
                    self.chan_history_pressure \
                        = np.append(self.chan_history_pressure,pressure[:,np.newaxis],axis=1)
                #print(volts, self.chan_history_pressure.shape)
                self.history_i += 1       
        finally:
            self.adc.close()
            self.adc = None
        
            
    def update_display(self):        
        for i in range(self.NUM_CHANS):
            self.plot_lines[i].setData(self.chan_history_pressure[i,:])           #self.plots[i].setTitle("Channel {}: {}".format(i, self.chan_history[i,self.history_i]))
