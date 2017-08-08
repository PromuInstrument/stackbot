from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='DEBUG')#, filename='m3_log.txt')
#logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)


class IRMicroscopeApp(BaseMicroscopeApp):

    name = 'ir_microscope'
    
    def setup(self):
        
        #self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'trpl_quick_access.ui')))
        
        print("Adding Hardware Components")
        import ScopeFoundryHW.picoharp as ph
        self.add_hardware(ph.PicoHarpHW(self))

        self.add_measurement(ph.PicoHarpChannelOptimizer(self))
        self.add_measurement(ph.PicoHarpHistogramMeasure(self))
        

        ##########
        self.settings_load_ini('trpl_defaults.ini')

if __name__ == '__main__':
    import sys
    app = IRMicroscopeApp(sys.argv)
    sys.exit(app.exec_())