from ScopeFoundry import Measurement
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

class TestMeasure(Measurement):
    
    name = "test_measurements"

    def setup(self):
        "create settings"
        
        self.settings.New('Channels length', dtype=int, initial=5000,vmin=1)
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.graph_layout.show()
        self.graph_layout.setWindowTitle("AugerAnalyzerChannels")
        
#         self.vLine = pg.InfiniteLine(angle=90, movable=False)
#         self.plots[0].addItem(self.vLine)
        
#         self.CHAN_HIST_LEN = 8000
#         self.history_i = 0
    
    
    def run(self):
        Nx=10
        Ny=10
        self.imageA = np.zeros((9, Ny, Nx))
        #self.randomnumbers =[]
        #run in thread for data acq
        #self.chan_history_Hz = np.zeros( (8, self.CHAN_HIST_LEN) )
        while not self.interrupt_measurement_called:
#             randomnumber = np.random.rand()
#             self.randomnumbers.append(randomnumber)
#             time.sleep(0.1)
#             self.history_i = self.history_i +1
            for j in range(Nx):
                for i in range(Ny):
                    self.imageA[:, j, i] = np.random.rand()
                    time.sleep(.01)
        
    def setup_figure(self):

        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.graph_layout.show()
        self.graph_layout.setWindowTitle('pyqtgraph example: ImageItem')

        plot_pos = np.array([[0,0],[0,1],[0,2],[1,0],[1,1],[1,2],[2,0],[2,1],[2,2]])
        self.img_plots = []
        self.img_items = []
        for i in range(9):
            img_plot = self.graph_layout.addPlot(row=plot_pos[i,0], col=plot_pos[i,1])
            img_item = pg.ImageItem()
            img_plot.addItem(img_item)
            img_plot.showGrid(x=True, y=True)
            img_plot.setAspectLocked(lock=True, ratio=1)
            self.img_plots.append(img_plot)
            self.img_items.append(img_item)
        
        self.hist_lut = pg.HistogramLUTItem()
        self.graph_layout.addItem(self.hist_lut, colspan=1, rowspan=3, col=3,row=0)
        self.hist_lut.setImageItem(self.img_items[0])
        #self.hist_lut.vb.setLimits(yMin=0, yMax=1)
        self.hist_lut.sigLookupTableChanged.connect(self.on_Lookup_Table_Changed)
        self.hist_lut.sigLevelsChanged.connect(self.on_Lookup_Table_Changed)
        
    def on_Lookup_Table_Changed(self):
        for i in range(9):
            self.img_items[i].setLookupTable(self.hist_lut.getLookupTable)
            self.img_items[i].setLevels(self.hist_lut.region.getRegion())
        #self.graph_layout.addItem(self.img_item)
        #view.addItem(self.img_item)
        
        
    def update_display(self):
#         self.vLine.setPos(self.history_i)
#         self.plot_lines[0].setData(self.randomnumbers)
        for i in range(9):
            self.img_items[i].setImage(self.imageA[i].T)
        self.app.qtapp.processEvents()