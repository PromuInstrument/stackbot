'''
Created on Feb 28, 2017

@author: Alan Buckley
'''
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.flask_web_view import flask_web_view
import logging
 
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)


class DLIApp(BaseMicroscopeApp):
    
    name="dli_app"


    def setup(self):
        """Registers :class:`HardwareComponent` object, such that the top level `DLIApp` may access its functions."""
        from ScopeFoundryHW.dli_powerswitch.dlipower_hardware import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))
        
if __name__ == '__main__':
    import sys
    app = DLIApp(sys.argv)
    app.flask_thread = flask_web_view.MicroscopeFlaskWebThread(app)
    app.flask_thread.start()
    sys.exit(app.exec_())    