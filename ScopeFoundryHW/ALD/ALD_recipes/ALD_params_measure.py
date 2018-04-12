'''
Created on Apr 11, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
import time

class ALD_params(Measurement):
    
    name = 'ALD_params'
    
    def __init__(self, app):
        Measurement.__init__(self, app)
        
    def setup(self):
        self.settings.New('RF_pulse_duration', dtype=int, initial=1)
        self.settings.New('history_length', dtype=int, initial=1000, vmin=1)
        
        self.ui_enabled = True
        if self.ui_enabled:
            self.ui_setup()
            

    def ui_setup(self):
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.show()
        self.ui.setWindowTitle('ALD Control Panel')
        self.ui.setLayout(self.layout)
        
        
        self.rf_widget = QtWidgets.QGroupBox('RF Settings')
        self.layout.addWidget(self.rf_widget)
        self.rf_widget.setLayout(QtWidgets.QVBoxLayout())
        
        plot_ui_list = ('history_length',)
        self.rf_widget.layout().addWidget(self.settings.New_UI(include=plot_ui_list))
        
        self.rf_plot_widget = pg.GraphicsLayoutWidget()
        self.rf_plot = self.rf_plot_widget.addPlot(title='RF Power')
        self.rf_plot.showGrid(y=True)
        self.rf_plot.addLegend()
        self.rf_widget.layout().addWidget(self.rf_plot_widget)
        
        
        self.recipe_control_widget = QtWidgets.QGroupBox('Recipe Controls')
        self.layout.addWidget(self.recipe_control_widget)
        self.recipe_control_widget.setLayout(QtWidgets.QHBoxLayout())
        
        self.recipe_start_button = QtWidgets.QPushButton('Start')
        self.recipe_stop_button = QtWidgets.QPushButton('Stop')
        self.recipe_control_widget.layout().addWidget(self.recipe_start_button)
        self.recipe_control_widget.layout().addWidget(self.recipe_stop_button)
        self.recipe_start_button.clicked.connect(self.app.measurements['ALD_routine'].start)
        self.recipe_stop_button.clicked.connect(self.app.measurements['ALD_routine'].interrupt)
        