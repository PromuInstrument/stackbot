'''
Created July 2016

@author: Daniel B. Durham
revised Frank Ogletree March 2017
'''

from __future__ import division, print_function
from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
import scipy.optimize as opt
from qtpy import QtWidgets

'''
Alternative: 
minimize f(x,*args) where x is 2d quad array, x2=y2=0, *args gives delay/dwell,
    moves to x then gets -counts
scipy.optimize.brute()
    evaluate on grid to get x1 = starting point, use fraction of grid min for ftol
scipy.optimize.fmin noise-tolerant simplex Nelder-Mead
    x1 starting, 4d search, xtol = 0.1, 

start with max energy (easier to hit starting point), drop energy in 20% steps
save coord array, -fmin vs energy 
'''

class AugerSimplexOptimizer(Measurement):
    
    name = "AugerSimplexOptimizer"
    
    qmin = -100
    qmax = 100
    couple1_2 = -0.52

    def setup(self):
        
        """#Settings for quad optimization over energy range
        lq_settings = dict(dtype=float, ro=False, vmin=0, vmax=2200, unit='V')
        self.settings.New('Energy_min', initial=0, **lq_settings)
        self.settings.New('Energy_max', initial=2000, **lq_settings)
        self.settings.New('Energy_step', **lq_settings)
        self.settings.New('Energy_num_steps', initial=10, dtype=int)
        S = self.settings
        
        self.energy_range = LQRange(S.Energy_min, S.Energy_max, 
                                    S.Energy_step, S.Energy_num_steps)"""
        
        #Settings for quad optimization parameters
        lq_quad = dict(dtype=float, ro=False, vmin=-self.qmin, vmax=self.qmax, unit='%')
#         self.settings.New('Quad_X1_Min', initial=-10, **lq_quad)
#         self.settings.New('Quad_X1_Max', initial=10, **lq_quad)
#         self.settings.New('Quad_X1_Tol', initial=0.1, dtype=float, ro=False, unit='%', vmin=0)
#         
#         self.settings.New('Quad_Y1_Min', initial=-10, **lq_quad)
#         self.settings.New('Quad_Y1_Max', initial=10, **lq_quad)
        self.settings.New('Quad_Tol', initial=0.1, dtype=float, ro=False, unit='%', vmin=1e-4)
        self.settings.New('Intensity_Tol', initial=0.1, dtype=float, ro=False, unit='%', vmin=1e-4)
        
        self.settings.New('Max_Iterations', initial=5, dtype=int, ro=False, vmin=0)       
        self.settings.New('dwell', initial=0.05, dtype=float, ro=False, vmin=0, unit='s')
        
        # Required Hardware objects
        self.fpga_hw = self.app.hardware['auger_fpga']
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']
        self.sem_hw = self.app.hardware['sem_remcon']
                
    def setup_figure(self):
        
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.ui.setLayout(self.layout)
        self.start_button= QtWidgets.QPushButton("Start")
        self.layout.addWidget(self.start_button)
        self.stop_button= QtWidgets.QPushButton("Stop")
        self.layout.addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        
#         quad_names = ['quad_'+x for x in ['X1', 'X2', 'Y1', 'Y2']]
#         
#         self.spinboxes = dict()
#         for quad_name in quad_names:
#             sb = self.spinboxes[quad_name] = QtWidgets.QDoubleSpinBox()
#             self.analyzer_hw.settings.get_lq(quad_name).connect_bidir_to_widget(sb)
#             self.layout.addWidget(sb)
            
        #self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))        
        #self.layout.addWidget(self.graph_layout)

        self.imview = pg.ImageView()
        self.layout.addWidget(self.imview)
        
        self.imview.setImage(np.random.rand(10,10))

        
        self.ui.show()
        self.ui.setWindowTitle("AugerSimplexOptimizer")
        
        """## Create window with ImageView widget
        self.graph_layout = pg.ImageView()
        self.graph_layout.show()
        self.graph_layout.setWindowTitle('Quadrupole Optimization')"""
        

    def get_point_value(self, xy):
        '''
        called by opt.brute
        '''
        self.analyzer_hw.settings['quad_X1'] = xy[0]
        self.analyzer_hw.settings['quad_Y1'] = xy[1]
        return -self.fpga_hw.get_single_value()
        
    def run(self):
        try:
                #hardware setup
            self.fpga_hw.setup_single_clock_mode(self.settings['dwell'],delay_fraction = 0.05)
            self.analyzer_hw.settings['multiplier'] = True
            print('ramping multiplier...')
            time.sleep(3.0) #wait while multiplier ramps up

                #set second quad position neutral
            self.analyzer_hw.settings['quad_X2'] = 0.
            self.analyzer_hw.settings['quad_Y2'] = 0.
            time.sleep(0.015)
            
                #initial brute force quad scan
            xy_range = ((self.qmin,self.qmax),(self.qmin,self.qmax))
            points = 10
            scan_time = self.settings['dwell'] * points**2 * 1.05
            print('initial scanning, estimated time {} sec ...'.format(scan_time))
            xy, value = opt.brute(self.get_point_value,xy_range,Ns=points,finish=None,full_output=False)
            print( 'position', xy )
            print( 'value', value)
 
        finally:
            self.fpga_hw.settings['trigger_mode'] = 'off' 
            self.analyzer_hw.settings['multiplier'] = False
        
