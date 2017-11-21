from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,\
    replace_spinbox_in_layout
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
from collections import OrderedDict, namedtuple


AvailChan = namedtuple('AvailChan', ['type_', 'index', 'phys_chan', 'chan_name', 'term'])


class CLQuadView(Measurement):
    
    name = 'cl_quad_view'
    
    def setup(self):
        
        self.scanDAQ   = self.app.hardware['sync_raster_daq']
        self.sync_scan = self.app.measurements['sync_raster_scan']

        self.ui_filename = sibling_path(__file__, 'cl_quad_measure.ui')
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
        
        
        self.update_available_channels()
        
        
        # Crosshairs
        show_crosshairs = self.settings.New('show_crosshairs', dtype=bool, initial=True)
        show_crosshairs.connect_to_widget(self.ui.show_crosshairs_checkBox)
        show_crosshairs.add_listener(self.on_crosshair_change)
        
        # Collect
        # TODO
        self.collection_chans = ['ai%i' % i for i in [0,1,2,3]] + ['ctr%i' % i for i in [0,1,2,3]] 
        
        for name in self.collection_chans:
            checkbox = getattr(self.ui, name + "_collect_checkBox")
            chan = self.available_chan_dict[name]
            checkbox.setText( "|".join(chan[2:] ) )
        
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
        if not ('description' in self.sync_scan.settings):
            self.sync_scan.settings.New('description', dtype=str, initial="")
        self.sync_scan.settings.description.connect_to_widget(
            self.ui.description_plaintTextEdit)
    
    def update_available_channels(self):
        
        self.available_chan_dict = OrderedDict()
                
        for i, phys_chan in enumerate(self.scanDAQ.settings['adc_channels']):
            self.available_chan_dict[phys_chan] = AvailChan(
                # type, index, physical_chan, channel_name, terminal
                'ai', i, phys_chan, self.scanDAQ.settings['adc_chan_names'][i], phys_chan)
        for i, phys_chan in enumerate(self.scanDAQ.settings['ctr_channels']):
            self.available_chan_dict[phys_chan] = AvailChan(
                # type, index, physical_chan, channel_name, terminal
                'ctr', i, phys_chan, self.scanDAQ.settings['ctr_chan_names'][i], self.scanDAQ.settings['ctr_chan_terms'][i])
        
        choices = [(chan.chan_name, phys_name) for phys_name, chan in self.available_chan_dict.items()]
        for disp_letter in "ABCD":
            lq = self.settings.get_lq(disp_letter + "_chan_display")
            lq.change_choice_list(choices)

        
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
        self.optimizer_plot_adc = self.graph_layout.addPlot(
            title='Analog Optimizer', colspan=2)
        self.optimizer_plot_adc.addLegend()
        self.optimizer_plot_adc.showButtons()
        self.optimizer_plot_adc.setLabel('left', text='SEM Signal', units='V')
        
        self.optimizer_plot_ctr = self.graph_layout.addPlot(
            title='Counter Optimizer', colspan=2)
        self.optimizer_plot_ctr.addLegend()
        self.optimizer_plot_ctr.showButtons()
        self.optimizer_plot_ctr.setLabel('left', text='Count Rate', units='Hz')


        
        self.hist_buffer_plot_lines = dict()

        for ii in range(0,4):
            name = 'ai%i' % ii
            self.hist_buffer_plot_lines[name] = self.optimizer_plot_adc.plot(pen=(ii,8), name=name)
            name = 'ctr%i' % ii
            self.hist_buffer_plot_lines[name] = self.optimizer_plot_ctr.plot(pen=(ii,8), name=name)


    def run(self):
        self.display_update_period = 0.050
        #self.sync_scan.start()
        self.app.hardware['sem_remcon'].read_from_hardware()
        
        if not self.sync_scan.settings['activation']:
            self.sync_scan.settings['activation'] =True
            time.sleep(0.3)
        
        self.HIST_N = 500
        
        self.hist_buffers = dict()
        self.hist_i = 0
        for name in self.collection_chans:
            self.hist_buffers[name] = np.zeros(self.HIST_N, dtype=float)

        for name in "ABCD":
            self.img_items[name].setAutoDownsample(True)
            
            # move crosshairs to center of images
            hLine, vLine = self.cross_hair_lines[name]
            vLine.setPos(self.sync_scan.settings['Nh']/2)
            hLine.setPos(self.sync_scan.settings['Nv']/2)

                
        self.display_maps = dict()
        
        for key, chan in self.available_chan_dict.items():
            if chan.type_ == 'ai':
                self.display_maps[key] = self.sync_scan.adc_map[:,:,:,chan.index]
            elif chan.type_ == 'ctr':
                self.display_maps[key] = self.sync_scan.ctr_map_Hz[:,:,:,chan.index]
                
        
        while not self.interrupt_measurement_called:
            if not self.sync_scan.is_measuring():
                self.interrupt_measurement_called = True

            time.sleep(self.display_update_period)
        #self.sync_scan.interrupt()
        self.sync_scan.settings['activation'] = False


    def update_display(self):
        
        t0 = time.time()
        
        # Update Quad Images
        for name in "ABCD":
            chan_id = self.settings[name + "_chan_display"]
            chan = self.available_chan_dict[chan_id]
            
            px_map = self.display_maps[chan_id]
            #self.hist_luts[name].setImageItem(self.img_items[name])
            self.img_items[name].setImage(px_map[0,:,:], autoDownsample=True, autoRange=False, autoLevels=False)
            #self.hist_luts[name].imageChanged(autoLevel=self.settings[name + '_autolevel'])
            self.hist_luts[name].imageChanged(autoLevel=False)
            if self.settings[name + '_autolevel']:
                self.hist_luts[name].setLevels(*np.percentile(px_map[0,:,:],(1,99)))
            
            plot = self.plot_items[name] 
            plot.setTitle("{} {}".format( chan_id, chan.chan_name))
        
        for name in self.collection_chans:
            self.hist_buffers[name][self.hist_i] = self.display_maps[name].mean()
            self.hist_buffer_plot_lines[name].setData(self.hist_buffers[name])
 
        self.hist_i += 1
        self.hist_i %= self.HIST_N
        

        #print('quad display {}'.format(time.time() -t0))
        
    def on_crosshair_change(self):
        vis = self.settings['show_crosshairs']
        
        if hasattr(self, 'cross_hair_lines'):
            for name in 'ABCD':
                hLine, vLine = self.cross_hair_lines[name]
                hLine.setVisible(vis)
                vLine.setVisible(vis)

        