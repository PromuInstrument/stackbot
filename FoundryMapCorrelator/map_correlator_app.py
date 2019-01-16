'''
Created on May 3, 2018

@author: Benedikt Ursprung
    
Correlates a 'small map' ('sm') to a 'big map' ('bm').
Correlation assumes sm is completely embedded in bm.
Adjust the load functions for new files.  
'''

from __future__ import division, print_function, absolute_import
from ScopeFoundry import BaseApp
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
from qtpy import QtCore, QtWidgets
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import numpy as np
import scipy.ndimage as ndimage
import h5py
from kde_map_interpolation import kde_map_interpolation, bilinear_weighted_map
from ir_microscope.data.analysis import shift_time_trace_map, tau_x_calc_map
from astropy._erfa.core import DTY
from ScopeFoundry.widgets import MinMaxQSlider

class MapCorrelatorApp(BaseApp):
    
    name = "FoundryMapCorrelator"
    
    def __init__(self, argv):
        BaseApp.__init__(self, argv)
        self.setup()
    
    def setup(self):
        self.iso_level = self.settings.New('iso_level', initial=0.5)
        self.delta_x = self.settings.New('delta_h', initial=0, spinbox_decimals=7, vmin=-0.00, vmax=0.08, unit='mm')
        self.delta_y = self.settings.New('delta_v', initial=0, spinbox_decimals=7, vmin=-0.00, vmax=0.08, unit='mm')
        self.angle = self.settings.New('angle', initial = 0, spinbox_decimals=3, unit='deg', vmin=0, vmax=360)
        
        self.sm_dh = self.settings.New('sm_dh', initial = 0.015/1024, spinbox_decimals=7, unit='mm/px', )
        self.sm_dv = self.settings.New('sm_dv', initial = 0.015/1024, spinbox_decimals=7, unit='mm/px', )
        self.flip_sm_x = self.settings.New('flip_sm_x', dtype=bool, initial=False)
        self.flip_sm_y = self.settings.New('flip_sm_y', dtype=bool, initial=False)
        
        self.sm_opacity = self.settings.New('sm_opacity', dtype=float, initial=0.8, vmin=0, vmax=1)
        self.sm_blur = self.settings.New('sm_blur', dtype=float, initial=20, vmin=0, vmax=30)
        
        
        
        choices = ('integrated_count_map', 'taue_map')
        self.bm_map_name = self.settings.New('bm_map_name', dtype=str, initial = 'integrated_count_map', choices=choices) 
        

        self.delta_x.add_listener(self.update_figure)
        self.delta_y.add_listener(self.update_figure)
        self.angle.add_listener(self.update_figure)
        self.sm_dh.add_listener(self.update_figure)
        self.sm_dv.add_listener(self.update_figure)
        self.flip_sm_x.add_listener(self.filter_sm)
        self.flip_sm_y.add_listener(self.filter_sm)
        
        self.sm_opacity.add_listener(self.update_figure)
        self.sm_blur.add_listener(self.filter_sm)
        self.bm_map_name.add_listener(self.set_bm)

        #self.mask_exponent = self.settings.New('mask_exponent', dtype=float, initial=-12)
        #self.mask_exponent.add_listener(self.update_correlated_figure)

        self.gauss_sigma = self.settings.New('gauss_sigma', dtype=float, initial=0.6)
        
        # ui
        self.ui = self.dockarea = dockarea.DockArea()
        self.ui.showNormal()
        self.ui.adjustSize()
        self.ui.raise_()
        
        #settings dock
        self.settings_dock = self.dockarea.addDock(name='Settings', position='left', 
                              widget=self.settings.New_UI())
        
        # sliders and buttons
        self.settings_dock.addWidget(QtWidgets.QLabel('small image x,y,alpha,opacity'), )
        
        self.delta_x_slider = MinMaxQSlider()
        self.delta_x.connect_to_widget(self.delta_x_slider)
        self.settings_dock.addWidget(self.delta_x_slider)

        self.delta_y_slider = MinMaxQSlider()
        self.delta_y.connect_to_widget(self.delta_y_slider)
        self.settings_dock.addWidget(self.delta_y_slider,)

        self.angle_slider = MinMaxQSlider()
        self.angle.connect_to_widget(self.angle_slider)
        self.settings_dock.addWidget(self.angle_slider,  )

        self.sm_opacity_slider = MinMaxQSlider()
        self.sm_opacity.connect_to_widget(self.sm_opacity_slider)
        self.settings_dock.addWidget(self.sm_opacity_slider)
        
        self.sm_blur_slider = MinMaxQSlider()
        self.sm_blur.connect_to_widget(self.sm_blur_slider)
        self.settings_dock.addWidget(self.sm_blur_slider)
        
        self.correlate_pushBotton = QtWidgets.QPushButton()
        self.correlate_pushBotton.setText('correlate (kde interpolate sm to bm)')
        self.correlate_pushBotton.clicked.connect(self.correlate)
        self.settings_dock.addWidget(self.correlate_pushBotton)

        #self.save_pushBotton = QtWidgets.QPushButton()
        #self.save_pushBotton.setText('save settings and correlated array')
        #self.save_pushBotton.clicked.connect(self.save)
        #self.settings_dock.addWidget(self.save_pushBotton)

        
        # overlayer dock         
        self.overlayer_graph_layout=pg.GraphicsLayoutWidget()
        self.overlayer_graph_dock = self.dockarea.addDock(name='overlayer', position='right', widget=self.overlayer_graph_layout)        
        self.overlayer_plot = self.overlayer_graph_layout.addPlot(title='overlayer')
        self.overlayer_plot.setAspectLocked(lock=True, ratio=1)

        self.sm_img_item = pg.ImageItem()
        self.overlayer_plot.addItem(self.sm_img_item)
        self.sm_img_item.setZValue(2)
        self.sm_hist_lut = pg.HistogramLUTItem()
        self.sm_hist_lut.setImageItem(self.sm_img_item)
        self.overlayer_graph_layout.addItem(self.sm_hist_lut)
        #self.sm_img_item.setLookupTable(pg.colormaps.Viridis().getLookupTable())

        self.bm_img_item = pg.ImageItem()
        self.bm_img_item.setZValue(1)
        self.overlayer_plot.addItem(self.bm_img_item)
        self.bm_hist_lut = pg.HistogramLUTItem()
        self.bm_hist_lut.setImageItem(self.bm_img_item)
        self.overlayer_graph_layout.addItem(self.bm_hist_lut)

        #Note:isocurveItem is a single contour line witch requires and imageItem 
        #to align correctly.
        #self.sm_isocurve_item = pg.IsocurveItem(pen='r')
        #self.sm_isocurve_item.setParentItem(self.sm_img_item)
        #self.overlayer_plot.addItem(self.sm_isocurve_item)

        # correlator dock
        self.correlator_graph_layout=pg.GraphicsLayoutWidget()
        self.correlator_graph_dock = self.dockarea.addDock(name='correlator', position='bottom', widget=self.correlator_graph_layout)        

        self.correlator_im_plot = self.correlator_graph_layout.addPlot(title='interpolated small map')        
        self.correlator_im_plot.setAspectLocked(lock=True, ratio=1)
        
        self.sm_kde_img_item = pg.ImageItem()
        self.sm_kde_img_item.setZValue(2)
        self.correlator_im_plot.addItem(self.sm_kde_img_item)
        #self.sm_kde_img_lut = pg.HistogramLUTItem(self.sm_kde_img_item)
        #self.correlator_im_plot.addItem(self.sm_kde_img_lut)

        self.bm_img_item_ = pg.ImageItem()
        self.bm_img_item_.setZValue(1)    
        self.correlator_im_plot.addItem(self.bm_img_item_)
        #self.bm_img_item_lut = pg.HistogramLUTItem(self.bm_img_item_)
        #self.correlator_im_plot.addItem(self.bm_img_item_lut)
                      
        self.correlator_scatter_plot = pg.ScatterPlotItem()        
        self.correlator_plot = self.correlator_graph_layout.addPlot(title='correlator')
        self.correlator_plot.addItem(self.correlator_scatter_plot)
        self.correlator_plot.setLabel('left','kde small map value')
        self.correlator_plot.setLabel('bottom','big map value')
           

        #load data 
        # bm='big map', sm='small map'
        self.load_bm() 
        self.set_bm()

        self.filter_sm() #also calls load_sm()   

    def update_sm_extent(self):
        [x0_,x1_,y0_,y1_] = self.bm_imshow_extent
        sm_Nv, sm_Nh= self.sm.shape
        self.sm_width  = self.sm_dh.val*sm_Nh       
        self.sm_height = self.sm_dv.val*sm_Nv
        x0 = x0_+self.delta_x.val
        y0 = y0_+self.delta_y.val
        self.sm_extent=[x0,x0+self.sm_width,y0,y0+self.sm_height]


    def update_figure(self):
        self.update_sm_extent()
        x0, x1, y0, y1 = self.sm_extent
        #self.sm_isocurve_item.setData(self.sm_show, level=self.threshold.val)
        #self.sm_isocurve_item_rect = QtCore.QRectF(x0, y0, x1-x0, y1-y0)
        self.sm_img_item.setImage(self.sm, opacity=self.sm_opacity.val )
        self.sm_img_item_rect = QtCore.QRectF(x0, y0, x1-x0, y1-y0)
        self.sm_img_item.setRect(self.sm_img_item_rect)
        self.sm_img_item.rotate(self.angle.val)
        
        #bm
        self.bm_img_item.setImage(self.bm)
        x0, x1, y0, y1 = self.bm_imshow_extent        
        self.bm_img_item.setRect( QtCore.QRectF(x0, y0, x1-x0, y1-y0) )

            
    def load_sm(self):
        smfname   = r"G:/My Drive/PVRD_CIGS/CIGS_correlated_microscopy/overlayer/data/loc_(20,0um).png"
        smfname = r"G:\My Drive\PVRD_CIGS\CIGS_correlated_microscopy\AFM\180618/Image0014_cpd.tif"
        #smfname = r"G:\My Drive\PVRD_CIGS\CIGS_correlated_microscopy\AFM\correlation.png"
        self.sm = ndimage.imread(smfname).sum(axis=2)

    def load_bm(self):
        trplfname = r"G:/My Drive/PVRD_CIGS/CIGS_correlated_microscopy/overlayer/data/180430_204334_trpl_scan.h5"
        trplfname = r"G:/My Drive\PVRD_CIGS\data_and_analysis/20180621-5904 for correlated microscopy/1a/180621_182210_trpl_2d_scan.h5"
        trplfname = r"G:\My Drive\PVRD_CIGS\data_and_analysis\20180621-5904 for correlated microscopy\2a/180701_203132_trpl_2d_scan.h5"
        h5_file=h5py.File(trplfname)
        try:
            self.H = h5_file['measurement/trpl_scan/']
        except:
            self.H = h5_file['measurement/trpl_2d_scan/']
        self.time_array = self.H['time_array'].value
        self.time_trace_map = (self.H['time_trace_map'].value)[0]
        self.integrate_count_map = (self.H['integrated_count_map'].value)[0]
            
        self.bm_imshow_extent = self.H['imshow_extent'].value
        self.bm_dh=h5_file['app/settings'].attrs['dh']
        self.bm_dv=h5_file['app/settings'].attrs['dv']
        
        h5_file.close()  


        
    def set_bm(self):
        bm_map_name=self.bm_map_name.val
        if bm_map_name=='taue_map':
            taue_map = tau_x_calc_map(self.time_array,self.time_trace_map)
            self.bm = taue_map
            print('set bm to taue_map')

        if bm_map_name == 'integrated_count_map':
            self.bm = self.integrate_count_map             
        try:
            self.update_figure()
        except AttributeError:
            pass

    def flip_sm(self):
        self.load_sm()
        sm = self.sm
        if self.flip_sm_x.val:
            sm = np.flip(sm, axis=0)
        if self.flip_sm_y.val:
            sm = np.flip(sm, axis=1)
        self.sm = sm
        
        
    def filter_sm(self):
        self.flip_sm()
        if self.sm_blur.val!=0:
            self.sm = ndimage.filters.gaussian_filter(self.sm, self.sm_blur.val)
        self.update_figure()
        
    def correlate(self):
        print('correlation started')
        self.kde_interpolate_sm_to_bm()
        self.update_correlated_figure()
        print('correlation ended')
        
    def kde_interpolate_sm_to_bm(self):
        self.calc_new_sm_pixel_coordinates()
        self.flip_sm()
        self.sm_kde = kde_map_interpolation( shape = self.bm.shape, 
                                             x = self.sm_x.flatten(),
                                             y = self.sm_y.flatten(),
                                             z = self.sm.flatten(),
                                             sigma=self.gauss_sigma.val,
                                             r_threshold=1e-15)
        
    def calc_new_sm_pixel_coordinates(self):
        # sm adjust to bm map, pixels units will be in units of bm_dh, bm_dv
        # this requires to rescale sm pixel units and delta
        
        # generate non-rotated coordinates
        sm_scaled_unit_h = self.sm_dh.val/self.bm_dh
        sm_scaled_unit_v = self.sm_dv.val/self.bm_dv

        sm_Nv,sm_Nh= self.sm.shape        
        XX,YY = np.meshgrid(np.arange(sm_Nh)*sm_scaled_unit_h,
                            np.arange(sm_Nv)*sm_scaled_unit_v)
        
        # rotate
        alpha = self.angle.val*np.pi/180
        self.sm_x =  XX*np.cos(alpha) + YY*np.sin(alpha)
        self.sm_y = -XX*np.sin(alpha) + YY*np.cos(alpha)

        # translate
        self.sm_x += self.delta_x.val/self.bm_dh
        self.sm_y += self.delta_y.val/self.bm_dv
    
    def update_correlated_figure(self):
        self.calc_correlated_arrays()
        self.correlator_scatter_plot.setData(x=self.cor_sm_array_masked, y=self.cor_bm_array_masked)
        self.sm_kde_img_item.setImage(self.sm_kde, opacity=0.5)
        self.bm_img_item_.setImage(self.bm, opacity=0.5)
        
    def calc_correlated_arrays(self):
        mask = self.sm_kde>0#10**self.mask_exponent.val
        self.cor_sm_array_masked = self.sm_kde[mask].flatten()
        self.cor_bm_array_masked = self.bm[mask].flatten()
    
    def save_correlation(self):    
        print('not implemented')
        
        #settings
        #maps
        #cor_sm_array_masked
        #cor_bm_array_masked
            

if __name__ == '__main__':
    import sys
    
    app = MapCorrelatorApp(sys.argv)
    
    sys.exit(app.exec_())