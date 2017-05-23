from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

class APDOptimizerCBMeasurement(Measurement):

    name = "apd_optimizer"
        
    def setup(self):
        
        self.ui = load_qt_ui_file(sibling_path(__file__, "apd_optimizer.ui"))

        self.display_update_period = 0.1 #seconds
        
        # TODO add saving
        self.ui.save_data_checkBox.setEnabled(False)
        
        self.app.hardware['apd_counter'].settings.int_time.connect_to_widget(
            self.ui.int_time_doubleSpinBox)

        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

    def setup_figure(self):
        # add a pyqtgraph GraphicsLayoutWidget to the measurement ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        ## Add plot and plot items
        self.opt_plot = self.graph_layout.addPlot(title="APD Optimizer")
        self.optimize_plot_line = self.opt_plot.plot([1,3,2,4,3,5])
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.opt_plot.addItem(self.vLine, ignoreBounds=True)
        
        
    def run(self):
        apd_counter = self.app.hardware['apd_counter']
        if not apd_counter.settings['connected']:
            apd_counter.settings['connected']=True
            time.sleep(0.1)
        
        self.display_update_period = self.app.hardware['apd_counter'].settings['int_time']
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
    
    def update_display(self):
        apd_counter = self.app.hardware['apd_counter']
        self.vLine.setPos(apd_counter.mean_buffer_i)
        X = apd_counter.mean_buffer
        self.optimize_plot_line.setData(X)
