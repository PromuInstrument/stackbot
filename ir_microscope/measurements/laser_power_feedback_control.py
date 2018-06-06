from ScopeFoundry import Measurement
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph import dockarea
from ScopeFoundry import h5_io

class LaserPowerFeedbackControl(Measurement):

    name = "laser_power_feedback_control"
    
    def setup(self):

        self.display_update_period = 0.1 #seconds


        self.update_interval = self.settings.New("update_interval",  dtype=float, unit="sec", initial=0.1, si=True)
        self.p_gain = self.settings.New("p_gain", dtype=float, unit = "steps/V", initial = 1000, si=True)
        self.max_position = self.settings.New("max_position", dtype=int, unit="step", initial=24000000, si=False)
        self.min_position = self.settings.New("min_position", dtype=int, unit="step", initial=-24000000, si=False)

        self.set_voltage      = self.settings.New("set_voltage",    unit="V", dtype=float, ro=False, vmin=0, vmax=2, si=True)
        self.present_voltage  = self.settings.New("present_voltage", unit="V", dtype=float, ro=True, si=True)

        self.encoder_position = self.settings.New("encoder_position", dtype=int, ro=True, unit="steps", si=False)


        self.optimize_history_len = self.settings.New('optimize_history_len', dtype=int, 
                                                      initial=100,
                                                      vmin=2, ro=False)
        
        self.save_h5 = self.settings.New('save_h5', dtype=bool, initial=False, ro=False)


        
    def setup_figure(self):
        self.ui = self.dockarea = dockarea.DockArea()
        self.settings_dock = self.dockarea.addDock(name='Settings', position='top', 
                              widget=self.settings.New_UI()
                              )
        
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.graph_dock = self.dockarea.addDock(name='plot', 
                                                #position='below',
                                                relativeTo=self.settings_dock,
                                                widget=self.graph_layout)
        
        self.plot = self.graph_layout.addPlot(title='normalized power', 
                                              labels = {'left':'present/set voltage','bottom':'time (a.u)'})
        
        self.plot_line = pg.PlotCurveItem()
        self.plot.addItem(self.plot_line)
        
        self.infline = pg.InfiniteLine(pos=(0,1), angle=0)
        self.plot.addItem(self.infline)
        self.plot.addItem(pg.InfiniteLine(pos=(0,0), angle=0))
        
        
        
    def run(self):
        # hardware components
        self.power_wheel_hc = self.app.hardware['power_wheel_arduino']
        self.power_wheel    = self.power_wheel_hc.power_wheel_dev
        self.power_analog_hc = self.app.hardware['thorlabs_powermeter_analog_readout']
        self.powermeter = self.app.hardware['thorlabs_powermeter']

        #set up
        self.set_voltage.update_value(self.power_analog_hc.voltage.read_from_hardware())

        self.power_wheel.read_status()

        
        self.optimize_history = np.zeros(self.optimize_history_len.val, dtype=np.float)        
        self.optimize_ii = 0
        self.t0 = time.time()
        t0_pow_reading = self.powermeter.settings.power.read_from_hardware()

        
          
        
        while not self.interrupt_measurement_called:

            # read current state
            self.encoder_position.update_value(self.power_wheel_hc.encoder_pos.read_from_hardware())
            self.present_voltage.update_value(self.power_analog_hc.voltage.read_from_hardware())

            # compute motion
            v_error = self.set_voltage.val - self.present_voltage.val
            move_delta_steps = (v_error * self.p_gain.val)

            # Limit motion per step
            if move_delta_steps > 100:
                move_delta_steps = 100
            if move_delta_steps < -100:
                move_delta_steps = -100


            # Check limits on motion
            final_pos = self.encoder_position.val + move_delta_steps
            
            if final_pos > self.max_position.val:
                print(self.name,"target encoder position above maximum")
                move_delta_steps = self.max_position.val - self.encoder_position.val
            if final_pos < self.min_position.val:
                print(self.name,"target encoder position bellow minimum")
                move_delta_steps = self.min_position.val - self.encoder_position.val

            # move
            move_delta_steps = int(move_delta_steps)
            #TODO can be done with power_wheel.write_steps_and_wait()
            self.power_wheel.write_steps(move_delta_steps)
            sleep_time = abs(move_delta_steps*1.0/100)
            time.sleep(sleep_time)
            self.power_wheel.read_status()
            while(self.power_wheel.is_moving_to):
                time.sleep(0.050)
                s = self.power_wheel.read_status()
                #print(s)
                if self.interrupt_measurement_called:
                    self.power_wheel.write_brake()
                    break
            
            self.encoder_position.update_value(self.power_wheel_hc.encoder_pos.read_from_hardware())
            self.present_voltage.update_value(self.power_analog_hc.voltage.read_from_hardware())

            time.sleep(self.update_interval.val)
            
            self.optimize_history[self.optimize_ii] = self.present_voltage.val/self.set_voltage.val
            self.optimize_ii += 1          
            if (self.optimize_ii % self.optimize_history_len.val == 0 or self.interrupt_measurement_called) and self.settings['save_h5']:
                self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
                t1_pow_reading = self.powermeter.settings.power.read_from_hardware()
                self.h5_file.attrs['time_id'] = self.t0
                H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)  
                self.t1 = time.time()
                H['time_start'] = self.t0
                H['time_end'] = self.t1
                H['normalized_power'] = self.optimize_history[0:self.optimize_ii]
                H['time_array'] = np.linspace(0, self.t1-self.t0, self.optimize_ii) 
                H['power_at_time_end'] = t1_pow_reading
                H['power_at_time_start'] = t0_pow_reading
                self.h5_file.close()  
                
                
            self.settings.activation.update_value(True)
            self.optimize_ii %= self.optimize_history_len.val
            
            


    def update_display(self):
        self.plot_line.setData(np.arange(self.optimize_history_len.val),self.optimize_history)

