from ScopeFoundry.measurement import Measurement
import time
import numpy as np

class BeamDwellMeasure(Measurement):
    
    name = 'beam_dwell'    
    
    def setup(self):
        
        self.settings.New('n_pixels', dtype=int, vmin=2, initial=8)
        self.settings.New('min_exp', dtype=int, vmin=-3, initial=-1)
        self.settings.New('max_exp', dtype=int, vmin=-3, initial=1)
        self.settings.New('dwell_time', dtype=float, vmin=0.001, initial=0.1)
        self.settings.New('constant_dwell', dtype=bool, initial = False)
        self.settings.New('voltage_min',dtype=float, vmin=-10.,initial=-10.)
        self.settings.New('voltage_max',dtype=float, vmin=-10.,initial=10.)
        self.settings.New('BEASTMODE',dtype=bool,initial=False)
    
    def run(self):
        
        beam_hw = self.app.hardware['static_beam_pos']
        beam_hw.settings['connected'] = True
        
        time.sleep(0.2)
        
        num_pix = self.settings['n_pixels']
        max_exp = self.settings['max_exp']
        min_exp = self.settings['min_exp']
        volt_min = -self.settings['voltage_min']
        volt_max = -self.settings['voltage_max']
        volt_range = volt_max - volt_min
        
        dwell = self.settings['dwell_time']
        
        
        BEASTMODE = self.settings['BEASTMODE']
        if BEASTMODE ==True:
            
            tt = np.linspace(0,2*np.pi,25)
            x,y = 8*np.cos(tt),8*np.sin(tt)
            locs_head = [(xx,yy,dwell) for xx,yy in zip(x,y)]
            
            tt = np.linspace(5*np.pi/4,7*np.pi/4,10)
            x,y = 5*np.cos(tt),5*np.sin(tt)
            locs_smile = [(xx,yy,dwell) for xx,yy in zip(x,y)]
            
            tt = [3*np.pi/4,np.pi/4]
            x,y = 3.5*np.cos(tt),3.5*np.sin(tt)
            locs_eye = [(xx,yy,dwell) for xx,yy in zip(x,y)]
            
            locations = locs_head + locs_smile + locs_eye
            
        
        else:
            locx = np.arange(volt_min,volt_max,volt_range/float(num_pix))
            locx = locx + volt_range/(2.0*num_pix)
        
            locy = np.copy(locx)
        
            locations = np.array([(yy,xx,dwell) for xx in locx for yy in locy])
            if self.settings['constant_dwell']==False:
                dts = np.logspace(min_exp,max_exp,num_pix**2)
                for l,d in zip(locations,dts):
                    l[-1]=d
        
        #locations = [(-7.5,-7.5,0.5),(-2.5,-7.5,0.5),(2.5,-7.5,0.5),(7.5,-7.5,0.5),
        #             (-7.5,-2.5,0.5),(-2.5,-2.5,0.5),(2.5,-2.5,0.5),(7.5,-2.5,0.5),
        #             (-7.5,2.5,0.5),(-2.5,2.5,0.5),(2.5,2.5,0.5),(7.5,2.5,0.5),
        #             (-7.5,7.5,0.5),(-2.5,7.5,0.5),(2.5,7.5,0.5),(7.5,7.5,0.5)]
        
        #locations = [(-7.5,-7.5,0.5),(-2.5,-7.5,0.5),(2.5,-7.5,0.5),(7.5,-7.5,0.5),
        #             (7.5,-2.5,0.5),(2.5,-2.5,0.5),(-2.5,-2.5,0.5),(-7.5,-2.5,0.5),
        #             (-7.5,2.5,0.5),(-2.5,2.5,0.5),(2.5,2.5,0.5),(7.5,2.5,0.5),
        #             (-7.5,7.5,0.5),(-2.5,7.5,0.5),(2.5,7.5,0.5),(7.5,7.5,0.5)]

        
        
        for x,y,dwell_time in locations:
            print(self.name, x,y,dwell_time)
            
            if self.interrupt_measurement_called:
                break
            
            beam_hw.settings['x'] = x
            beam_hw.settings['y'] = y
            #beam_hw.settings['x'] = np.float64(x)
            #beam_hw.settings['y'] = np.float64(y)
            #beam_hw.settings['x'] = np.float64(x)
            #beam_hw.settings['y'] = np.float64(y)
            
            #time.sleep(1.0)
            
            t0 = time.time()
            
            while (time.time() - t0) < dwell_time:
                if self.interrupt_measurement_called:
                    break
                time.sleep(0.001)
           
        beam_hw.settings['x'] = -10.
        beam_hw.settings['y'] = -10.