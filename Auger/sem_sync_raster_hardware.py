'''
Created on Feb 4, 2015

@author: Hao Wu
Rewritten 2016-07-11 ESB
Rewritten 2017-01-27 ESB

'''
from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryHW.ni_daq import NI_SyncTaskSet
except Exception as err:
    print("could not load modules needed for SemSyncRasterDAQ:", err)

import numpy as np

class SemSyncRasterDAQ(HardwareComponent):
    
    name = 'SemSyncRasterDAQ'
    
    def setup(self):
        self.display_update_period = 0.050 #seconds

        # Create logged quantities, set limits and defaults
        
        self.sample_rate = self.add_logged_quantity("sample_rate", dtype=float, 
                                                    ro=False, 
                                                    initial=2e6, 
                                                    vmin=1, 
                                                    vmax=2e6,
                                                    unit='Hz',
                                                    si=True)
        
        self.output_rate = self.add_logged_quantity("output_rate", dtype=float, 
                                                    ro=True, 
                                                    initial=5e5, 
                                                    vmin=1, 
                                                    vmax=2e6,
                                                    unit='Hz', si=True)
        
        self.samples_per_pixel = self.add_logged_quantity("samples_per_pixel", dtype=int, 
                                                    ro=False, 
                                                    initial=1, 
                                                    vmin=1, 
                                                    vmax=1e10,
                                                    unit='samples')
        
        self.continuous = self.add_logged_quantity('continuous', dtype=bool, initial=True)
        
                 
        self.output_channel_addresses= self.add_logged_quantity("output_channel_addresses",dtype=str,
                                                        ro=False,
                                                        initial='X-6363/ao0:1')
        
        self.trigger_output_term = self.add_logged_quantity('trigger_output_term', dtype=str,
                                                            ro=False,
                                                            initial="/X-6368/PXI_Trig0",
                                                            )
        
        self.input_channel_addresses= self.add_logged_quantity("input_channel_addresses",dtype=str,
                                                        ro=False,
                                                        initial='X-6363/ai1')        
        
        self.input_channel_names= self.add_logged_quantity("input_channel_names",dtype=str,
                                                        ro=False,
                                                        initial='SE')
        
        self.counter_channel_addresses= self.add_logged_quantity("counter_channel_addresses",dtype=str,
                                                        ro=False,
                                                        initial='X-6363/ctr0,X-6363/ctr1')

        self.counter_channel_names= self.add_logged_quantity("counter_channel_names",dtype=str,
                                                        ro=False,
                                                        initial='PMT,PMT2')
        
        self.counter_channel_terminals= self.add_logged_quantity("counter_channel_terminals",dtype=str,
                                                        ro=False,
                                                        initial='PFI0,PFI12')
        
        
        #self.counter_unit=self.add_logged_quantity("counter_unit",dtype=str,
        #                                                ro=False,
        #                                                initial='count',
        #                                                choices=[('count','count'),('Hz','Hz')])
        
#             #FIX implement in SemSyncRasterScan
#         self.auto_blanking=self.add_logged_quantity('auto_blanking', initial=True,
#                                                    dtype=bool,
#                                                    ro=False)
#         
        
        self.ext_clock_enable = self.add_logged_quantity("ext_clock_enable", dtype=bool, initial=False)
        self.ext_clock_source = self.add_logged_quantity("ext_clock_source", dtype=str, initial="/X-6368/PFI0")
        
        #parameters that cannot change during while connected
        self.lq_lock_on_connect = ['output_channel_addresses', 'input_channel_addresses',
                                    'counter_channel_addresses', 'counter_channel_terminals',
                                    'ext_clock_source', 'trigger_output_term']
       
        self.sample_rate.add_listener(self.compute_output_rate)
        self.samples_per_pixel.add_listener(self.compute_output_rate)
        
    def connect(self):        
        if self.debug_mode.val: self.log.debug( "connecting to {}".format(self.name))
        
        #self.remcon=self.app.hardware['sem_remcon']        
                
        # lock logged quantities during connection
        for lqname in self.lq_lock_on_connect:
            lq = self.settings.get_lq(lqname)
            lq.change_readonly(True)

        #setup tasks
        if self.settings['ext_clock_enable']:
            clock_source = self.settings['ext_clock_source']
        else:
            clock_source = "" 
        ctr_chans = self.counter_channel_addresses.val.split(',')
        self.sync_analog_io = NI_SyncTaskSet(out_chan  = self.output_channel_addresses.val,
                                   in_chan   = self.input_channel_addresses.val,
                                   ctr_chans = ctr_chans,
                                   ctr_terms = self.counter_channel_terminals.val.split(','),
                                   clock_source = clock_source,
                                   trigger_output_term = self.trigger_output_term.val,
                                   )
        
        #from sample per point and sample rate, calculate the output(scan rate)
        #self.output_rate.update_value(self.sample_rate.val/self.samples_per_pixel.val)
        
        self.adc_chan_count  = self.sync_analog_io.get_adc_chan_count()
        
        
    def disconnect(self):
        
        for lqname in self.lq_lock_on_connect:
            lq = self.settings.get_lq(lqname)
            lq.change_readonly(False)

        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()

        #disconnect hardware
        if hasattr(self, "sync_analog_io"):
            self.sync_analog_io.stop()
            self.sync_analog_io.close()
        
            # clean up hardware object
            del self.sync_analog_io


    @property
    def ctr_num(self):
        return self.sync_analog_io.ctr_num
    
    def compute_output_rate(self):
        self.output_rate.update_value(self.sample_rate.val/self.samples_per_pixel.val)
    
    def setup_io_with_data(self, X, Y):
        """
        Set up sync task with X and Y arrays sent to the analog output channels
        Compute output rate based on settings 
        """
        assert len(X) == len(Y)        
        self.num_pixels = len(X)
        self.num_samples = int(self.num_pixels *self.samples_per_pixel.val)
        self.pixel_time = self.samples_per_pixel.val / self.sample_rate.val        
        self.timeout = 1.5 * self.pixel_time * self.num_pixels             
        self.compute_output_rate()
        
        
        self.sync_analog_io.setup(rate_out = self.output_rate.val,
                                      count_out = self.num_pixels, 
                                      rate_in = self.sample_rate.val,
                                      count_in = self.num_samples, 
                                      #pad = ?,
                                      is_finite=(not self.continuous.val))
        
        self.XY = self.interleave_xy_arrays(X, Y)                
        self.sync_analog_io.write_output_data_to_buffer(self.XY)
        
    
    def interleave_xy_arrays(self, X, Y):
        """take 1D X and Y arrays to create a flat interleaved XY array
        of the form [x0, y0, x1, y1, .... xN, yN]
        """
        assert len(X) == len(Y)
        N = len(X)
        XY = np.zeros(2*N, dtype=float)
        XY[0::2] = X
        XY[1::2] = Y
        return XY       
          

    def read_ai_chan_pixels(self, n_pixels):
        # Grabs n_pixels worth of multi-channel, multi-sample 
        # data shaped as (n_pixels, n_chan, n_samp)
        # TODO: check if n_pixels worth of data are actually returned
        n_samples = int(n_pixels * self.samples_per_pixel.val)
        buf = self.sync_analog_io.read_adc_buffer(count = n_samples, timeout=self.timeout)
        #print('read_ai_chan_pixels', 'n_pixels', n_pixels, 'adc_chan_count', self.adc_chan_count, 
        #      'n_samples', n_samples, 'buf.shape', buf.shape)

        return buf.reshape(n_pixels, self.samples_per_pixel.val, self.adc_chan_count).swapaxes(1,2)
        
    
    def read_counter_buffer(self, ctr_i, count=0):
        return self.sync_analog_io.read_ctr_buffer_diff(
            ctr_i, count, self.timeout)

    def start(self):
        # TODO disable LQ's that can't be changed during task run
        self.sync_analog_io.start()
        
    def stop(self):
        # TODO re-enable LQ's that can't be changed during task run
        self.sync_analog_io.stop()
        
        
    def set_adc_n_pixel_callback(self, n_pixels, cb_func):
        """
        Setup callback functions for EveryNSamplesEvent
        *cb_func* will be called 
        after every *n_pixels* are acquired. 
        """
        n_samples = n_pixels*self.samples_per_pixel.val
        self.sync_analog_io.adc.set_n_sample_callback(n_samples, cb_func)
    
    def set_ctr_n_pixel_callback(self, ctr_i, n_pixels, cb_func):
        """
        Setup callback functions for EveryNSamplesEvent
        *cb_func* will be called 
        after every *n_pixels* are acquired. 
        """
        n_samples = n_pixels#*self.samples_per_pixel.val
        self.sync_analog_io.ctr[ctr_i].set_n_sample_callback(n_samples, cb_func)
        
        

    #def read_counters(self):
    
    # replaced by callback-based measurement 2/9/17
    # keep as as reference for single frame measurement
    """
    def single_scan_data_block(self):
        self.ai_data = self.read_ai_chans()
            #handle oversampled ADC data
        self.ai_data =\
            self.ai_data.reshape(-1,self.samples_per_pixel.val,self.adc_chan_count)
        self.ai_data = self.ai_data.mean(axis=1)
        
        self.sync_analog_io.stop()
        #self.scanDAQ.sync_analog_io.close()
        return self.ai_data

    # replaced by callback-based measurement 2/9/17
    # keep as as reference for single frame measurement
    def single_scan_regular(self, X_pos, Y_pos):
        #connect to SEM scanner module, which calculates the voltage output,
        #create detector channels and creates the scanning task

        self.setup_io_with_data(X_pos, Y_pos)
        self.sync_analog_io.start()            
        
        self.ai_data = self.read_ai_chans()
            #handle oversampled ADC data
        self.ai_data =\
            self.ai_data.reshape(-1,self.samples_per_pixel.val,self.sync_analog_io.get_adc_chan_count())
        self.ai_data = self.ai_data.mean(axis=1)
        
        self.sync_analog_io.stop()
        #self.scanDAQ.sync_analog_io.close()
        return self.ai_data
    
    def read_ai_buffer(self):
        # interleaved buffer
        return self.sync_analog_io.read_adc_buffer(timeout=self.timeout)
    
    def read_ai_chans(self):
        return self.sync_analog_io.read_adc_buffer_reshaped(timeout=self.timeout)

    """