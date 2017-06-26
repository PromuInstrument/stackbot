'''
Created on Feb 28, 2017

@author: Alan Buckley
'''
<<<<<<< HEAD
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.flask_web_view import flask_web_view
import logging
 
=======
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path
import logging

>>>>>>> d23eddb51984f311015483594899062df7612379
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)


class DLIApp(BaseMicroscopeApp):
    
    name="dli_app"
<<<<<<< HEAD


=======
    
>>>>>>> d23eddb51984f311015483594899062df7612379
    def setup(self):
        """Registers :class:`HardwareComponent` object, such that the top level `DLIApp` may access its functions."""
        from ScopeFoundryHW.dli_powerswitch.dlipower_hardware import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))
        
<<<<<<< HEAD
if __name__ == '__main__':
    import sys
    app = DLIApp(sys.argv)
    app.flask_thread = flask_web_view.MicroscopeFlaskWebThread(app)
    app.flask_thread.start()
    sys.exit(app.exec_())    
=======

if __name__ == '__main__':
    import sys
    app = DLIApp(sys.argv)
    sys.exit(app.exec_())    
        
>>>>>>> d23eddb51984f311015483594899062df7612379
