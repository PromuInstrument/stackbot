from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.andor_spec.andor_spec_dev import AndorShamrockSpec

class AndorShamrockSpecHW(HardwareComponent):
    
    name = 'andor_spec'
    
    def setup(self):
        
        self.settings.New('dev_id', dtype=int, initial=0)
        self.settings.New('serial_num', dtype=str, ro=True)
        
        self.settings.New('center_wl',
                                dtype=float, 
                                fmt="%1.3f",
                                ro=False,
                                unit = "nm",
                                si=False,
                                vmin=-100, vmax=2000,
                                spinbox_decimals = 3,
                                reread_from_hardware_after_write = True
                                )

        self.settings.New('turret', dtype=int, ro=True)
        self.settings.New('grating_id', dtype=int, initial=1, choices=(1,2,3,4,5,6))
        self.settings.New('grating_name', dtype=str, ro=True)
        
        self.settings.New('input_flipper', dtype=str, choices=('direct', 'side'))
        self.settings.New('output_flipper', dtype=str, choices=('direct', 'side'))
        
        self.settings.New('focus_mirror', dtype=int, unit='steps')
        
        self.settings.New('slit_input_side', dtype=float, unit='um')
        #self.settings.New('slit_output_side', dtype=float, unit='um')
        
        
    def connect(self):
        S = self.settings
        
        spec = self.spec = AndorShamrockSpec(dev_id=S['dev_id'])
        
        S['serial_num'] = spec.serial_number
        S['turret'] = spec.get_turret()
        
        ## update grating list
        S.grating_id.change_choice_list(
            tuple([ ("{}: {}".format(num,name), num) 
                   for num, name in spec.gratings.items()])
            )

        S.grating_id.connect_to_hardware(
            read_func = spec.get_grating,
            write_func = spec.set_grating
            )
        
        S.grating_id.add_listener(self.on_grating_id_change)
        
        S.input_flipper.connect_to_hardware(
            read_func = lambda flipper='input': spec.get_flipper_mirror(flipper), 
            write_func = lambda port, flipper='input': spec.set_flipper_mirror(flipper, port), 
            )
        
        S.output_flipper.connect_to_hardware(
            read_func = lambda flipper='output': spec.get_flipper_mirror(flipper), 
            write_func = lambda port, flipper='output': spec.set_flipper_mirror(flipper, port), 
            )
        
        S.focus_mirror.connect_to_hardware(
            read_func = spec.get_focus_mirror_position,
            write_func = spec.set_focus_mirror_position_abs)
        
        S.slit_input_side.connect_to_hardware(
            read_func = lambda slit='input_side': spec.get_slit_width(slit),
            write_func = lambda w, slit='input_side': spec.set_slit_width(slit, w)
            )
        
        S.center_wl.connect_to_hardware(
            read_func = spec.get_wavelength,
            write_func = spec.set_wavelength)
        
        self.read_from_hardware()
        self.on_grating_id_change()
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, "spec"):
            self.spec.close()
            del self.spec
        
        
        
    def on_grating_id_change(self):
        self.settings['grating_name'] = self.spec.gratings[self.settings['grating_id']]
        self.settings.focus_mirror.read_from_hardware()