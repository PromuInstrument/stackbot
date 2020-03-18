from ScopeFoundryHW.sync_stream_scan.sync_stream_scan import SyncStreamScan
import numpy as np
import pyqtgraph as pg
import time
#from .kde_interp_fft import KDE_Image
#from ScopeFoundry import h5_io
from ScopeFoundryHW.sync_stream_scan.kde_interp import kde_map_interpolation,\
    KDE_Image

class LJScan(SyncStreamScan):

    name = 'lj_scan'

    def setup(self):
        
        self.settings.New('image_size_x', dtype=int, initial=1000)
        self.settings.New('image_size_y', dtype=int, initial=1000)
        self.settings.New('amplitude_x', dtype=float, initial=5.0)
        self.settings.New('amplitude_y', dtype=float, initial=5.0)
        self.settings.New('kde_sigma', dtype=float, initial=2)              
        self.settings.New('ni_device', dtype=str, initial='X-6363') #dev2
        self.settings.New('do_chan', dtype=str, initial='port0/line0:3')
        self.settings.New('di_chan', dtype=str, initial='port0/line4:7')
        self.settings.New('ao_chan', dtype=str, initial='ao0:1')
        self.settings.New('ai_chan', dtype=str, initial='ai1:2')
        
        self.settings.New('freq', dtype=float, initial=30.0)
        self.settings.New('freq_ratio', dtype=float, initial=np.sqrt(2))
        
        # KDE Interp
        self.kde_img = None


    def setup_figure(self):
        
        self.ui = self.graph_layout = pg.GraphicsLayoutWidget()
        self.graph_layout.clear()


    def on_start_of_run(self):
        img_shape = (self.settings['image_size_x'],self.settings['image_size_y'])
        self.r_map= np.zeros(img_shape, dtype=np.float)
        self.z_r_map = np.zeros(img_shape, dtype=np.float)
        self.img = np.zeros(img_shape, dtype=np.float)
        self.i_processed = 0        

        Nx=self.settings['image_size_x']
        Ny=self.settings['image_size_y']

        #KDE interp (it overwrites the one created in setup())
        self.kde_img = KDE_Image((Ny,Nx), self.settings['kde_sigma'])


    def handle_new_data(self):
        SyncStreamScan.handle_new_data(self)

        if self.ai_data_h5.shape[0] > self.i_processed:

            Nx=self.settings['image_size_x']
            Ny=self.settings['image_size_y']
            Ax=self.settings['amplitude_x']
            Ay=self.settings['amplitude_y']
                                        
            x = self.ao_data_h5[self.i_processed: self.i_processed + self.N_ao, 0]
            y = self.ao_data_h5[self.i_processed: self.i_processed + self.N_ao, 1]    
            #we are choosing here analog input channel 0 as signal
            z = self.ai_data_h5[self.i_processed: self.i_processed + self.N_ai, 0]

            # Quick interpolation
            x_img=np.uint32((Nx-1)/2*x/Ax+(Nx)/2)
            y_img=np.uint32((Ny-1)/2*y/Ay+(Ny)/2)
#             for ii in range(0,len(x), 100):
#                 #self.img[x_img[ii],y_img[ii]]+=z[ii]
#                 self.counts[x_img[ii],y_img[ii]]+=1
#                 cc=self.counts[x_img[ii],y_img[ii]]
#                 old_z=self.img[x_img[ii],y_img[ii]]
#                 new_z=(old_z*(cc-1)+z[ii])/cc
#                 self.img[x_img[ii],y_img[ii]]=new_z
#                  
            bins = [np.arange(Nx+1), np.arange(Ny+1)]
            self.r_map += np.histogram2d(x=x_img, y=y_img, bins=bins)[0]
            self.z_r_map += np.histogram2d(x=x_img, y=y_img, bins=bins, weights=z)[0]
            #self.img = self.z_r_map/self.r_map
            #self.img = np.nan_to_num(self.img)

            #x_img=(Nx-1)/2*x/Ax+(Nx)/2
            #y_img=(Ny-1)/2*y/Ay+(Ny)/2
        
            #self.img = kde_map_interpolation(self.img.shape, 
            #                                 x=x_img, y=y_img, z=z, sigma=2.0)
            self.kde_img.add_datapoints(x=x_img, y=y_img, z=z)
            self.img = self.kde_img.data
            
            self.i_processed += self.N_ao

            ### KDE
    #                     x_img=(Nx-1)/2*x/Ax+(Nx)/2
    #                     y_img=(Ny-1)/2*y/Ay+(Ny)/2
    #                     
    #                     x_img = np.clip(x_img, 4, Nx-4)
    #                     y_img = np.clip(y_img, 4, Ny-4)
    #                     
    #                     t0=time.time()    
    #                     #self.kde_img.add_datapoints(x_img, y_img,z)
    #                     print('Elapsed time for adding chunk to image:', round(time.time()-t0,3))


        
    # run during callback
    def ao_stream_gen(self, t):
        print("ao_stream_gen",t[0], t[-1])
        S = self.settings
        ao_stream = np.zeros((len(t), self.ao_chan_count), dtype=float)
        ao_stream[:,0] = S['amplitude_x']*np.sin(S['freq']*t*np.pi/0.5)
        ao_stream[:,1] = S['amplitude_y']*np.cos(S['freq']*S['freq_ratio']*t*np.pi/0.5)
        return ao_stream

    def update_display(self):
        
        t0 = pg.ptime.time()
        
        
        if self.first_display:
            ## Create a PlotItem in the remote process that will be displayed locally
            #self.plot = rplt = self.remote_graphics_view.pg.PlotItem()
            #rplt._setProxyOptions(deferGetattr=True)  ## speeds up access to rplt.plot
            #self.remote_graphics_view.setCentralItem(rplt)
            
            self.graph_layout.clear()

            self.plot_lines = dict()
            
            self.do_plot = self.graph_layout.addPlot(0,0)
            #self.do_plot.show()
            self.ao_plot = self.graph_layout.addPlot(1,0)
            
            self.di_plot = self.graph_layout.addPlot(2,0)
            self.ai_plot = self.graph_layout.addPlot(3,0)
            
            self.plot2d = self.graph_layout.addPlot(0,1, rowspan=2)
            self.plot2d.setAspectLocked(1)
            
            self.pos_plotline = self.plot2d.plot()

            self.plotimg = self.graph_layout.addPlot(2,1, rowspan=2)
            self.img_item = pg.ImageItem()
            self.plotimg.setAspectLocked(1)
            self.plotimg.addItem(self.img_item)
            
            for i in range(self.do_chan_count):
                self.plot_lines['do{}'.format(i)] = self.do_plot.plot()#autoDownsample=True, downsampleMethod='subsample', autoDownsampleFactor=1.0)
            for i in range(self.ao_chan_count):
                self.plot_lines['ao{}'.format(i)] = self.ao_plot.plot()#autoDownsample=True, downsampleMethod='subsample', autoDownsampleFactor=1.0)
            for i in range(self.di_chan_count):
                self.plot_lines['di{}'.format(i)] = self.di_plot.plot()
            for i in range(self.ai_chan_count):
                self.plot_lines['ai{}'.format(i)] = self.ai_plot.plot()
                
            self.first_display = False
        
        for i in range(self.do_chan_count):
            self.plot_lines['do{}'.format(i)].setData(self.do_i_array, i+self.do_data[:,i], autoDownsample=True, downsampleMethod='mean', autoDownsampleFactor=1.0, pen=i)

        for i in range(self.ao_chan_count):
            self.plot_lines['ao{}'.format(i)].setData(self.ao_i_array, self.ao_data[:,i], autoDownsample=True, downsampleMethod='mean', autoDownsampleFactor=1.0, pen=i)

        for i in range(self.di_chan_count):
            self.plot_lines['di{}'.format(i)].setData(self.di_i_array, i+self.di_data[:,i], autoDownsample=True, downsampleMethod='mean', autoDownsampleFactor=1.0, pen=i)

        for i in range(self.ai_chan_count):
            self.plot_lines['ai{}'.format(i)].setData(self.ai_i_array, self.ai_data[:,i], autoDownsample=True, downsampleMethod='mean', autoDownsampleFactor=1.0, pen=i)

        
        self.pos_plotline.setData(self.ao_data[:,0], self.ao_data[:,1])
        
        self.img_item.setImage(self.img)
        
        print("update_display", pg.ptime.time()-t0)


