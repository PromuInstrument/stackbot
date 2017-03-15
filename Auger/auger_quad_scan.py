'''Ed Barnard and Frank Ogletree 14 Mar 2017'''

from __future__ import division
import pyqtgraph as pg
import numpy as np
from qtpy import QtWidgets
import time

from ScopeFoundry import Measurement, h5_io
from ScopeFoundry.scanning import BaseRaster2DScan
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
from ScopeFoundry.scanning.base_raster_scan import BaseRaster2DSlowScan


          
class AugerQuadSlowScan(BaseRaster2DSlowScan):
    
    name = "auger_quad_slowscan"
    
    def scan_specific_setup(self):
        
        #auger analyzer
        self.settings.New('ke_start', dtype=float, initial=30,unit = 'V',vmin=0,vmax = 2200)
        self.settings.New('ke_end',   dtype=float, initial=600,unit = 'V',vmin=1,vmax = 2200)
        self.settings.New('ke_delta', dtype=float, initial=0.5,unit = 'V',vmin=0.02979,vmax = 2200,si=True)
        self.settings.New('dwell', dtype=float, initial=0.05,unit = 's', si=True,vmin=1e-4)
        self.settings.New('pass_energy', dtype=float, initial=50,unit = 'V', vmin=5,vmax=500)
        self.settings.New('crr_ratio', dtype=float, initial=5, vmin=1.5,vmax=20)
        self.settings.New('CAE_mode', dtype=bool, initial=False)
       
        self.display_update_period = 0.01 


        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']
        #self.analyzer = self.analyzer_hw.analyzer
        NUM_CHANS = self.auger_fpga_hw.NUM_CHANS
        
        #raster scan setup
        #self.h_unit = self.v_unit = "%"
        self.set_h_limits(-50,50, set_scan_to_max=True)
        self.set_v_limits(-50,50, set_scan_to_max=True)
        
        
        
    
        
    # begining of run
    def pre_scan_setup(self):
        print("pre_scan_setup")

        #### Reset FPGA
        self.auger_fpga_hw.settings['int_trig_sample_count'] = 0 
        self.auger_fpga_hw.settings['trigger_mode'] = 'off' 
        time.sleep(0.01)
        self.auger_fpga_hw.flush_fifo()
        
        #### setup analyzer
        self.analyzer_hw.settings['multiplier'] = True
        self.analyzer_hw.settings['CAE_mode'] = self.settings['CAE_mode']
        self.analyzer_hw.settings['KE'] = self.settings['ke_start']
        self.analyzer_hw.settings['pass_energy'] = self.settings['pass_energy']
        self.analyzer_hw.settings['crr_ratio'] = self.settings['crr_ratio']
        time.sleep(3.0)
        
        self.sample_block = 21
        self.timeout = 2.0 * self.settings['dwell']
        print("pre_scan_setup2")

        self.auger_fpga_hw.settings['period'] =self.settings['dwell']/(self.sample_block - 1)
        self.auger_fpga_hw.settings['trigger_mode'] = 'int'
        print("pre_scan_setup")


    def move_position_start(self, x,y):        
        self.move_position_slow(x, y, 0,0)
        self.analyzer_hw.settings['quad_X1'] = x
        self.analyzer_hw.settings['quad_Y1'] = y
    
    def move_position_slow(self, x,y, dx, dy):
        self.analyzer_hw.settings['quad_X1'] = x
        self.analyzer_hw.settings['quad_Y1'] = y
        
    def move_position_fast(self, x,y, dx, dy):
        self.analyzer_hw.analyzer.write_quad('X1',x)
        self.analyzer_hw.analyzer.write_quad('Y1',y)
        #self.move_position_slow(x, y, dx, dy)
        

    def collect_pixel(self, pixel_num, k, j, i):
        # collect data
        if pixel_num == 0:
            self.auger_fpga_hw.flush_fifo()
        remaining, buf_reshaped = self.auger_fpga_hw.read_fifo(n_transfers = self.sample_block,timeout = self.timeout, return_remaining=True)                
        if remaining > 0:
            print( "collect pixel {} samples remaining at pixel {}, resyncing".format( remaining, pixel_num))
            self.auger_fpga_hw.flush_fifo()
            remaining, buf_reshaped = self.auger_fpga_hw.read_fifo(n_transfers = self.sample_block,timeout = self.timeout, return_remaining=True)                
            print( "collect pixel {} samples remaining after resync, resyncing".format( remaining))

        buf_reshaped = buf_reshaped[1:] #discard first sample, transient
        data = np.sum(buf_reshaped,axis=0)
        value = np.sum(data[0:6])
        #print(self.ke[0,self.index], data, remaining)                   
        
        # store in arrays
        self.display_image_map[k,j,i] = value
        if pixel_num == 0:
            self.p_min = self.p_max = value
        else:
            self.p_min = min( value, self.p_min)
            self.p_max = max( value, self.p_max)               
        #print(self.name, "collect_pixel", pixel_num, k,j,i, value)
        
    def update_LUT(self):
        self.hist_lut.imageChanged(autoLevel=False)
        self.hist_lut.setLevels(self.p_min, self.p_max)
        
    def post_scan_cleanup(self):
        self.analyzer_hw.settings['multiplier'] = False
        
        A = self.display_image_map
        k,j,i = np.unravel_index(A.argmax(), A.shape)
        
        print("found quad opt peak at ", k,j,i, A[k,j,i], self.h_array[i], self.v_array[j])
        
        self.analyzer_hw.settings['quad_X1'] = self.h_array[i] 
        self.analyzer_hw.settings['quad_Y1'] = self.v_array[j]         