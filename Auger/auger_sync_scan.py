from .sem_sync_raster_measure import SemSyncRasterScan
import time
import numpy as np


class AugerSyncRasterScan(SemSyncRasterScan):
    
    name = "auger_sync_raster_scan"
    
    def scan_specific_setup(self):
        self.display_update_period = 0.1
        SemSyncRasterScan.scan_specific_setup(self)
        
        #self.ui.centralwidget.layout().addWidget(self.settings.New_UI(), 0,0)
        self.testui = self.settings.New_UI()
        self.testui.show()
        
    def pre_scan_setup(self):
        # Hardware
        self.auger_fpga_hw = self.app.hardware['auger_fpga']
        self.auger_fpga_hw.settings['trigger_mode'] = 'off'
        time.sleep(0.01)
        self.auger_fpga_hw.flush_fifo()

        self.auger_fpga_hw.settings['trigger_mode'] = 'pxi'

        # Data Arrays
        self.auger_queue = []
        self.auger_i = 0
        self.auger_total_i = 0
        self.auger_chan_pixels = np.zeros((self.Npixels, 10), dtype=np.uint32)
        self.auger_chan_map = np.zeros( self.scan_shape + (10,), dtype=np.uint32)
        if self.settings['save_h5']:
            self.auger_chan_map_h5 = self.create_h5_framed_dataset("auger_chan_map", self.auger_chan_map)
                                                                   
                                                                    
        # figure?
        
    def handle_new_data(self):
        """ Called during measurement thread wait loop"""
        SemSyncRasterScan.handle_new_data(self)
        
        new_auger_data = self.auger_fpga_hw.read_fifo()
        self.auger_queue.append(new_auger_data)
        
        #ring_buf_index_array = (i + np.arange(n, dtype=int)) % self.Npixels
        #self.auger_chan_pixels[ring_buf_index_array] = new_auger_data
        
        while len(self.auger_queue) > 0:
            # grab the next available data chunk
            #print('new_adc_data_queue' + "[===] "*len(self.new_adc_data_queue))            
            new_data = self.auger_queue.pop(0)
            i = self.auger_i
            n = new_data.shape[0]

            # grab only up to end of frame, put the rest back in the queue
            if i + n > self.Npixels:
                split_index = (self.Npixels - i )
                print("split", i, n, split_index, self.Npixels)
                self.auger_queue.append(new_data[split_index: ])
                new_data = new_data[0:split_index]
                n = new_data.shape[0]
            
            # copy data to image shaped map
            self.auger_chan_pixels[i:i+n,:] = new_data
            x = self.scan_index_array[i:i+n,:].T
            self.auger_chan_map[x[0], x[1], x[2],:] = new_data
            
            # new frame
            if self.auger_i == 0:
                frame_num = (self.auger_total_i // self.Npixels) - 1
                if self.settings['save_h5']:
                    self.extend_h5_framed_dataset(self.auger_chan_map_h5, frame_num)
                    self.auger_chan_map_h5[frame_num,:,:,:,:] = self.auger_chan_map

            if self.interrupt_measurement_called:
                break
        
            self.auger_i += n
            self.auger_total_i += n 
            self.auger_i %= self.Npixels

        print(new_auger_data.shape)

    
    def post_scan_cleanup(self):
        self.auger_fpga_hw.settings['trigger_mode'] = 'off'


    def get_display_pixels(self):
        #SemSyncRasterScan.get_display_pixels(self)
        self.display_pixels = self.auger_chan_pixels[:,0:8].sum(axis=1)
        self.display_pixels[0] = 0
        #self.display_pixels = self._pixels[:,0]
    
        
        