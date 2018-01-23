'''Frank Ogletree and Ed Barnard'''

from __future__ import division
from ScopeFoundry import Measurement, h5_io
import pyqtgraph as pg
import numpy as np
import time, datetime
from qtpy import QtWidgets

from ScopeFoundryHW.ni_daq import NI_AdcTask

class DateAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        strns = []
        if len(values) < 1:
            return []
        rng = max(values)-min(values)
        #if rng < 120:
        #    return pg.AxisItem.tickStrings(self, values, scale, spacing)
        if rng < 3600*24:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= 3600*24 and rng < 3600*24*30:
            string = '%m/%d %H:%M'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= 3600*24*30 and rng < 3600*24*30*24:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >=3600*24*30*24:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            try:
                strns.append(time.strftime(string, time.localtime(x)))
            except ValueError:  ## Windows can't handle dates before 1970
                strns.append('')
        try:
            label = time.strftime(label1, time.localtime(min(values)))+time.strftime(label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        #self.setLabel(text=label)
        return strns
    
class AugerPressureHistory(Measurement):
    
    name = "auger_pressure_history"
    
    def setup(self):
        
        self.has_turbo = 'tc110_turbo' in self.app.hardware

        if self.has_turbo:
            self.turbo_names = []
            for name in ['prep', 'ion', 'nano']:
                for x in ['speed', 'power', 'temp']:
                    self.turbo_names.append(name + "_" + x)
        
        
        self.settings.New('delta_t', dtype=float, unit='s', vmin=0.0, initial=1.0)
        self.settings.New('save_h5', dtype=bool, initial=True)
        
        #display
        self.settings.New('show_last', dtype=int, initial=-1)
        
        self.names = names = ('Prep','Nano')
        for name in self.names:
            self.settings.New(name+"_pressure", dtype=float, ro=True, si=True, unit="Bar")
        #self.settings.New('start_time', dtype=str, ro=True, initial = datestring())
        self.settings.New('ADC_channels', dtype=str, initial = '9215A/ai0:1')
        self.settings.New('TC_channels', dtype=str, initial = 'cDAQ1-9211/ai0:1')
    
        #setup gui
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QHBoxLayout()
        self.ui.setLayout(self.layout)
        self.control_widget = QtWidgets.QGroupBox(self.name)
        self.layout.addWidget(self.control_widget, stretch=0)
        self.control_widget.setLayout(QtWidgets.QVBoxLayout())

        self.start_button= QtWidgets.QPushButton("Start")
        self.control_widget.layout().addWidget(self.start_button)
        self.stop_button= QtWidgets.QPushButton("Stop")
        self.control_widget.layout().addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        self.control_widget.layout().addWidget(\
            self.settings.New_UI(exclude=['activation','progress','profile']))

        self.control_widget.layout().addWidget(\
            self.app.settings.New_UI())

        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))        
        self.layout.addWidget(self.graph_layout,stretch=1)
        
        self.ui.show()
        self.ui.setWindowTitle("auger_pressure_history")

        self.NUM_CHANS = 2
        
        self.TC_CHAN_NAMES = ['oven_air', 'vac_system']
        self.TC_CHANS = 2
        
        self.plots = []
        
        #ion gauge pressure display
        axis = DateAxis(orientation='bottom')
        self.pressure_plot = plot = self.graph_layout.addPlot(title="Pressure", axisItems={'bottom': axis})
        plot.setLogMode(y=True)
        plot.setYRange(-11,-6)
        plot.showGrid(y=True,x=True,alpha=1.0)
        plot.addLegend()
        
        self.plots.append(plot)
        
        self.pressure_plot_lines = []
        for i in range(self.NUM_CHANS):
            color = pg.intColor(i)
            plot_line = self.pressure_plot.plot(pen=pg.mkPen(color, width=4), 
                                           name=names[i], 
                                           autoDownsample=True)
            self.pressure_plot_lines.append(plot_line)
        self.graph_layout.nextRow()
            
        #turbo status display
        self.turbo_plot = self.graph_layout.addPlot(title="Turbo", axisItems={'bottom': axis})
        self.turbo_plot.showGrid(y=True,x=True,alpha=1.0)
        self.turbo_plot.addLegend()
        self.turbo_plot_lines = dict()
        
        for name in self.turbo_names:
            if 'prep' in name:
                color = 'r'
            elif 'ion' in name:
                color = 'y'
            else:
                color = 'w'
            if 'speed' in name:
                width = 4
                style = 1
            elif 'power' in name:
                style= 2
                width = 2                
            else:
                style=style = 3
                width = 1
            
            self.turbo_plot_lines[name] = self.turbo_plot.plot(pen=pg.mkPen(color=color, width=width), 
                                                               name=name, autoDownsample=True)
        
            
        
        
    def volts_to_pressure(self,volts):
        '''
        convert log output of ion gauge into mBarr)
        FIX not working for prep ion gauge, vmin or vmax must be wrong...
        '''
        vmin=np.array([0.0,0.078])
        vmax=np.array([10.0,2.89])
        vhi=np.array([1.0,1.0])
        vlo=np.array([0.0,0.0])
        
        pmin=np.array([1e-11,1e-12])
        pmax=np.array([1e-2,0.2])
        vr = (volts-vmin)/(vmax-vmin)
        vr = np.minimum(1.0,np.maximum(vr,0.0))
        pr=np.log(pmax/pmin)
        return pmin*np.exp(vr*pr)           
            
    def run(self):
        print(self.name, 'run')
        
        #self.settings['start_time'] = self.datestring()
        block =self.block = 100
        self.chan_history_pressure = np.zeros( (self.NUM_CHANS, block), dtype=float )
        #self.chan_history_pressure[:,:] = 1e-11
        self.chan_history_time = self.settings['delta_t'] * np.arange(block)
        self.history_i = 0
        self.display_i = 0
        
        self.press_adc = NI_AdcTask(self.settings['ADC_channels'],name='pressure')
        self.temp_adc = NI_AdcTask(self.settings['TC_channels'],name='temperature')
        self.start_time = time.time()
        print( datetime.datetime.now().strftime("%H:%M %b %d, %Y "))
        
        
        try:
            # H5 File
            if self.settings['save_h5']:
                self.h5file = h5_io.h5_base_file(app=self.app,measurement=self)
                self.h5m = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
                
                self.pressure_h5 = self.h5m.create_dataset('pressure', dtype=float, shape=(self.NUM_CHANS,block),
                                                                        maxshape=(self.NUM_CHANS, None), chunks=(self.NUM_CHANS,block))
                #self.time_h5 = self.h5m.create_dataset('time', dtype=float, shape=(block,),
                #                                                        maxshape=(None,), chunks=(block,))
                
                self.epoch_h5 = self.h5m.create_dataset('epoch', dtype=float, shape=(block,),
                                                                        maxshape=(None,), chunks=(block,))
                
                self.tc_temp_h5 = self.h5m.create_dataset('tc_temp', dtype=float, shape=(self.TC_CHANS, block),
                                                                    maxshape=(self.TC_CHANS, None), chunks=(self.TC_CHANS, block))
                
                print('saving to h5:', self.h5file.filename)
                
                if self.has_turbo:                    
                    for name in self.turbo_names:
                        self.h5m.create_dataset(name, 
                                                dtype=float, shape=(block,),
                                                maxshape=(None,), chunks=(block,))
                    
            
            while not self.interrupt_measurement_called:
                                
                #read ion gauge pressure
                volts=0.0
                i_ave = 0
                start = time.time()
                while (time.time() - start) < self.settings['delta_t'] or i_ave == 0:
                    i_ave += 1
                    volts += self.press_adc.get()
                volts /= i_ave
                pressure = self.volts_to_pressure(volts)
                
                self.settings['Prep_pressure'] = pressure[0]*1e-3
                self.settings['Nano_pressure'] = pressure[1]*1e-3

                # read tc temperatures
                temps = [0,0] #self.temp_adc.get()
                

                # timestamp
                abs_time = time.time()
                sample_time = abs_time - self.start_time

                
                # write to numpy arrays
                self.chan_history_time = np_block_extend(self.chan_history_time, self.history_i, 
                                                        block, axis=0)
                self.chan_history_time[self.history_i] = sample_time

                self.chan_history_pressure = np_block_extend(self.chan_history_pressure, self.history_i, 
                                                        block, axis=1)
                self.chan_history_pressure[:,self.history_i] = pressure

                # write to h5
                if self.settings['save_h5']:
                    #h5_resize_and_insert(self.time_h5, self.history_i, 
                    #                     data=sample_time, block=block, axis=0)
                    h5_resize_and_insert(self.epoch_h5, self.history_i, 
                                         data=abs_time, block=block, axis=0)
                    h5_resize_and_insert(self.pressure_h5, self.history_i, 
                                         data=pressure[:], block=block, axis=1)
                    h5_resize_and_insert(self.tc_temp_h5, self.history_i, 
                                         data=temps, block=block, axis=1)
                    
                    if self.has_turbo:
                        for name in self.turbo_names:
                            val = self.app.hardware['tc110_turbo'].settings.get_lq(name).read_from_hardware()
                            h5_resize_and_insert(self.h5m[name], self.history_i, 
                                                 data=val, block=block, axis=0)
                
                #print(volts, self.chan_history_pressure.shape)
                self.history_i += 1       
        finally:
            self.h5file.close()
            
            self.press_adc.close()
            self.temp_adc.close()
            del self.press_adc
            del self.temp_adc
            
            print(self.name, 'stopped')
        
            
    def update_display(self):
        
        if self.history_i > self.display_i:
            jj1 = self.history_i 
            
            show_last = self.settings['show_last']
            if show_last < 0:
                jj0 = 0
            else:
                jj0 = max(0, jj1 - show_last)
                
            #pressure
            for i in range(self.NUM_CHANS):
                self.pressure_plot_lines[i].setData(
                    self.epoch_h5[jj0:jj1],
                    self.chan_history_pressure[i,jj0:jj1])
                
            #Turbo
            for name in self.turbo_names:
                yy = np.array(self.h5m[name][jj0:jj1], dtype=float)
                if 'speed' in name: #convert to %
                    if 'ion' in name:
                        yy /= 15.
                    else:
                        yy /= 10.
                self.turbo_plot_lines[name].setData(
                    self.epoch_h5[jj0:jj1],
                    yy
                    )
            
            self.display_i = self.history_i

def h5_resize_and_insert(arr, i, data, block, axis=0):
    curr_size = arr.shape[axis]
    if i >= curr_size:
        #print('too big', i, curr_size)
        new_shape = list(arr.shape)
        new_shape[axis] = curr_size + block
        arr.resize(new_shape)
    
    insert_slice = [np.s_[:],]*len(arr.shape)
    insert_slice[axis] = i
    
    arr[tuple(insert_slice)] = data
    
def np_block_extend(arr, i, block, axis=0):
    curr_size = arr.shape[axis]
    if i >= curr_size:
        #print('too big', i, curr_size)
        block_shape = list(arr.shape)
        block_shape[axis] = block
        zero_block = np.zeros( block_shape, dtype=arr.dtype )
        return np.append(arr, zero_block, axis=axis)
    else:
        return arr