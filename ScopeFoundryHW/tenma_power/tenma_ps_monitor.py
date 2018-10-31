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
        self.settings.New('poll_time', dtype=float, initial=1.0, unit='s')
        
        self.on_new_history_len()
        self.settings.history_len.add_listener(self.on_new_history_len)
        
        self.tenma_hw = self.app.hardware['tenma_powersupply']


    def setup_figure(self):
        
        ui_filename = sibling_path(__file__, "tenma_ps_monitor.ui")
        self.ui = load_qt_ui_file(ui_filename)
        
        self.settings.activation.connect_to_widget(self.ui.run_checkBox)
        self.settings.history_len.connect_to_widget(self.ui.history_len_doubleSpinBox)
        
        self.settings.poll_time.connect_to_widget(self.ui.poll_time_doubleSpinBox)
        
        
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        self.plot_i = self.graph_layout.addPlot(title="Current")
        self.graph_layout.nextRow()
        self.plot_i = self.graph_layout.addPlot(title="Voltage")


        self.c0_plotline = self.plot.plot()
        self.c1_plotline = self.plot.plot()

        self.settings.c0_visible.add_listener(self.c0_plotline.setVisible, bool)
        self.settings.c1_visible.add_listener(self.c1_plotline.setVisible, bool)
        
        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.plot.addItem(self.vline, ignoreBounds=True)
        
        
        hw = self.tenma_hw
        hw.settings.device_name.connect_to_widget(self.ui.device_name_label)
        hw.settings.set_current.connect_to_widget(self.ui.set_current_doubleSpinBox)
        hw.settings.actual_current.connect_to_widget(self.ui.actual_current_doubleSpinBox)
        hw.settings.set_voltage.connect_to_widget(self.ui.set_voltage_doubleSpinBox)
        hw.settings.actual_voltage.connect_to_widget(self.ui.actual_voltage_doubleSpinBox)
        

    def run(self):
        ph_hw = self.picoharp_hw

        while not self.interrupt_measurement_called:
            self.optimize_ii += 1
            self.optimize_ii %= self.OPTIMIZE_HISTORY_LEN

            cr0 = ph_hw.settings.count_rate0.read_from_hardware()
            cr1 = ph_hw.settings.count_rate1.read_from_hardware()

            self.optimize_history[self.optimize_ii,:] = (cr0, cr1)
            time.sleep(self.settings['poll_time']) 
            
            
    def on_new_history_len(self):
        N = self.settings['history_len']
        self.optimize_ii = 0
        self.optimize_history = np.zeros( (N, 2), dtype=float)
        self.OPTIMIZE_HISTORY_LEN = N
        
    def update_display(self):
        self.c0_plotline.setData(self.optimize_history[:,0])
        self.c1_plotline.setData(self.optimize_history[:,1])
        self.vline.setPos(self.optimize_ii)
        
