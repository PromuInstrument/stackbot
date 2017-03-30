'''Ed Barnard and Frank Ogletree 14 Mar 2017'''

from __future__ import division
import pyqtgraph as pg
import numpy as np
from scipy import ndimage
from qtpy import QtWidgets
import time

from ScopeFoundry import Measurement, h5_io
from ScopeFoundry.scanning import BaseRaster2DScan
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
from ScopeFoundry.scanning import BaseRaster2DFrameSlowScan
          
class AugerQuadSlowScan(BaseRaster2DFrameSlowScan):
    
    name = "auger_quad_slowscan"
    
    ''' FIX
    modified quad scan to do gun align scan, works but slow, 
    also should detect inlens signal, not auger, which gives odd effects
    probably should duplicate measurement...
    
    Also could use mouse pointer to control stig etc, !
    '''
    q1 = {'x_slow':'quad_X1', 'x_fast':'X1','y_slow':'quad_Y1', 'y_fast':'Y1'}
    q2 = {'x_slow':'quad_X2', 'x_fast':'X2','y_slow':'quad_Y2', 'y_fast':'Y2'}
    xx = {'x_slow':'quad_X1', 'x_fast':'X1','y_slow':'quad_X2', 'y_fast':'X2'}
    yy = {'x_slow':'quad_Y1', 'x_fast':'Y1','y_slow':'quad_Y2', 'y_fast':'Y2'}
    scan_mode = [q1,q2,xx,yy]

    
    def scan_specific_setup(self):
        self.settings.continuous_scan.update_value(False)
        self.settings.continuous_scan.change_readonly(True)
        self.settings.n_frames.change_readonly(True)
        
        self.settings.New('quad_scan_mode', dtype=int, initial = 0, vmin = 0, vmax = 4, 
                          choices=(('quad 1',0),('quad 2',1),('x shift/angle',2),('y shift/angle',3),('SEM gun',4)))

        #auger analyzer
        self.settings.New('ke_start', dtype=float, initial=30,unit = 'V',vmin=0,vmax = 2200)
        self.settings.New('ke_end',   dtype=float, initial=600,unit = 'V',vmin=1,vmax = 2200)
        self.settings.New('ke_steps', dtype=int, initial=10,vmin=1)
        self.settings.New('dwell', dtype=float, initial=0.05,unit = 's', si=True,vmin=1e-4)
        self.settings.New('pass_energy', dtype=float, initial=50,unit = 'V', vmin=5,vmax=500)
        self.settings.New('crr_ratio', dtype=float, initial=5, vmin=1.5,vmax=20)
        self.settings.New('CAE_mode', dtype=bool, initial=False)
       
        for lqname in ['ke_start', 'ke_end', 'ke_steps', 'dwell']:
            self.settings.get_lq(lqname).add_listener(self.compute_times)
        
        self.display_update_period = 0.01 

        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        self.analyzer_hw = self.app.hardware['auger_electron_analyzer']
        self.sem_hw = self.app.hardware['sem_remcon']
         
        #raster scan setup
        #self.h_unit = self.v_unit = "%"
        self.set_h_limits(-100,100, set_scan_to_max=True)
        self.set_v_limits(-100,100, set_scan_to_max=True)
        
        
    # begining of run
    def pre_scan_setup(self):
        print("pre_scan_setup auger_quad")

#         #### Reset FPGA
        self.auger_fpga_hw.setup_single_clock_mode(self.settings['dwell'], delay_fraction = 0.05)
        
        #### setup analyzer
        self.analyzer_hw.settings['multiplier'] = True
        self.analyzer_hw.settings['CAE_mode'] = self.settings['CAE_mode']
        self.analyzer_hw.settings['KE'] = self.settings['ke_start']
        self.analyzer_hw.settings['pass_energy'] = self.settings['pass_energy']
        self.analyzer_hw.settings['crr_ratio'] = self.settings['crr_ratio']
        time.sleep(3.0)
        print("pre_scan_setup done auger_quad")
        
        S = self.settings
        self.ke_array = np.linspace(S['ke_start'], S['ke_end'], S['ke_steps'])
        S['n_frames'] = len(self.ke_array)
        
        self.quad_count_map = np.zeros(self.scan_shape, dtype=float)
        
        if S['save_h5']:
            self.h5_meas_group['ke_array'] = self.ke_array
            self.quad_count_map_h5 = self.create_h5_framed_dataset("quad_count_map", self.quad_count_map, dtype=float)
            self.quad_max_vs_ke_h5 = self.h5_meas_group.create_dataset("quad_max_vs_ke", shape=(S['n_frames'], 3)) # x%, y%, Hz
            

    def move_position_start(self, x,y):       
        qmode = self.settings['quad_scan_mode']
        if qmode == 4:
            self.sem_hw.settings['gun_xy'] = (x,y)
        else:
            XX = self.scan_mode[qmode]['x_slow']
            YY = self.scan_mode[qmode]['y_slow']
            self.analyzer_hw.settings[XX] = x
            self.analyzer_hw.settings[YY] = y

        time.sleep(0.2)
    
    def move_position_slow(self, x,y, dx, dy):
        qmode = self.settings['quad_scan_mode']
        if qmode == 4:
            self.sem_hw.settings['gun_xy'] = (x,y)
        else:
            XX = self.scan_mode[qmode]['x_slow']
            YY = self.scan_mode[qmode]['y_slow']
            self.analyzer_hw.settings[XX] = x
            self.analyzer_hw.settings[YY] = y
        
    def move_position_fast(self, x,y, dx, dy):
        qmode = self.settings['quad_scan_mode']
        if qmode == 4:
            self.sem_hw.settings['gun_xy'] = (x,y)
        else:
            XX = self.scan_mode[qmode]['x_fast']
            YY = self.scan_mode[qmode]['y_fast']
            self.analyzer_hw.analyzer.write_quad(XX,x)
            self.analyzer_hw.analyzer.write_quad(YY,y)
            #self.move_position_slow(x, y, dx, dy)
        
    def on_new_frame(self, frame_i):
        print("New frame", frame_i)
        # set ke
        self.analyzer_hw.settings['KE'] = self.ke_array[frame_i]
        print ("New frame", frame_i, self.analyzer_hw.settings['KE'], self.ke_array)
        # wait
        time.sleep(0.1)
        
    def on_end_frame(self, frame_i):
        #filter image before finding max
        A = self.quad_count_map
        B = ndimage.gaussian_filter(A[0,:,:], sigma=2)
        self.p_max = np.amax(B)
        self.p_min = np.amin(B)
        self.display_image_map[0,:,:] = B
        j,i = np.unravel_index(B.argmax(), B.shape)
        k = 0
         
        print("found quad opt peak at ", k,j,i, A[k,j,i], self.h_array[i], self.v_array[j])
        #self.move_position_slow(self.h_array[i],self.v_array[j],0,0)
        if self.settings['save_h5']:
            self.quad_count_map_h5[frame_i,:,:] = A
            self.quad_max_vs_ke_h5[frame_i,:] = self.h_array[i],self.v_array[j], A[k,j,i]
    
        self.current_stage_pos_arrow.setPos(self.h_array[i], self.v_array[j] )
        

    def collect_pixel(self, pixel_num, frame_i, k, j, i):
        # collect data
        value = self.auger_fpga_hw.get_single_value(pixel_num==0)
        self.display_image_map[k,j,i] = value
        self.quad_count_map[k,j,i] = value
        if pixel_num == 0:
            self.p_min = self.p_max = value
        else:
            self.p_min = min( value, self.p_min)
            self.p_max = max( value, self.p_max)               
        #print(self.name, "collect_pixel", pixel_num, k,j,i, value)
        
    def update_LUT(self):
        self.hist_lut.imageChanged(autoLevel=False)
        if hasattr(self, 'p_min'):
            self.hist_lut.setLevels(self.p_min, self.p_max)
        
    def post_scan_cleanup(self):
        self.analyzer_hw.settings['multiplier'] = False
        

   