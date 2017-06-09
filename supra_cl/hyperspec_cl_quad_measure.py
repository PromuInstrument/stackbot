from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,\
    replace_spinbox_in_layout
import pyqtgraph as pg
import numpy as np
import time


class HyperSpecCLQuadView(Measurement):
    
    name = 'hyperspec_cl_quad_view'

    def setup(self):
        
        self.scanDAQ   = self.app.hardware['sync_raster_daq']
        #self.sync_scan = self.app.measurements['sync_raster_scan'] 
        self.sync_scan = self.hyperspec_scan = self.app.measurements['hyperspec_cl']

        self.names = ['ai0', 'ctr0', 'ai1', 'ctr1']


        
        self.ui_filename = sibling_path(__file__, 'hyperspec_cl_quad_measure.ui')
        self.ui = load_qt_ui_file(self.ui_filename)
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_widget.layout().addWidget(self.graph_layout)
        
        
        #### Control Widgets
        #self.settings.activation.connect_to_widget(self.ui.activation_checkBox)
        self.ui.start_pushButton.clicked.connect(
            self.start)
        self.ui.interrupt_pushButton.clicked.connect(
            self.interrupt)
        
        # Auto level
        for name in self.names:
            lq_name = name+'_autolevel'
            self.settings.New(lq_name, dtype=bool, initial=True)
            self.settings.get_lq(lq_name).connect_to_widget(
                getattr(self.ui, lq_name + "_checkBox"))

        self.settings.New('show_crosshairs', dtype=bool, initial=True)
        self.settings.show_crosshairs.connect_to_widget(self.ui.show_crosshairs_checkBox)
        self.settings.show_crosshairs.add_listener(self.on_crosshair_change)
        
        # Collect
        # TODO
        
        
        # Scan settings
        self.settings.New('n_pixels', dtype=int, vmin=1, initial=512)
        self.settings.n_pixels.connect_to_widget(self.ui.n_pixels_doubleSpinBox)
        def on_new_n_pixels():
            self.sync_scan.settings['Nh'] = self.settings['n_pixels']
            self.sync_scan.settings['Nv'] = self.settings['n_pixels']
        self.settings.n_pixels.add_listener(on_new_n_pixels)
        
        self.sync_scan.settings.adc_oversample.connect_to_widget(
            self.ui.adc_oversample_doubleSpinBox)
        
        self.ui.pixel_time_pgSpinBox = \
            replace_spinbox_in_layout(self.ui.pixel_time_doubleSpinBox)
        self.sync_scan.settings.pixel_time.connect_to_widget(
            self.ui.pixel_time_pgSpinBox)
        
        self.ui.line_time_pgSpinBox = \
            replace_spinbox_in_layout(self.ui.line_time_doubleSpinBox)
        self.sync_scan.settings.line_time.connect_to_widget(
            self.ui.line_time_pgSpinBox)
        
        self.ui.frame_time_pgSpinBox = \
            replace_spinbox_in_layout(self.ui.frame_time_doubleSpinBox)
        self.sync_scan.settings.frame_time.connect_to_widget(
            self.ui.frame_time_pgSpinBox)
        

        # Data
        self.sync_scan.settings.continuous_scan.connect_to_widget(
            self.ui.continuous_scan_checkBox)
        self.sync_scan.settings.save_h5.connect_to_widget(
            self.ui.save_h5_checkBox)
        self.sync_scan.settings.n_frames.connect_to_widget(
            self.ui.n_frames_doubleSpinBox)
        
        # Description
        self.sync_scan.settings.New('description', dtype=str, initial="")
        self.sync_scan.settings.description.connect_to_widget(
            self.ui.description_plaintTextEdit)
        
        # Spectrometer settings
        self.app.hardware['andor_ccd'].settings.em_gain.connect_to_widget(
            self.ui.andor_emgain_doubleSpinBox)
        spec = self.app.hardware['acton_spectrometer']
        spec.settings.center_wl.connect_to_widget(
            self.ui.spec_center_wl_doubleSpinBox)
        spec.settings.entrance_slit.connect_to_widget(
            self.ui.spec_ent_slit_doubleSpinBox)
        spec.settings.grating_id.connect_to_widget(
            self.ui.spec_grating_id_comboBox)

        
    def setup_figure(self):
        
        
        self.plot_items = dict()
        self.img_items = dict()
        self.hist_luts = dict()
        self.display_image_maps = dict()
        self.cross_hair_lines = dict()
        
        for ii, name in enumerate(self.names):
            if (ii % 2)-1:
                self.graph_layout.nextRow()
            plot = self.plot_items[name] = self.graph_layout.addPlot(title=name)
            img_item = self.img_items[name] = pg.ImageItem()
            img_item.setOpts(axisOrder='row-major')
            img_item.setAutoDownsample(True)
            plot.addItem(img_item)
            plot.showGrid(x=True, y=True)
            plot.setAspectLocked(lock=True, ratio=1)


            vLine = pg.InfiniteLine(angle=90, movable=False)
            hLine = pg.InfiniteLine(angle=0, movable=False)
            

            self.cross_hair_lines[name] = hLine, vLine
            plot.addItem(vLine, ignoreBounds=True)
            plot.addItem(hLine, ignoreBounds=True)

            hist_lut = self.hist_luts[name] = pg.HistogramLUTItem()
            hist_lut.setImageItem(img_item)
            self.graph_layout.addItem(hist_lut)

        self.graph_layout.nextRow() 
        
        self.spectrum_plot = self.graph_layout.addPlot(
            title="Spectrum", colspan=2)
        self.spectrum_plot.addLegend()
        self.spectrum_plot.showButtons()
        self.spectrum_plot.setLabel('bottom', text='wavelength', units='nm')
        self.current_spec_plotline = self.spectrum_plot.plot()
        #self.roi_spec_plotline = self.spectrum_plot.plot()

        self.bp_img_plot = self.graph_layout.addPlot(
            title="Band Pass Image", colspan=2)

        self.bp_img_item = pg.ImageItem()
        self.bp_img_item.setOpts(axisOrder='row-major')
        self.bp_img_item .setAutoDownsample(True)
        plot.addItem(self.bp_img_item )
        plot.showGrid(x=True, y=True)
        plot.setAspectLocked(lock=True, ratio=1)


        

    def run(self):
        self.display_update_period = 0.050
        #self.sync_scan.start()
        if not self.sync_scan.settings['activation']:
            self.sync_scan.settings['activation'] =True
            time.sleep(0.3)

        for name in self.names:
            self.img_items[name].setAutoDownsample(True)
            
            # move crosshairs to center of images
            hLine, vLine = self.cross_hair_lines[name]
            vLine.setPos(self.sync_scan.settings['Nh']/2)
            hLine.setPos(self.sync_scan.settings['Nv']/2)

        
        self.display_maps = dict(
            ai0=self.sync_scan.adc_map[:,:,:,0], # numpy views of data
            ctr0=self.sync_scan.ctr_map_Hz[:,:,:,0],
            ctr1=self.sync_scan.ctr_map_Hz[:,:,:,1],
            )
        
        if self.sync_scan.scanDAQ.adc_chan_count > 1:
            self.display_maps['ai1']=self.sync_scan.adc_map[:,:,:,1]
        else:
            self.display_maps['ai1']=np.zeros((1,10,10))
        
        while not self.interrupt_measurement_called:
            if not self.sync_scan.is_measuring():
                self.interrupt_measurement_called = True


            time.sleep(self.display_update_period)
        #self.sync_scan.interrupt()
        self.sync_scan.settings['activation'] = False


    def update_display(self):
        
        t0 = time.time()
        
        # Update Quad Images
        for name, px_map in self.display_maps.items():
            #self.hist_luts[name].setImageItem(self.img_items[name])
            self.img_items[name].setImage(px_map[0,:,:], autoDownsample=True, autoRange=False, autoLevels=False)
            #self.hist_luts[name].imageChanged(autoLevel=self.settings[name + '_autolevel'])
            self.hist_luts[name].imageChanged(autoLevel=False)
            if self.settings[name + '_autolevel']:
                self.hist_luts[name].setLevels(*np.percentile(px_map[0,:,:],(1,99)))
            
        # Update Spectrum
        # need wavelength
        M = self.hyperspec_scan
        self.current_spec_plotline.setData(
            M.spec_buffer[M.andor_ccd_pixel_i-1])

        #print('quad display {}'.format(time.time() -t0))
        
    def on_crosshair_change(self):
        vis = self.settings['show_crosshairs']
        
        if hasattr(self, 'cross_hair_lines'):
            for name in self.names:
                hLine, vLine = self.cross_hair_lines[name]
                hLine.setVisible(vis)
                vLine.setVisible(vis)
