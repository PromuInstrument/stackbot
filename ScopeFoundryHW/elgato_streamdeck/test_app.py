'''
Created on Mar 27, 2018

@author: esbarnard
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.elgato_streamdeck.elgato_streamdeck_hw import ElgatoStreamDeckHW
import numpy as np

class StreamDeckTestApp(BaseMicroscopeApp):
    
    name = 'streamdeck_testapp'
    
    def setup(self):
        
        from ScopeFoundryHW.random_gen.rand_gen_hw import RandomNumberGenHW
        random_gen = self.add_hardware(RandomNumberGenHW(self))

        from ScopeFoundryHW.random_gen.sine_wave_measure import SineWaveOptimizerMeasure
        self.sine_measure = self.add_measurement_component(SineWaveOptimizerMeasure(self))
        

        
        hw = self.add_hardware(ElgatoStreamDeckHW(self))
        
        hw.settings['connected'] = True
        
        
        key_image_format = hw.deck.key_image_format()
    
        width, height = (key_image_format['width'], key_image_format['height'])
        depth = key_image_format['depth']

        grid_x, grid_y = np.mgrid[0:1:width*1j, 0:1:height*1j]
        img = np.ones((height, width, depth), dtype=int)
        print(img.shape)
        img[:,:,0] = 255
        #img[1,:,:] = 255
        
        hw.deck.set_key_image(0, img.flat)
        
        hw.connect_key_to_lq_toggle(1, hw.settings.debug_mode, text="Toggle")
        hw.connect_key_to_lq_momentary(2, hw.settings.debug_mode, text="Momentary")
        
        def inc_brightness():
            hw.settings['brightness'] += 5
        hw.add_key_press_listener(3, inc_brightness)
        hw.set_key_image(3, hw.img_icon("plus", text='brightness'))

        def dec_brightness():
            hw.settings['brightness'] -= 5
        hw.add_key_press_listener(4, dec_brightness)
        hw.set_key_image(4, hw.img_icon("minus", text='brightness'))
        
        hw.set_key_image(6, hw.img_icon("arrow-circle-left", text="icon test") )
        hw.set_key_image(5, hw.img_icon("arrow-circle-right", text=" MOOSE", bgcolor='yellow' ))      
        
        
        def on_sine_data():
            val = random_gen.settings['sine_data']
            hw.set_key_image(7, hw.img_icon("power-standby", bgcolor='purple', text="SINE={:+1.2f}".format(val)))
        random_gen.settings.sine_data.add_listener(on_sine_data)
          
        
if __name__ == '__main__':
    
    import sys
    
    app = StreamDeckTestApp(sys.argv)
    
    app.exec_()