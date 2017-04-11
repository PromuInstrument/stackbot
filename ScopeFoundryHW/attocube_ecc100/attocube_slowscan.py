from __future__ import division, print_function
import numpy as np
from ScopeFoundry.scanning import BaseRaster2DSlowScan
from ScopeFoundry import Measurement, LQRange
import time

class AttoCube2DSlowScan(BaseRaster2DSlowScan):
    
    name = "AttoCube2DSlowScan"
    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app, h_limits=(-10e3,10e3), v_limits=(-10e3,10e3), h_unit="um", v_unit="um")        
    
    def setup(self):
        BaseRaster2DSlowScan.setup(self)
        #Hardware
        self.stage = self.app.hardware['attocube_xyz_stage']
        self.target_range = 0.050 # um
        self.slow_move_timeout = 1.0 # sec

    def move_position_start(self, x,y):
        self.move_position_slow(x,y, 0, 0)
    
    def move_position_slow(self, x,y, dx,dy):
        # update target position
        self.stage.settings.x_target_position.update_value(x)
        self.stage.settings.y_target_position.update_value(y)
        
        t0 = time.time()
        
        # Wait until stage has moved to target
        while True:
            self.stage.settings.x_position.read_from_hardware()
            self.stage.settings.y_position.read_from_hardware()
            if self.distance_from_target() < self.target_range:
                #print("settle time {}".format(time.time() - t0))
                break
            if (time.time() - t0) > self.slow_move_timeout:
                raise IOError("AttoCube ECC100 took too long to reach position")
            time.sleep(0.005)

    def move_position_fast(self, x,y, dx,dy):
        self.move_position_slow(x, y, dx, dy)
        #settle time even on small steps seems to be 30ms,
        #so we should always wait until settle
        """# update target position, but don't wait to settle to target
        self.stage.settings.x_target_position.update_value(x)
        self.stage.settings.y_target_position.update_value(y)
        self.stage.settings.x_position.read_from_hardware()
        self.stage.settings.y_position.read_from_hardware()
        """
    def distance_from_target(self):
        S = self.stage.settings
        return (  (S['x_position'] - S['x_target_position'])**2 
                + (S['y_position'] - S['y_target_position'])**2)
