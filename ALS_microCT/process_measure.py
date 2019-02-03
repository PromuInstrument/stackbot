from ScopeFoundry.measurement import Measurement
import time
import numpy as np

class ChamberProcessMeasure(Measurement):
    
    name = 'chamber_process'
    
    def setup(self):
        pass
    
    def run(self):
        
        
        #start data logger
        self.app.measurements['chamber_data_log'].settings['activation'] = True
        
        t0 = time.time()

        
        try:
            # set flow to 
            self.app.hardware['sierra_mfc'].settings['setpoint'] = 100
            time.sleep(8.0)
            
            total_ramp_time = 30.0
            max_current_ramp = 15.0
            dt = 0.25
            #current_setpoints = np.linspace(0, max_current_ramp, total_ramp_time/dt)

            current_setpoints_up = np.linspace(0, max_current_ramp, total_ramp_time/dt)
            current_setpoints_down = current_setpoints_up[::-1]
            current_setpoints = np.concatenate((current_setpoints_up, current_setpoints_down))


            self.app.hardware['lambda_zup1'].settings['current_setpoint'] = current_setpoints[0]
            self.app.hardware['lambda_zup2'].settings['current_setpoint'] = current_setpoints[0]

            # Turn on lamps
            self.app.hardware['lambda_zup1'].settings['output_enable'] = True
            self.app.hardware['lambda_zup2'].settings['output_enable'] = True
            
            # start ramp
            for current in current_setpoints:
                if self.interrupt_measurement_called:
                    break
                self.app.hardware['lambda_zup1'].settings['current_setpoint'] = current
                self.app.hardware['lambda_zup2'].settings['current_setpoint'] = current
                time.sleep(dt)
                                
        finally:
            # turn off lamps
            self.app.hardware['lambda_zup1'].settings['output_enable'] = False
            self.app.hardware['lambda_zup2'].settings['output_enable'] = False

            
            # set flow to zero
            self.app.hardware['sierra_mfc'].settings['setpoint'] = 0
            
        #time.sleep(5.0)
        #self.app.measurements['chamber_data_log'].settings['activation'] = False


            
