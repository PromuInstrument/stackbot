from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class PicoHarpChannelOptimizer(Measurement):
    name = "picoharp_channel_optimizer"
    
    hardware_requirements = ['picoharp']
    
    def setup(self):
        
        self.settings.New('history_len', dtype=int, initial=500)
        self.settings.New('c0_visible', dtype=bool, initial=False)
        self.settings.New('c1_visible', dtype=bool, initial=True)
        
        self.on_new_history_len()
        self.settings.history_len.add_listener(self.on_new_history_len)
        
        self.picoharp_hw = self.app.hardware['picoharp']


    def setup_figure(self):
        
        ui_filename = sibling_path(__file__, "picoharp_channel_optimizer.ui")
        self.ui = load_qt_ui_file(ui_filename)
        
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.settings.c0_visible.connect_to_widget(self.ui.c0_visible_checkBox)
        self.settings.c1_visible.connect_to_widget(self.ui.c1_visible_checkBox)
        self.settings.history_len.connect_to_widget(self.ui.history_len_doubleSpinBox)
        
        ph_hw = self.picoharp_hw
        ph_hw.settings.count_rate0.connect_to_widget(self.ui.c0_doubleSpinBox)
        ph_hw.settings.count_rate1.connect_to_widget(self.ui.c1_doubleSpinBox)
        
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        self.plot = self.graph_layout.addPlot(title="Picoharp Channel Optimizer")

        self.c0_plotline = self.plot.plot()
        self.c1_plotline = self.plot.plot()

        self.settings.c0_visible.add_listener(self.c0_plotline.setVisible, bool)
        self.settings.c1_visible.add_listener(self.c1_plotline.setVisible, bool)
        
        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.plot.addItem(self.vline, ignoreBounds=True)

    def run(self):
        ph_hw = self.picoharp_hw

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN

            cr0 = ph_hw.settings.count_rate0.read_from_hardware()
            cr1 = ph_hw.settings.count_rate1.read_from_hardware()

            self.optimize_history[self.optimize_ii,:] = (cr0, cr1)
            time.sleep(0.100) # Countrates from PH_GetCountRate are updated every 100ms
            
            
    def on_new_history_len(self):
        N = self.settings['history_len']
        self.optimize_ii = 0
        self.optimize_history = np.zeros( (N, 2), dtype=float)
        self.OPTIMIZE_HISTORY_LEN = N
        
    def update_display(self):
        self.c0_plotline.setData(self.optimize_history[:,0])
        self.c1_plotline.setData(self.optimize_history[:,1])
        self.vline.setPos(self.optimize_ii)
        
