'''
Created on Jun 29, 2017

@author: Daniel Durham
'''
from ScopeFoundry import Measurement
import pyqtgraph as pg
import numpy as np
import time
from scipy.optimize import curve_fit
from qtpy import QtWidgets

class SEMAutoFocus(Measurement):
    
    name = "SEMAutoFocus"
    
    def setup(self):
        
        #Settings for auto-focus parameters
        self.settings.New('num_frames', dtype = int, initial=20, vmin=1)
        self.settings.New('wd_min', dtype = float, initial=9.8, vmin=0.0, unit='mm')
        self.settings.New('wd_max', dtype = float, initial=10.0, vmin=0.0, unit='mm')
        self.settings.New('fft_lpf_px', dtype=float, initial=50.0, vmin=1.0, unit='px')
        self.settings.New('adc_oversample', dtype=int, initial=10, vmin=1, unit='x')

    def setup_figure(self):
        
        self.ui = QtWidgets.QWidget()
        self.layout = QtWidgets.QGridLayout()
        self.ui.setLayout(self.layout)
        self.start_button= QtWidgets.QPushButton("Start")
        self.layout.addWidget(self.start_button)
        self.stop_button= QtWidgets.QPushButton("Stop")
        self.layout.addWidget(self.stop_button)
        
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.interrupt)
        
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.layout.addWidget(self.graph_layout)
        
        labelStyle = {'color': '#A9A9A9', 'font-size': '11pt'}
        
        self.plots = self.graph_layout.addPlot(title='Score function vs. working distance')
        self.plot_score_line = self.plots.plot([], pen=None, symbol = 'x')
        self.plot_fit_line = self.plots.plot([], pen=pg.intColor(1))
        self.plot_opt_val = self.plots.plot([], pen=None, symbol='o')
        self.axis_vert = self.plots.getAxis('left')
        self.axis_vert.setLabel(text='Expectation value of fourier wave vector (1/px)', **labelStyle)
        self.axis_horz = self.plots.getAxis('bottom')
        self.axis_horz.setLabel(text='Working Distance (mm)', **labelStyle)
        
        #Initialize data to be plotted
        self.plot_data = [0]
        self.plot_horz = [0]
        
        self.image_layout = pg.ImageView()
        self.layout.addWidget(self.image_layout)
        # self.image_view = self.image_layout.getView()
        
        
        self.ui.show()
        self.ui.setWindowTitle("SEMAutoFocus")
    
    def run(self):
        # print("="*80)

        ## Analysis preparation
        # build q vector array
        imshape_v = self.app.measurements['sync_raster_scan'].settings['Nv']
        imshape_h = self.app.measurements['sync_raster_scan'].settings['Nh']
        qy = np.fft.fftfreq(imshape_v)
        qx = np.fft.fftfreq(imshape_h)
        [qxa, qya] = np.meshgrid(qx, qy)
        q_mag = np.sqrt(qxa**2 + qya**2)
        qx_step = qxa[0,1]-qxa[0,0]
        qy_step = qya[1,0]-qya[0,0]
        
        # Hann window to image to avoid edge artifacts
        win = np.outer(np.hanning(imshape_v),np.hanning(imshape_h))
        
        range_px = self.settings['fft_lpf_px']
        # Working distances over which to image
        wd = np.linspace(self.settings['wd_min'], self.settings['wd_max'], 
                         self.settings['num_frames'])
        
        # Preallocate score and fourier amplitude arrays
        score = np.zeros(self.settings['num_frames'])
        amp_weighted = np.zeros((self.settings['num_frames'], imshape_v, imshape_h))
        
        # Prepare plot window
        self.plot_score_line.setData([])
        self.plot_fit_line.setData([])
        self.plot_opt_val.setData([])
        
        # Prepare SEM viewing screen
        sync_scan = self.app.measurements['sync_raster_scan']
        ## NEED TO SAVE OLD SETTINGS HERE SO THEY CAN BE RESTORED AFTER AUTOFOCUSING, 
        ## e.g. if creating a long sync_raster_scan movie but interrupting to autofocus
        wd_orig = self.app.hardware['sem_remcon'].settings['WD']
        sync_scan.settings['adc_oversample'] = self.settings['adc_oversample']
        sync_scan.settings['save_h5'] = False
        sync_scan.settings['continuous_scan'] = False
        sync_scan.settings['n_frames'] = 1
        sync_scan.settings['display_chan'] = 'adc_1'
        
        # Perform measurement and calculate scoring functions on the fly
        for imNum in range(0,self.settings['num_frames']):
            
            ## ACQUIRE IMAGE HERE ##
            self.app.hardware['sem_remcon'].settings['WD'] = wd[imNum]
            sync_scan.run()
            image = sync_scan.adc_map[0,:,:,1]
            
            G = np.fft.fft2(image*win) # Fourier transform
            amp = np.abs(G) # Amplitude distribution
            # Expectation value of wave vector (q)
            amp_weighted[imNum] = amp*q_mag*self.gauss_2d(qxa,qya,qx_step*range_px,qy_step*range_px)
            score[imNum] = np.sum(amp_weighted[imNum])/np.sum(amp)
            
            # Update q plot
            self.plot_score_line.setData(wd, score)
            # Display the current fft plot
            self.image_layout.setImage(np.fft.fftshift(amp_weighted[imNum]**0.04))
        
        # Calculate the optimal working distance by fitting a gaussian + background
        # p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
        p0 = [np.max(score)-np.min(score), wd[np.argmax(score)], 0.01, np.min(score)] # standard deviation probably similar order from image to image
        coeff, var_matrix = curve_fit(self.gauss, wd, score, p0=p0)
        # Get the fitted curve
        try: 
            wd_upsamp = np.linspace(np.min(wd), np.max(wd), self.settings['num_frames'] * 20)
            score_fit = self.gauss(wd_upsamp, *coeff)
            self.plot_fit_line.setData(wd_upsamp, score_fit)
            opt_fit = self.gauss(opt_wd, *coeff)
            self.plot_opt_val.setData([coeff[1]], [opt_fit])
        except RuntimeError:
            opt_wd = wd_orig
            print('Gaussian fit failed... original working distance maintained')
        
        ## RESTORE SEM SYNC RASTER SETTINGS HERE ##
        if (opt_wd > np.min(wd)) & (opt_wd < np.max(wd)):
            self.app.hardware['sem_remcon'].settings['WD'] = opt_wd
        else:
            self.app.hardware['sem_remcon'].settings['WD'] = wd_orig
            print('Estimated optimum outside of measurement range')
            # In the future, this may become adjustment of WD measurement range
        
    def gauss_2d(self, x, y, sigma_x, sigma_y):
        # 2d gaussian function
        return np.exp(-1*((x**2/sigma_x**2)+(y**2/sigma_y**2)))
    
    def gauss(self, x, *p):
            A, mu, sigma, C = p
            return A*np.exp(-(x-mu)**2/(2.*sigma**2)) + C    
        