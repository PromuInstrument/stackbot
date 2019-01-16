from ScopeFoundry import Measurement
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph import dockarea
from ScopeFoundry import h5_io

class LaserPowerFeedbackControl(Measurement):

    name = "laser_power_feedback_control"
    
    def setup(self):

        self.display_update_period = 0.2 #seconds


        self.update_interval = self.settings.New("update_interval",  dtype=float, unit="sec", initial=0.1, si=True)
        self.settings.New("position_range", dtype=float, unit="deg", initial=10, si=False, vmin=0)
        self.p_gain = self.settings.New("p_gain", dtype=float, unit = "steps/W", initial = 1000, si=True)
        self.settings.New('setpoint_power', unit='W', si=True, dtype=float, initial=1e-6)
        self.settings.New('set_setpoint_on_start', dtype=bool, initial=True)


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
        
        self.plot = self.graph_layout.addPlot(title='power history', 
                                              labels = {'left':'present/set voltage','bottom':'time (a.u)'})
        
        self.plot_line = self.plot.plot([1,2,3]) 
        
        self.graph_layout.nextRow()
        
        self.plot_err = self.graph_layout.addPlot(title = 'err')
        self.err_plotline = self.plot_err.plot()

        self.graph_layout.nextRow()
        
        self.plot_pos = self.graph_layout.addPlot(title='pos')
        self.pos_plotline = self.plot_pos.plot()
        
        
        
        #pg.PlotCurveItem()
        #self.plot.addItem(self.plot_line)
        
        #self.infline = pg.InfiniteLine(pos=(0,1), angle=0)
        #self.plot.addItem(self.infline)
        #self.plot.addItem(pg.InfiniteLine(pos=(0,0), angle=0))
        
        
        
    def run(self):
        # hardware components
        
        pw = self.app.hardware['power_wheel']
        pw_pos = pw.settings.position
        
        pw.settings['connected'] = True
        
        #self.power_wheel_hc = self.app.hardware['power_wheel_arduino']
        #self.power_wheel    = self.power_wheel_hc.power_wheel_dev
        #self.power_analog_hc = self.app.hardware['thorlabs_powermeter_analog_readout']
        pm = self.app.hardware['thorlabs_powermeter']
        pm_power = pm.settings.power
        pm.settings['connected'] = True

        #set up
        #self.set_voltage.update_value(self.power_analog_hc.voltage.read_from_hardware())

        #self.power_wheel.read_status()

        if self.settings['set_setpoint_on_start']:
            self.settings['setpoint_power'] = pm_power.read_from_hardware()

        
        N = self.optimize_history_len.val
        self.pow_history = np.zeros(N, dtype=np.float)
        
        self.time_history = np.zeros(N, dtype=float)
        self.err_history = np.zeros(N,dtype=float)
        self.pos_history = np.zeros(N, dtype=float)
             
        self.optimize_ii = 0
        self.t0 = time.time()
        t0_pow_reading = pm_power.read_from_hardware()
        
        
        pw.settings.raw_position.read_from_hardware()
        self.initial_pos = pw_pos.val
        self.max_pos = self.initial_pos + 0.5*self.settings['position_range']
        self.min_pos = self.initial_pos - 0.5*self.settings['position_range']
        
        
        
        while not self.interrupt_measurement_called:

            # read current state
            #self.encoder_position.update_value(self.power_wheel_hc.encoder_pos.read_from_hardware())
            #self.present_voltage.update_value(self.power_analog_hc.voltage.read_from_hardware())
            pm_power.read_from_hardware()
            #pw.settings.raw_position.read_from_hardware()
            

            # compute motion
            power_error = pm_power.val - self.settings['setpoint_power']
            move_delta_steps = -(power_error * self.p_gain.val)

            #print(pm_power.val, pw_pos.val, power_error, move_delta_steps)


#             # Limit motion per step
#             if move_delta_steps > 100:
#                 move_delta_steps = 100
#             if move_delta_steps < -100:
#                 move_delta_steps = -100

            


            # Check limits on motion
            final_pos = pw_pos.val + move_delta_steps
            
            if   final_pos > self.max_pos:
                print(self.name,"target encoder position above maximum")
                #move_delta_steps = self.max_position.val - self.encoder_position.val
                final_pos = self.max_pos
            
            elif final_pos < self.min_pos:
                print(self.name,"target encoder position bellow minimum")
                #move_delta_steps = self.min_position.val - self.encoder_position.val
                final_pos = self.min_pos

            # move
            pw_pos.update_value(final_pos)
                        
            #wait?
            
            time.sleep(self.update_interval.val)
            
            ii = self.optimize_ii
            self.pow_history[ii] = pm_power.val
            self.time_history[ii] = time.time() - self.t0
            self.err_history[ii] = power_error
            self.pos_history[ii]  = pw_pos.val
            
            self.optimize_ii += 1          
            if (self.optimize_ii % self.optimize_history_len.val == 0 or self.interrupt_measurement_called) and self.settings['save_h5']:
                self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
                t1_pow_reading = pm_power.read_from_hardware()
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
        ii = self.optimize_ii
        self.plot_line.setData(self.time_history[:ii],self.pow_history[:ii])
        self.err_plotline.setData(self.time_history[:ii],self.err_history[:ii])
        self.pos_plotline.setData(self.time_history[:ii],self.pos_history[:ii])


