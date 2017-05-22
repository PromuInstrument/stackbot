from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ni_daq import NI_CounterTask


class NI_FreqCounterCallBackHW(HardwareComponent):
    
    name = 'ni_freq_counter_cb'
    
    def setup(self):
        
        self.settings.New(  name = 'count_rate', 
                            dtype=float, fmt="%e", ro=True,
                            unit="Hz")
        
        self.settings.New(  name = 'int_time',
                            initial=0.1,
                            dtype=float, si=True,
                            ro=False,
                            unit = "s",
                            vmin = 1e-6, vmax=100)
        
        self.settings.New('dev', dtype=str, initial='Dev1')
        
        self.settings.New(  'counter_chan',
                             dtype=str,
                             initial='ctr0',
                             ro=False)

        self.settings.New(  'input_terminal',
                             dtype=str,
                             initial="PFI0",
                             ro=False)
        
    def connect(self):
        S = self.settings
        
        self._ctr_chan = "{}/{}".format(S['dev'], S['counter_chan'])
        self._in_term = "/{}/{}".format(S['dev'], S['input_terminal'])
        
        C = self.counter_task = NI_CounterTask(channel=self._ctr_chan,
                                           input_terminal=self._in_term,
                                           #name=self.name
                                           )
        #C.set_rate(rate=100, finite=False,clk_source="Dev1/OnboardClock")
        
        
        self.settings.int_time.connect_to_hardware(
            write_func=self.restart_task
            )
        
        self.restart_task(S['int_time'])
        
        
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'counter_task'):
            self.counter_task.stop()
            del self.counter_task
        
        
    def counter_callback(self):
        self.current_count = self.counter_task.read_buffer(count=self.n_samples)[-1]
        self.settings['count_rate'] = (self.current_count - self.prev_count)/self._int_time
        self.prev_count = self.current_count
        #print("counter_callback")
        
    def restart_task(self, int_time):
        self._int_time = int_time
        C = self.counter_task
        self.n_samples = int(100000*int_time)
        print('restart_task', self.n_samples)
        C.stop()
        C.set_rate(rate=100000, finite=False,
               count=self.n_samples,
               clk_source="/{}/100kHzTimebase".format(self.settings['dev']))
        C.set_n_sample_callback(n_samples=self.n_samples,cb_func=self.counter_callback)
        self.prev_count = 0
        C.start()
