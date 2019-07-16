"""
Created on 7/11/2019
@author: Camille, Edward Barnard, Benedikt Ursprung
"""

from ScopeFoundry import Measurement
import numpy as np
import time
import pyqtgraph as pg
from qtpy import QtWidgets


class AutoFocusMeasure(Measurement):
    '''focuses based on optimization of a (logged) quantity'''
            
    name = 'auto_focus'
    
    def setup(self):
        self.settings.New('use_current_z_as_center', dtype=bool, initial=True)  
        
        self.optimization_quantity_choices = [
                        # Add more choices here in the form
                        # (some_name, lq_path to the quantity to be optimized)
                        # Note: the lq should either automatically update within each sampling period
                        #       or have a read_hardware_func!
                        # At the end the stage moves to (position + z_correction) where that lq was MAXIMAL
                        # TODO: MINIMAL
                         ('hydraharp_CountRate0','hardware/hydraharp/CountRate0'),
                         ('hydraharp_CountRate1','hardware/hydraharp/CountRate1'),
                         ('picoharp_CountRate0','hardware/hydraharp/count_rate'),
                         ('toupcam_inv_FWHM','measure/toupcam_spot_optimizer/inv_FWHM'),
                         ]
        
        self.settings.New('optimization_quantity', dtype=str, choices=self.optimization_quantity_choices,
                          initial='hydraharp_CountRate0')      
                
        lq_kwargs = {'spinbox_decimals':6, 'unit':'mm'}
        self.settings.New_Range('z', include_center_span=True, 
                                initials=[-0.001,0.001,0.00002],
                                **lq_kwargs)
        self.settings.New('z_correction', initial=0.0,**lq_kwargs)     
        self.settings.New('sampling_period', float, initial=0.050, unit='s', si=True)
        self.settings.New('N_samples', int, initial=10)
        
        self.z_optimal_history = []
        self.t0 = time.time()

        
    def setup_figure(self):      
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.setLayout(self.layout)

        ## Add settings
        S = self.settings
        settings_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(settings_layout)
        
        settings_layout.addWidget( S.New_UI(['activation', 'optimization_quantity', 
                                             'N_samples', 'sampling_period']) )
        settings_layout.addWidget( S.New_UI(['use_current_z_as_center', 
                                             'z_center', 'z_span', 'z_num']) )
        settings_layout.addWidget( S.New_UI(['z_correction']) )
                                   
                                   
        ## Add plot and plot items
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.layout.addWidget(self.graph_layout)

        self.plot = self.graph_layout.addPlot(title="Z auto-focus")
        self.plot_line = self.plot.plot()
        self.plot_line_fine = self.plot.plot(pen='r')
        self.line_z_center_start = pg.InfiniteLine(angle=0, movable=False, pen='b')
        self.line_z_center_coarse = pg.InfiniteLine(angle=0, movable=False, pen='y')
        self.line_z_center_fine = pg.InfiniteLine(angle=0, movable=False, pen='r')
    
        self.plot.addItem(self.line_z_center_start, ignoreBounds=True)
        self.plot.addItem(self.line_z_center_coarse, ignoreBounds=True)
        self.plot.addItem(self.line_z_center_fine, ignoreBounds=True)

        self.plot.enableAutoRange()

        
    def get_optimization_quantity(self):
        x = 0.0
        for q in range(self.settings['N_samples']):
            time.sleep(self.settings['sampling_period']) 
            if self.optimization_lq.hardware_read_func is not None:
                x += self.optimization_lq.hardware_read_func()
            else:
                x += self.optimization_lq.val
        return x/self.settings['N_samples']
    
            
    def run(self):
        S = self.settings
        z_position = self.app.hardware['attocube_xyz_stage'].settings.z_position
        z_target_position = self.app.hardware['attocube_xyz_stage'].settings.z_target_position

        # set the (logged quantity) to be maximized
        self.optimization_lq = self.app.lq_path(S['optimization_quantity']) 

        if S['use_current_z_as_center']:
            S['z_center'] = z_position.val
        
        # switch to apd using flip mirror
        #old_flip_position = self.app.hardware['flip_mirrors'].settings['apd_flip'] 
        #self.app.hardware['flip_mirrors'].settings['apd_flip'] = True
        
        # create data arrays
        self.z_array = np.linspace(S['z_center']-0.5*S['z_span'],
                                   S['z_center']+0.5*S['z_span'],
                                   S['z_num'], dtype=float)       
        self.quantity_records = np.zeros(S['z_num'], dtype=float)
        self.z_center_coarse = S['z_center']
        self.z_center_fine = S['z_center']

        # move to start position
        original_z = z_position.val
        z_target_position.update_value( self.z_array[0] )
        time.sleep(0.1)
        
        # for loop through z-array
        for i, z in enumerate(self.z_array):
            self.set_progress(i*100.0/S['z_num']/3)
            # check for interrupt:
            if self.interrupt_measurement_called:
                break
            # move z
            z_target_position.update_value(z)
            self.quantity_records[i] = self.get_optimization_quantity()
        
        z_center_coarse = self.z_center_coarse = self.z_array[np.argmax(self.quantity_records)]
        
        
        # Repeat fine scan
        self.z_array_fine = np.linspace(z_center_coarse-0.5*S['z_span']/4,
                                        z_center_coarse+0.5*S['z_span']/4,
                                        2*S['z_num'], dtype=float)        
        self.quantity_records_fine = np.ones(2*S['z_num'], dtype=float) * self.quantity_records.max()

        z_target_position.update_value(self.z_array_fine[0])
        time.sleep(0.1)
        
        for i, z in enumerate(self.z_array_fine):
            self.set_progress((S['z_num']+i)*100.0/S['z_num']/3)
            if self.interrupt_measurement_called:
                break            
            # move z
            z_target_position.update_value(z)
            self.quantity_records_fine[i] = self.get_optimization_quantity()       
            self.z_center_fine = self.z_array_fine[np.argmax(self.quantity_records_fine)]
        
        if self.interrupt_measurement_called:
            z_target_position.update_value(original_z)
        else:
            z_target_position.update_value(self.z_center_fine + S['z_correction'])
            self.z_optimal_history.append( [self.z_center_fine, int((time.time() - self.t0)), S['optimization_quantity']] ) 
            print('z_optimal, time (s), optimization_quantity')
            for x in self.z_optimal_history: print(*x)     


    def update_display(self):
        self.plot.enableAutoRange()

        self.plot_line.setData(self.quantity_records, self.z_array)
        if hasattr(self, 'apd_counts_fine'):
            self.plot_line_fine.setData(self.quantity_records_fine, self.z_array_fine)
        
        S = self.settings
        self.line_z_center_start.setPos(S['z_center'])
        self.line_z_center_coarse.setPos(self.z_center_coarse)
        self.line_z_center_fine.setPos(self.z_center_fine)       
        
        self.plot.setLabels(bottom=S['optimization_quantity'], left='z position')
        
        