from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,\
    replace_spinbox_in_layout
import pyqtgraph as pg
import numpy as np
import time
from collections import OrderedDict, namedtuple


class HyperSpecCLQuadView(Measurement):
    
    name = 'hyperspec_cl_quad_view'

    def setup(self):
        
        self.scanDAQ   = self.app.hardware['sync_raster_daq']
        self.sync_scan = self.hyperspec_scan = self.app.measurements['hyperspec_cl']

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
        
        # Display channels and autolevel
        for disp_letter in "ABCD":
            lq_name = disp_letter+'_autolevel'
            lq = self.settings.New(lq_name, dtype=bool, initial=True)
            lq.connect_to_widget(
                getattr(self.ui, disp_letter + "_autolevel_checkBox"))
            
            lq = self.settings.New(disp_letter + "_chan_display", dtype=str, initial='ai0', choices = ('ai0',))
            
            lq.connect_to_widget(
                getattr(self.ui, disp_letter + "_chan_comboBox"))
        
        
        
        self.scanDAQ.channels_changed.connect(self.update_available_channels)

        self.update_available_channels()
        
        
        # Crosshairs
        show_crosshairs = self.settings.New('show_crosshairs', dtype=bool, initial=True)
        show_crosshairs.connect_to_widget(self.ui.show_crosshairs_checkBox)
        show_crosshairs.add_listener(self.on_crosshair_change)
        
        # Collect
        # TODO
        self.collection_chans = ['ai%i' % i for i in [0,1,2,3]] + ['ctr%i' % i for i in [0,1,2,3]] 
        
        #for name in self.collection_chans:
        #    checkbox = getattr(self.ui, name + "_collect_checkBox")
        #    chan = self.available_chan_dict[name]
        #    checkbox.setText( "|".join(chan[2:] ) )
        
        # Scan settings
        self.settings.New('n_pixels', dtype=int, vmin=1, initial=512)
        self.settings.n_pixels.connect_to_widget(self.ui.n_pixels_doubleSpinBox)
        def on_new_n_pixels():
            self.sync_scan.settings['Nh'] = self.settings['n_pixels']
            self.sync_scan.settings['Nv'] = self.settings['n_pixels']
        self.settings.n_pixels.add_listener(on_new_n_pixels)
        
        self.sync_scan.settings.adc_oversample.connect_to_widget(
            self.ui.adc_oversample_doubleSpinBox)
        
        self.ui.adc_rate_pgSpinBox = \
            replace_spinbox_in_layout(self.ui.adc_rate_doubleSpinBox)
        self.sync_scan.settings.adc_rate.connect_to_widget(
            self.ui.adc_rate_pgSpinBox)
        
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

    def update_available_channels(self):
        self.sync_scan.update_available_channels()
        
        for disp_letter in "ABCD":
            print(disp_letter)
            lq = self.settings.get_lq(disp_letter + "_chan_display")
            lq.change_choice_list(tuple(self.sync_scan.available_chan_dict.keys()))
        
    def setup_figure(self):
        
        
        self.plot_items = dict()
        self.img_items = dict()
        self.hist_luts = dict()
        self.display_image_maps = dict()
        self.cross_hair_lines = dict()
        
        for ii, name in enumerate("ABCD"):
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
        
        # linear region for band pass selection        
        self.bp_region = pg.LinearRegionItem()
        self.bp_region.setZValue(10)
        self.spectrum_plot.addItem(self.bp_region, ignoreBounds=False)
        self.bp_region.setRegion([0,1600])

        #self.bp_region.sigRegionChanged.connect(self.update_bp_region)

        plot = self.bp_img_plot = self.graph_layout.addPlot(
            title="Band Pass Image", colspan=1)

        self.bp_img_item = pg.ImageItem()
        self.bp_img_item.setOpts(axisOrder='row-major')
        self.bp_img_item .setAutoDownsample(True)
        plot.addItem(self.bp_img_item )
        plot.showGrid(x=True, y=True)
        plot.setAspectLocked(lock=True, ratio=1)
        self.hist_lut_bp = pg.HistogramLUTItem()
        self.hist_lut_bp .setImageItem(self.bp_img_item)
        self.graph_layout.addItem(self.hist_lut_bp )


    #def update_bp_region(self):
    #    self.reg = self.bp_region.getRegion()
        

    def run(self):
        self.display_update_period = 0.050
        #self.sync_scan.start()
        if not self.sync_scan.settings['activation']:
            self.sync_scan.settings['activation'] =True
            time.sleep(0.3)

        for name in "ABCD":
            self.img_items[name].setAutoDownsample(True)
            
            # move crosshairs to center of images
            hLine, vLine = self.cross_hair_lines[name]
            vLine.setPos(self.sync_scan.settings['Nh']/2)
            hLine.setPos(self.sync_scan.settings['Nv']/2)

                
                
    
        while not self.interrupt_measurement_called:
            if not self.sync_scan.is_measuring():
                self.interrupt_measurement_called = True

            time.sleep(self.display_update_period)
        #self.sync_scan.interrupt()
        self.sync_scan.settings['activation'] = False


    def update_display(self):
        
        t0 = time.time()
        
        self.display_maps = dict()
        
        for key, chan in self.sync_scan.available_chan_dict.items():
            if chan.type_ == 'ai':
                self.display_maps[key] = self.sync_scan.adc_map[:,:,:,chan.index]
            elif chan.type_ == 'ctr':
                self.display_maps[key] = self.sync_scan.ctr_map_Hz[:,:,:,chan.index]

        
        # Update Quad Images
        for name in "ABCD":
            
            chan_id = self.settings[name + "_chan_display"]
            chan = self.sync_scan.available_chan_dict[chan_id]
            
            px_map = self.display_maps[chan_id]
            #self.hist_luts[name].setImageItem(self.img_items[name])
            self.img_items[name].setImage(px_map[0,:,:], autoDownsample=True, autoRange=False, autoLevels=False)
            #self.hist_luts[name].imageChanged(autoLevel=self.settings[name + '_autolevel'])
            self.hist_luts[name].imageChanged(autoLevel=False)
            if self.settings[name + '_autolevel']:
                im = px_map[0,:,:]
                non_zero_mask = im!=0
                if np.any(non_zero_mask):
                    self.hist_luts[name].setLevels(*np.percentile(im[non_zero_mask],(1,99)))
            
            plot = self.plot_items[name] 
            plot.setTitle("{} {}".format( chan_id, chan.chan_name))

            
        # Update Spectrum
        M = self.hyperspec_scan
        self.current_spec_plotline.setData(M.wls,
            M.spec_buffer[M.andor_ccd_pixel_i-1])
        
        
        try:
            wl0, wl1 = self.bp_region.getRegion()
            kk0 = M.wls.searchsorted(wl0)
            kk1 = M.wls.searchsorted(wl1)
            #kk0, kk1 = self.bp_region.getRegion()
            bp_img = M.spec_map[0,:,:, int(kk0):int(kk1)].sum(axis=2)
            self.bp_img_item.setImage(bp_img, autoDownsample=True, autoRange=False, autoLevels=False)
            self.hist_lut_bp.imageChanged(autoLevel=False)
            self.hist_lut_bp.setLevels(*np.percentile(bp_img[bp_img!=0],(1,99)))
        except:
            pass
        #print('quad display {}'.format(time.time() -t0))
        
    def on_crosshair_change(self):
        vis = self.settings['show_crosshairs']
        
        if hasattr(self, 'cross_hair_lines'):
            for name in 'ABCD':
                hLine, vLine = self.cross_hair_lines[name]
                hLine.setVisible(vis)
                vLine.setVisible(vis)

        