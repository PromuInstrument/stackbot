import numpy as np
import time
from qtpy import QtCore

from ScopeFoundry import h5_io
from ScopeFoundry import Measurement 
 
        
class Base2DScan(Measurement):
    
    def setup(self):
        
        self.display_update_period = 0.1 #seconds

        #connect events        
        self.int_time = self.gui.apd_counter_hc.int_time
        
        # local logged quantities
        lq_params = dict(dtype=float, vmin=-1,vmax=100, ro=False, unit='um' )
        self.h0 = self.add_logged_quantity('h0',  initial=25, **lq_params  )
        self.h1 = self.add_logged_quantity('h1',  initial=45, **lq_params  )
        self.v0 = self.add_logged_quantity('v0',  initial=25, **lq_params  )
        self.v1 = self.add_logged_quantity('v1',  initial=45, **lq_params  )

        self.dh = self.add_logged_quantity('dh', initial=1, **lq_params)
        self.dh.spinbox_decimals = 3
        self.dv = self.add_logged_quantity('dv', initial=1, **lq_params)
        self.dv.spinbox_decimals = 3
        
        # connect to gui        
        self.h0.connect_bidir_to_widget(self.gui.ui.h0_doubleSpinBox)
        self.h1.connect_bidir_to_widget(self.gui.ui.h1_doubleSpinBox)
        self.v0.connect_bidir_to_widget(self.gui.ui.v0_doubleSpinBox)
        self.v1.connect_bidir_to_widget(self.gui.ui.v1_doubleSpinBox)
        
        self.dh.connect_bidir_to_widget(self.gui.ui.dh_doubleSpinBox)
        self.dv.connect_bidir_to_widget(self.gui.ui.dv_doubleSpinBox)
        
        self.scan_specific_setup()
    
    def scan_specific_setup(self):
        "subclass this function to setup additional logged quantities and gui connections"
        # logged quantities
        # connect events
        raise NotImplementedError()
        
    def setup_figure(self):
        #2D scan area
        #raise NotImplementedError()
        pass
    
    def pre_scan_setup(self):
        raise NotImplementedError()
        # hardware
        # create data arrays
        # update figure
    
    def collect_pixel(self, i_h, i_v):
        # collect data
        # store in arrays        
        raise NotImplementedError()
    
    def post_scan_cleanup(self):
        pass
    
    def scan_specific_savedict(self):
        return dict()    
        
    def _run(self):
        #hardware 
        self.stage = self.gui.mcl_xyz_stage_hc
        self.nanodrive = self.stage.nanodrive

        # Data arrays
        self.h_array = np.arange(self.h0.val, self.h1.val, self.dh.val, dtype=float)
        self.v_array = np.arange(self.v0.val, self.v1.val, self.dv.val, dtype=float)
        
        self.Nh = len(self.h_array)
        self.Nv = len(self.v_array)
        
        self.range_extent = [self.h0.val, self.h1.val, self.v0.val, self.v1.val]

        self.corners =  [self.h_array[0], self.h_array[-1], self.v_array[0], self.v_array[-1]]
        
        self.imshow_extent = [self.h_array[ 0] - 0.5*self.dh.val,
                              self.h_array[-1] + 0.5*self.dh.val,
                              self.v_array[ 0] - 0.5*self.dv.val,
                              self.v_array[-1] + 0.5*self.dv.val]
        
        # h5 data file setup
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(self.gui, "%i_%s.h5" % (self.t0, self.name) )
        self.h5_file.attrs['time_id'] = self.t0
        self.h5_meas_group = self.h5_file.create_group(self.name)
        #h5_io.h5_save_measurement(self, self.h5_meas_group)
        h5_io.h5_save_measurement_settings(self, self.h5_file['/'])
        
        self.h5_meas_group.create_dataset(name='h_array', data=self.h_array, compression='gzip', shuffle=True)
        self.h5_meas_group.create_dataset(name='v_array', data=self.v_array, compression='gzip', shuffle=True)
        self.h5_meas_group.attrs['Nv'] = self.Nv
        self.h5_meas_group.attrs['Nh'] = self.Nh
        self.h5_meas_group.attrs['range_extent'] = self.range_extent
        self.h5_meas_group.attrs['corners'] = self.corners
        self.h5_meas_group.attrs['imshow_extent'] = self.imshow_extent

        #scan specific setup
        self.pre_scan_setup()
                
        # TODO Stop other timers?!
        
        print "scanning"
        self.current_pixel_num = 0
        self.t_scan_start = time.time()
        try:
            
            v_axis_id = self.stage.v_axis_id
            h_axis_id = self.stage.h_axis_id
            
            # move slowly to start position
            start_pos = [None, None,None]
            start_pos[v_axis_id-1] = self.v_array[0]
            start_pos[h_axis_id-1] = self.h_array[0]
            #print "scan.."
            
            print start_pos
            self.nanodrive.set_pos_slow(*start_pos)
            
            # Scan!            
            line_time0 = time.time()

            for i_v in range(self.Nv):
                if self.interrupt_measurement_called:
                    break               
                
                self.v_pos = self.v_array[i_v]
                self.nanodrive.set_pos_ax(self.v_pos, v_axis_id)
                #self.read_stage_position()       
    
                if i_v % 2: #odd lines
                    h_line_indicies = range(self.Nh)[::-1]
                else:       #even lines -- traverse in opposite direction
                    h_line_indicies = range(self.Nh)            
    
                for i_h in h_line_indicies:
                    if self.interrupt_measurement_called:
                        break
        
                    self.h_pos = self.h_array[i_h]
                    self.nanodrive.set_pos_ax(self.h_pos, h_axis_id)    
                    
                    # collect data
                    self.collect_pixel(i_h, i_v)            
                    self.current_pixel_num += 1
    
                T_pixel =  float(time.time() - line_time0)/self.Nh
                print "line time:", time.time() - line_time0
                line_time0 = time.time()
                self.progress.update_value(self.current_pixel_num *100./(self.Nv*self.Nh))
                
                total_px = self.Nv*self.Nh
                print "time per pixel:", T_pixel, '| estimated total time (h)', total_px*T_pixel/3600,'| Nh, Nv:', self.Nh, self.Nv,
                Time_finish = time.localtime(total_px*T_pixel+self.t_scan_start)
                print '| scan finishes at: {:02d}:{:02d}'.format(Time_finish.tm_hour,Time_finish.tm_min)

                
                # read stage position every line
                self.stage.read_pos()
                
                            
            #scanning done
            self.post_scan_cleanup()
        #except Exception as err:
        #    self.interrupt()
        #    raise err
        finally:
            #save  data file
            save_dict = {
                     'h_array': self.h_array,
                     'v_array': self.v_array,
                     'Nv': self.Nv,
                     'Nh': self.Nh,
                     'range_extent': self.range_extent,
                     'corners': self.corners,
                     'imshow_extent': self.imshow_extent,
                        }               

            save_dict.update(self.scan_specific_savedict())
                    
            for lqname,lq in self.gui.logged_quantities.items():
                save_dict[lqname] = lq.val
            
            for hc in self.gui.hardware_components.values():
                for lqname,lq in hc.logged_quantities.items():
                    save_dict[hc.name + "_" + lqname] = lq.val
            
            for lqname,lq in self.logged_quantities.items():
                save_dict[self.name +"_"+ lqname] = lq.val
    
            self.fname = "%i_%s.npz" % (self.t0, self.name)
            np.savez_compressed(self.fname, **save_dict)
            print self.name, "saved:", self.fname
            
            #h5 file
            self.h5_file.close()

            if not self.interrupt_measurement_called:
                self.measurement_sucessfully_completed.emit()
            else:
                pass


