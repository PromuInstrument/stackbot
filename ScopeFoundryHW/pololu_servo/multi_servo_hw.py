from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.pololu_servo.pololu_interface import PololuMaestroDevice

class PololuMaestroHW(HardwareComponent):
    
    name = 'pololu_maestro'
    
    def __init__(self, app, debug=False, name=None, servo_names=None):
        self.servo_names = servo_names
        if not self.servo_names:
            self.servo_names = [(i, "ch{}".i) for i in range(6)]
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):        
        S = self.settings
        
        S.New(name='port', initial='COM1', dtype=str, ro=False)

        for servo_num, name in self.servo_names:
            raw = S.New(name + "_raw", dtype=int,  ro=False) # raw value of servo position output (in units of 1/4 us for PWM pulses)
            raw_min = S.New(name + '_raw_min', dtype=float, initial=2000, ro=False)
            raw_max = S.New(name + '_raw_max', dtype=float, initial=10000, ro=False)
            pos_scale = S.New(name + '_pos_scale', dtype=float, initial=180, ro=False)
            pos = S.New(name + '_position', dtype=float, ro=False)
        
            def pos_rev_func(new_pos, old_vals):
                raw, rmin, rmax, scale = old_vals
                new_raw = rmin + new_pos/scale*(rmax-rmin)
                return (new_raw, rmin, rmax, scale)
    
            pos.connect_lq_math( (raw, raw_min, raw_max, pos_scale),
                                        func=lambda raw, rmin, rmax, scale: scale*( (raw - rmin)/(rmax-rmin) ),
                                        reverse_func= pos_rev_func)
        
            S.New(name+'_jog_step', dtype=float, initial=10.0)
        
            self.add_operation(name + " Jog +", lambda n=name: self.jog_fwd(n))
            self.add_operation(name + " Jog -", lambda n=name: self.jog_bkwd(n))

    
    def connect(self):
        self.dev = PololuMaestroDevice(port=self.settings['port'])

        for servo_num, name in self.servo_names:

            raw = self.settings.get_lq(name+"_raw")
            raw.connect_to_hardware(
                read_func=lambda n=servo_num: self.dev.read_position(n),
                write_func=lambda pos, n=servo_num: self.dev.write_position(n,pos)
                )
        
            raw.read_from_hardware()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
    
    
    def jog_fwd(self, servo_name):
        S = self.settings
        S[servo_name+'_position'] += S[servo_name + '_jog_step']
    
    def jog_bkwd(self, servo_name):
        S = self.settings
        S[servo_name+'_position'] -= S[servo_name + '_jog_step']

