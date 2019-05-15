from ScopeFoundry.measurement import Measurement
import time
import pyqtgraph as pg

class ChamberDataLogMeasure(Measurement):
    
    name = 'chamber_data_log'
    
    def setup(self):
        pass
    
    def run(self):
        
        lq_polling_list = [
            # LQ, poll time (seconds) if <0 no poll
            ("hardware/pressure_gauge/adc_val", -1),
            ("hardware/pressure_gauge/pressure", -1),
            
            ("hardware/lambda_zup1/current_actual", -1),
            ("hardware/lambda_zup1/current_setpoint", -1),
            ("hardware/lambda_zup1/voltage_actual", -1),
            ("hardware/lambda_zup1/voltage_setpoint", -1),
            
            ("hardware/lambda_zup2/current_actual", -1),
            ("hardware/lambda_zup2/current_setpoint", -1),
            ("hardware/lambda_zup2/voltage_actual", -1),
            ("hardware/lambda_zup2/voltage_setpoint", -1),
            
            ("hardware/sierra_mfc/flow", -1),
            ("hardware/sierra_mfc/setpoint", -1),
            
            #("hardware/tc_reader/temp0", 1.0)
            ("hardware/tc_reader_stream/temp0", -1),
            ]
        
            
        self.lq_data = dict()
        last_poll_times = dict()
        self.time_list = [0]
        
        for lq_path, poll_time in lq_polling_list:
            self.lq_data[lq_path] = []
            last_poll_times[lq_path] = 0

        t_start = time.time()
        
        self.ii = 0
        

        ini_fname = self.app.generate_data_path(self, ext='ini', t=t_start)
        self.app.settings_save_ini(ini_fname)
        
        fname = self.app.generate_data_path(self, ext='csv', t=t_start)
        
        with open(fname, 'w') as csv_file:
            
            # write csv header
            header = ",".join(["time",] + list(self.lq_data.keys()))
            csv_file.write(header)
            csv_file.write('\n')
            
            while not self.interrupt_measurement_called:
                t = time.time() - t_start

                #print("time:", t, "dt:", t - self.time_list[-1])
                
                self.time_list.append(t)
                
                
                for lq_path, poll_time in lq_polling_list:
                    
                    lq = self.app.lq_path(lq_path)
                    
                    dt = t - last_poll_times[lq_path]
                    
                    if poll_time > 0:
                        if dt > poll_time:
                            t0_poll = time.time()
                            lq.read_from_hardware()
                            #print(lq_path, "read took", time.time() - t0_poll)
                            last_poll_times[lq_path] = t
                
                    self.lq_data[lq_path].append(lq.value)
                
                
                data_row = [t,] + [ self.lq_data[lq_path][-1] for lq_path in self.lq_data.keys() ]
                csv_file.write( ",".join([str(x) for x in data_row]))
                csv_file.write('\n')

                self.ii += 1
                time.sleep(0.010)
                
    def setup_figure(self):
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget()
        
        self.lq_plot_list = [
                             "hardware/tc_reader_stream/temp0",
                             #"hardware/tc_reader/temp0",
                             "hardware/pressure_gauge/pressure", 
                             "hardware/lambda_zup1/current_actual",
                             "hardware/sierra_mfc/flow"]
        self.lq_plots = dict()
        self.lq_plotlines = dict()
        for i, lq_path in enumerate(self.lq_plot_list):
            p = self.graph_layout.addPlot(row=i, col=0)
            p.setTitle(lq_path)
            self.lq_plots[lq_path] = p
            self.lq_plotlines[lq_path] = p.plot()
            
    def update_display(self):
        for lq_path, plotline in self.lq_plotlines.items():
            ii = self.ii
            plotline.setData(self.time_list[:ii], self.lq_data[lq_path][:ii])
