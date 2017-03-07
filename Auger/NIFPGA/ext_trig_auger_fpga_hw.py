from ScopeFoundry import HardwareComponent
from Auger.NIFPGA.ext_trig_auger_fpga import ExtTrigAugerFPGA

class AugerFPGA_HW(HardwareComponent):
    
    name = 'auger_fpga'
    
    def setup(self):
        
        self.settings.New('trigger_mode', dtype=str, initial='off', choices=('off', 'pxi', 'dio', 'int'))
        self.settings.New('overflow', dtype=bool, ro=True)
        self.settings.New('int_trig_sample_count', dtype=int, initial=0, vmin=0) # zero --> continuous
        self.settings.New('int_trig_sample_period', dtype=int, initial=25000, vmin=0, unit='cycles_25ns') # zero --> continuous

        self.NUM_CHANS = 10

    def connect(self):
        
        self.log.debug('connecting auger_fpga')
        self.ext_trig_dev = ExtTrigAugerFPGA(debug=self.settings['debug_mode'])
        
        self.fpga = self.ext_trig_dev.FPGA
        
        self.fpga.load_bitfile()
        self.fpga.reset()
        self.fpga.run()
        
        self.settings.trigger_mode.connect_to_hardware(
            read_func =self.ext_trig_dev.read_triggerMode,
            write_func=self.ext_trig_dev.write_triggerMode
            )
        
        self.settings.overflow.connect_to_hardware(
            read_func=self.ext_trig_dev.read_overflow
            )
        
        self.settings.int_trig_sample_count.connect_to_hardware(
            write_func=self.ext_trig_dev.write_sampleCount
            )

        self.settings.int_trig_sample_period.connect_to_hardware(
            write_func=self.ext_trig_dev.write_samplePeriod
            )

        #self.ext_trig_dev.write_triggerMode(self.settings['trigger_mode'])
        self.settings.trigger_mode.write_to_hardware()
        self.settings.int_trig_sample_count.write_to_hardware()
        self.settings.int_trig_sample_period.write_to_hardware()

        self.read_from_hardware()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'fpga'):
            self.ext_trig_dev.write_triggerMode('off')
            self.ext_trig_dev.flush_fifo()
            self.fpga.close()
            del self.ext_trig_dev

    
    def flush_fifo(self):
        self.ext_trig_dev.flush_fifo()
    
    def read_fifo(self, n_transfers=-1):
        """
        if n_transfers < 0: read all available transfer blocks 
        defaults to read all
        """
        if n_transfers < 0:
            n_transfers = self.ext_trig_dev.read_num_transfers_in_fifo()
            
        return self.ext_trig_dev.read_fifo_parse(n_transfers, timeout=0)
    