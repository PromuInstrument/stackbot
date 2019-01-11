'''
Created on Dec 19, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry.base_app import BaseMicroscopeApp


class VAT_App(BaseMicroscopeApp):
    
    name="vat_app"
    
    def setup(self):
        
        from ScopeFoundryHW.ALD.VAT_throttle.vat_throttle_hw import VAT_Throttle_HW
        self.add_hardware(VAT_Throttle_HW(self))
        
if __name__ == '__main__':
    import sys
    app = VAT_App(sys.argv)
    sys.exit(app.exec_()) 