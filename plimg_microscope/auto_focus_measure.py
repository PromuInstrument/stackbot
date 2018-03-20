from ScopeFoundry import Measurement
import numpy as np
import time
import pyqtgraph as pg

class AutoFocusMeasure(Measurement):
    
    name = 'auto_focus'
    
    def setup(self):
        
        self.settings.New('use_current_z', dtype=bool, initial=False)
        self.settings.New('z_center', dtype=float, initial=50, spinbox_decimals=3)
        self.settings.New('z_range', dtype=float, initial=1, spinbox_decimals=3)
        self.settings.New('Nz', dtype=int, initial=50)
        
        self.settings.New('z_correction', dtype=float)
        
        
    def setup_figure(self):
        # add a pyqtgraph GraphicsLayoutWidget to the measurement ui window
        if hasattr(self, 'graph_layout'):
            self.graph_layout.deleteLater() # see http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            del self.graph_layout
        self.ui = self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        #self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        ## Add plot and plot items
        self.plot = self.graph_layout.addPlot(title="APD Z auto-focus")
        self.plot_line = self.plot.plot()
        self.plot_line_fine = self.plot.plot(pen='r')
        self.line_z_center_start = pg.InfiniteLine(angle=0, movable=False, pen='b')
        self.line_z_center_coarse = pg.InfiniteLine(angle=0, movable=False, pen='y')
        self.line_z_center_fine = pg.InfiniteLine(angle=0, movable=False, pen='r')
        
        self.plot.addItem(self.line_z_center_start, ignoreBounds=True)
        self.plot.addItem(self.line_z_center_coarse, ignoreBounds=True)
        self.plot.addItem(self.line_z_center_fine, ignoreBounds=True)

        
    def run(self):
        S = self.settings        
        # hardware
        self.apd_counter_hw = self.app.hardware['apd_counter']
        self.apd_count_rate = self.apd_counter_hw.settings.count_rate            
        stage = self.app.hardware['mcl_xyz_stage']

        if S['use_current_z']:
            S['z_center'] = stage.settings['z_target']
        
        # switch to apd using flip mirror
        old_flip_position = self.app.hardware['flip_mirrors'].settings['apd_flip'] 
        self.app.hardware['flip_mirrors'].settings['apd_flip'] = True
        

        # create data arrays
        
        self.z_array = np.linspace(S['z_center']-0.5*S['z_range'],
                                   S['z_center']+0.5*S['z_range'],
                                   S['Nz'], dtype=float)
                
        self.z_array_fine = np.linspace(S['z_center']-0.5*S['z_range']/4,
                                   S['z_center']+0.5*S['z_range']/4,
                                   2*S['Nz'], dtype=float)
        
        self.apd_counts = np.zeros(S['Nz'], dtype=float)
        self.apd_counts_fine = np.zeros(2*S['Nz'], dtype=float)

        self.z_center_coarse = S['z_center']
        self.z_center_fine = S['z_center']

        # move to start position
        original_z = stage.settings['z_target']
        stage.settings['z_target'] = self.z_array[0]
        time.sleep(2*self.apd_counter_hw.settings['int_time'])
        
        # for loop through z-array
        for i, z in enumerate(self.z_array):
            # check for interrupt:
            if self.interrupt_measurement_called:
                break
            # move z
            stage.settings['z_target'] = z
            # record apd
            time.sleep(self.apd_counter_hw.settings['int_time'])
            x = self.apd_count_rate.read_from_hardware()
            self.apd_counts[i] = x
        
            # find max
            z_center_coarse = self.z_center_coarse = self.z_array[np.argmax(self.apd_counts)]
        
        # Fine scan
        self.z_array_fine = np.linspace(z_center_coarse-0.5*S['z_range']/4,
                                   z_center_coarse+0.5*S['z_range']/4,
                                   2*S['Nz'], dtype=float)
        
        stage.settings['z_target'] = self.z_array_fine[0]
        time.sleep(2*self.apd_counter_hw.settings['int_time'])
        
        for i, z in enumerate(self.z_array_fine):
            # check for interrupt:
            if self.interrupt_measurement_called:
                break            
            # move z
            stage.settings['z_target'] = z
            # record APD
            time.sleep(self.apd_counter_hw.settings['int_time'])
            x = self.apd_count_rate.read_from_hardware()
            self.apd_counts_fine[i] = x
            self.z_center_fine = self.z_array_fine[np.argmax(self.apd_counts_fine)]
        
        if self.interrupt_measurement_called:
            # move to original z
            stage.settings['z_target'] = original_z
        else:
            stage.settings['z_target'] = self.z_center_fine
        
        # find max, if success move to z_max (z_center + z_correction)

        # switch to apd using flip mirror
        self.app.hardware['flip_mirrors'].settings['apd_flip'] = old_flip_position

        
    def update_display(self):
        self.plot_line.setData(self.apd_counts, self.z_array)
        self.plot_line_fine.setData(self.apd_counts_fine, self.z_array_fine)
        
        S = self.settings
        self.line_z_center_start.setPos(S['z_center'])
        self.line_z_center_coarse.setPos(self.z_center_coarse)
        self.line_z_center_fine.setPos(self.z_center_fine)
        
        