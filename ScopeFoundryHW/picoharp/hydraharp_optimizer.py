'''
Created on May 7, 2019

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
import numpy as np
import pyqtgraph as pg
import time
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class HydraHarpOptimizerMeasure(Measurement):

    name = "hydraharp_channel_optimizer"
    
    hardware_requirements = ['hydraharp']
    
       
    def setup(self):
        
        self.n_channels = 2
        
        self.settings.New('history_len', dtype=int, initial=300)
        self.settings.New('sync_visible', dtype=bool, initial=True)        
        self.settings.New('c0_visible', dtype=bool, initial=True)
        self.settings.New('c1_visible', dtype=bool, initial=True)
        
        self.on_new_history_len()
        self.settings.history_len.add_listener(self.on_new_history_len)
        
        self.hydraharp_hw = self.app.hardware['hydraharp']


        
    def setup_figure(self):
        
        ui_filename = sibling_path(__file__, "hydraharp_channel_optimizer.ui")
        self.ui = load_qt_ui_file(ui_filename)
        
        
        #Connect hardware settings
        hh_hw = self.hydraharp_hw
        HS = hh_hw.settings
        
        spinboxes = ['DeviceIndex', 'HistogramChannels', 'Tacq', 'Resolution',
                     'StopCount',
                     'SyncOffset', 'CFDLevelSync', 'CFDZeroCrossSync',
                     'SyncRate', 'SyncPeriod',]
        for i in range(self.n_channels):
            spinboxes += ['{}{}'.format(x,i) for x in ['CFDLevel', 'CFDZeroCross', 'ChanOffset']]        
        for spinbox in spinboxes:
            widget = getattr(self.ui, '{}_doubleSpinBox'.format(spinbox))
            getattr(HS, spinbox).connect_to_widget(widget)
            
        
        HS.SyncDivider.connect_to_widget(self.ui.SyncDivider_comboBox)
        
        
        lcd_numbers = ['SyncRate'] + ['CountRate'+str(i) for i in range(self.n_channels)]
        for ln in lcd_numbers:
            widget = getattr(self.ui, '{}_lcdNumber'.format(ln))
            getattr(HS, ln).connect_to_widget(widget)
            
            
        checkBoxes = ['ChanEnable{}'.format(i) for i in range(self.n_channels)]
        for cB in checkBoxes:
            widget = getattr(self.ui, '{}_checkBox'.format(cB))
            getattr(HS, cB).connect_to_widget(widget)        

        
        HS.connected.connect_to_widget(self.ui.connected_checkBox)    
        HS.Mode.connect_to_widget(self.ui.Mode_comboBox)
        HS.RefSource.connect_to_widget(self.ui.RefSource_comboBox)
        HS.StopOnOverflow.connect_to_widget(self.ui.StopOnOverflow_checkBox)
        HS.Binning.connect_to_widget(self.ui.Binning_comboBox)

                


        #Optimizer Measurement
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.settings.sync_visible.connect_to_widget(self.ui.sync_visible_checkBox)
        self.settings.c0_visible.connect_to_widget(self.ui.c0_visible_checkBox)
        self.settings.c1_visible.connect_to_widget(self.ui.c1_visible_checkBox)
        self.settings.history_len.connect_to_widget(self.ui.history_len_doubleSpinBox)
        
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.channel_optimizer_GroupBox.layout().addWidget(self.graph_layout)

        self.plot = self.graph_layout.addPlot(title="Hydraharp Channel Optimizer")

        self.sync_plotline = self.plot.plot()
        self.c0_plotline = self.plot.plot(pen='b')
        self.c1_plotline = self.plot.plot(pen='g')

        self.settings.sync_visible.add_listener(self.sync_plotline.setVisible, bool)
        self.settings.c0_visible.add_listener(self.c0_plotline.setVisible, bool)
        self.settings.c1_visible.add_listener(self.c1_plotline.setVisible, bool)
        
        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.plot.addItem(self.vline, ignoreBounds=True)



    def run(self):
        hh_hw = self.hydraharp_hw

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN

            sync = hh_hw.settings['SyncRate']
            cr0 = hh_hw.settings['CountRate0']
            cr1 = hh_hw.settings['CountRate1']

            self.optimize_history[self.optimize_ii,:] = (sync, cr0, cr1)
            self.optimize_history_std[self.optimize_ii,:] = np.std(self.optimize_history, (0,1) )
            time.sleep(0.100) 
            
    def on_new_history_len(self):
        N = self.settings['history_len']
        self.optimize_ii = 0
        self.optimize_history = np.zeros( (N, 3), dtype=float)
        self.optimize_history_std = np.zeros_like(self.optimize_history)
        self.OPTIMIZE_HISTORY_LEN = N
        
    def update_display(self):
        self.sync_plotline.setData(self.optimize_history[:,0])
        self.c0_plotline.setData(self.optimize_history[:,1])
        self.c1_plotline.setData(self.optimize_history[:,2])
        self.vline.setPos(self.optimize_ii)
        
