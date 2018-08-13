from ScopeFoundry import Measurement, h5_io
import numpy as np
import time

from scipy.signal import gaussian, convolve2d, medfilt
from scipy.ndimage.filters import gaussian_filter1d, median_filter

class SEMAutoStigMeasure(Measurement):
    
    
    name = 'sem_auto_stig'
    
    def setup(self):
        #self.settings
        self.settings.New("autostig_mode", dtype=str, initial='measure', choices=('measure','correct'))
        self.settings.New('df_lim', dtype=float, initial=0.005, vmin=0.)
        self.settings.New('df_num', dtype=int, initial=5, vmin=1)
        self.settings.New('stig_df', dtype=float, initial=0.004)
        self.settings.New('del_elip_goal',dtype=float, initial=0.1, vmin=0.)
        self.settings.New('max_evals', dtype=int, initial=3, vmin=0)


    def run(self):

        remcon = self.app.hardware['sem_remcon']
        
        # Read from hardware here so that current working distance, stigs, etc. are correct
        remcon.read_from_hardware()

        old_settings = dict()
        
        self.h5_file = h5_io.h5_base_file(self.app, measurement=self)
        
        try:        
            # Prepare SEM sync_raster_scan measurement
            self.sync_scan = sync_scan = self.app.measurements['sync_raster_scan']
            ## SAVE OLD SETTINGS HERE SO THEY CAN BE RESTORED AFTER routine 
            for lq_name in ['adc_oversample', 'save_h5', 'continuous_scan', 'n_frames', 'display_chan']:
                old_settings[lq_name] = sync_scan.settings[lq_name]

            sync_scan.settings['save_h5'] = False
            sync_scan.settings['continuous_scan'] = False
            sync_scan.settings['n_frames'] = 1
            sync_scan.settings['display_chan'] = 'adc1'
            sync_scan.read_from_hardware = False #Don't want to read from hardware before each "single scan"
            
            if self.settings['autostig_mode'] == 'measure':
                
                H = self.h5m = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5_file)
                h5_io.h5_create_measurement_group(measurement=sync_scan, h5group=self.h5_file)
                
                wd_cur = remcon.settings['WD'] # Gives value in mm
                
                H['defocus_range'] = np.linspace(-0.01,+0.01,5)
                
                #H['defocus_range'] = np.array([0.01])
                
                H['wd_range'] = np.array(H['defocus_range']) + wd_cur
    
                orig_stig_x, orig_stig_y = remcon.settings['stig_xy']
                
                images = []
                            
                H['dstig_x_array'] = np.linspace(-0.8,0.8, 9)
                H['dstig_y_array'] = np.linspace(-0.8,0.8, 9)
                
                H['stig_x_array'] = np.array(H['dstig_x_array']) + orig_stig_x
                H['stig_y_array'] = np.array(H['dstig_y_array']) + orig_stig_y
                            
                
                Nx = len(H['stig_x_array'])
                Ny = len(H['stig_y_array'])
                Nz = len(H['wd_range'])
                Nh = sync_scan.settings['Nh']
                Nv = sync_scan.settings['Nv']
    
                images_h5 = H.create_dataset(
                                    'images', 
                                    (Nz, Ny, Nx, Nv, Nh), dtype=float )
    
                for k in range(Nz):
                    remcon.settings['WD'] = H['wd_range'][k]
                    for j in range(Ny):
                        for i in range(Nx):
                            remcon.settings['stig_xy'] = [H['stig_x_array'][i], H['stig_y_array'][j]] 
                            
                            if self.interrupt_measurement_called:
                                break
                            t0 = time.time()
                            sync_scan._thread_run()
                            image = sync_scan.adc_map[0,:,:,1]
                            images_h5[k,j,i,:,:] = image
                            #images.append(image)
                        print("frame time:", time.time() - t0)
    
                #self.h5m['images'] = np.array(images)
                
            elif self.settings['autostig_mode'] == 'correct':
                
                df_lim = self.settings['df_lim']
                df_num = self.settings['df_num']
                df_range = np.linspace(-df_lim,+df_lim,df_num)
                
                wd_cur = remcon.settings['WD']
                wd_range = wd_cur + df_range
                
                stig_df = self.settings['stig_df']
                
                del_elip_goal = self.settings['del_elip_goal']
                max_evals = self.settings['max_evals']
                
                Nh = sync_scan.settings['Nh']
                Nv = sync_scan.settings['Nv']
                
                # Variables for FFT analysis
                # Initialize q matrix (assumes all images are of same shape)
                qy = np.fft.fftfreq(Nv)
                qx = np.fft.fftfreq(Nh)
                qxm, qym = np.meshgrid(qx, qy)
                qmag = np.sqrt(qxm**2 + qym**2)
                
                self.qxm = qxm
                self.qym = qym
                
                num_evals = 0
                del_elip_mag = np.infty
                
                # storing ffts 
                
                self.fft_stig_pair = []
                self.fft_stig_int = []
                self.fft_stig_bg = []
                
                # storing ellipticity values
                
                self.elip_tot_init = []
                self.elip_tot_stig = []
                self.elip_A_init = []
                self.elip_A_stig = []
                self.elip_B_init = []
                self.elip_B_stig = []
                
                # a stig-only mode so can not worry about defocus
                
                stig_only = True
                focus_only = False
                
                while (del_elip_mag > del_elip_goal) and (num_evals < max_evals):
                
                    if stig_only:
                        wd_opt = wd_cur
                    else:
                        ### Part 1. Optimize focus at current stigmation
                        
                        # Acquire images at varying defocus
                        images_df = np.zeros((df_num,Nv,Nh))
                        for idf in range(df_num):
                            remcon.settings['WD'] = wd_range[idf]
                            if self.interrupt_measurement_called:
                                break
                            t0 = time.time()
                            sync_scan._thread_run()
                            images_df[idf] = sync_scan.adc_map[0,:,:,1]
                        
                        if self.interrupt_measurement_called:
                            break
                        
                        # Analyze and determine optimum focus
                        # Initialize focus criteria matrix
                        q_exp = np.zeros(df_num)
                        for ind_foc in range(df_num):
                            # Subtract mean value from the image (DC component/brightness)
                            img = images_df[ind_foc]
                            img -= np.mean(img.ravel())
                            # Normalize by the contrast of the image (rms intensity)
                            int_rms = np.sqrt(np.mean(np.square(img)))
                            img /= int_rms
                            print('RMS intensity: ', int_rms)
                        
                            # FFT: Apply hann window, fft
                            hann = np.outer(np.hanning(img.shape[0]),np.hanning(img.shape[1]))
                            imfft = np.fft.fft2(img*hann)
                        
                            # Reduce intensity variation
                            I_real = np.abs(imfft) # first square to make all positive
                            I_real = I_real**0.1 # then take to 1/10 power to make features away from center significant
                            # 1/10 is an arbitrary choice, but could use fft intensity variation to determine reasonable power for 
                            # each case
                        
                            # Median filter
                            I_real = median_filter(I_real,size=5,mode='wrap')
                        
                            # KDE
                            bins_per_px = 50 # high density of bins needed to sort out subpixel differences in q
                            n_bins = int(bins_per_px*img.shape[0])
                            filt_stdev = 0.5 * bins_per_px #px
                            q_rad, I_rad = self.map_to_1D_KDE(qmag, I_real, n_bins, filt_stdev)
                        
                            # Discard the outer tenth because it's too noisy (only image corners contribute)
                            ind_crop = int(0.9*I_rad.shape[0])
                            q_rad = q_rad[:ind_crop]
                            I_rad = I_rad[:ind_crop]
                            # Subtract the background intensity (average from the new outer tenth)
                            ind_bg = int(0.9*I_rad.shape[0])
                            I_rad -= np.mean(I_rad[ind_bg:])
                        
                            # Intensity-weighted value (expectation value)
                            q_exp[ind_foc] = np.sum(q_rad*I_rad)/np.sum(I_rad)
                        
                        # Check expectation value of q stability
                        print('Q_exp % error: ', 100*np.std(q_exp)/np.mean(q_exp))
                            
                        # Determine WD of optimum focus and move there
                        X = np.array([df_range**2,df_range**1,df_range**0]).T
                        coefs,_,_,_ = np.linalg.lstsq(X,q_exp)
                        # Maximum of parabola ax^2 + bx + c = 0 is given by x = -(b/2a)
                        df_opt = -(coefs[1]/(2*coefs[0]))
                        wd_opt = wd_cur + df_opt
                        
                        print('\nExpectation value of q: ', q_exp)
                        print('Df array: ', df_range)
                        print('df_opt: ', -(coefs[1]/(2*coefs[0])))
                        print('Optimum WD: ', wd_opt)
                        
                        # Limit amount WD can shift in one iteration
                        if np.abs(wd_opt-wd_cur) > 0.1:
                            print('WD overshift!')
                            wd_opt = wd_cur + 0.1*np.sign(wd_opt-wd_cur)
                            print('new WD_opt: ', wd_opt)
                            
                        if self.interrupt_measurement_called:
                            break
                    
                    ### Part 2. Determine stigmation effect ###

                    # Algorithm parameters:
                    # - power to which FFT intensity is raised to reduce variations
                    # - amount of FFT safely considered "background" for mean subtraction (not a big deal, gets thresholded out anyway)
                    # - threshold percentile of the FFT
                    
                    if not(focus_only):
                        # Take an image at optimum WD and a defocused image
                        self.img_stig_pair = [np.zeros((Nv,Nh)),np.zeros((Nv,Nh))]
                        wd_stig = [wd_opt, wd_opt+stig_df]
                        for istig in range(2):
                            print('moving to WD: ', wd_stig[istig])
                            remcon.settings['WD'] = wd_stig[istig]
                            if self.interrupt_measurement_called:
                                break
                            t0 = time.time()
                            sync_scan._thread_run()
                            self.img_stig_pair[istig] = sync_scan.adc_map[0,:,:,1]
                        
                        if self.interrupt_measurement_called:
                            break
                        
                        elip = []
                        theta = []
                        # Compute ellipse angle and ellipticity in each case
                        for img in self.img_stig_pair:
                            # 1. FFT conditioning
                            
                            # Subtract mean value from the image (DC component)
                            img -= np.mean(img.ravel())
                            # Normalize by the contrast of the image (rms intensity)
                            int_rms = np.sqrt(np.mean(np.square(img)))
                            img /= int_rms
                        
                            # FFT: Apply hann window, fft
                            hann = np.outer(np.hanning(img.shape[0]),np.hanning(img.shape[1]))
                            imfft = np.fft.fft2(img*hann)
                        
                            # Reduce intensity variation
                            I_real = np.real(imfft)**2 # first square to make all positive
                            I_real = I_real**0.1 # then take to 1/10 power to make features away from center significant
                            # 1/10 is an arbitrary choice, but could use fft intensity variation to determine reasonable power for 
                            # each case
                            
                            self.fft_stig_int.append(I_real)
                        
                            # Median filter
                            I_real = median_filter(I_real,size=5,mode='wrap')
                        
                            # Subtract background
                            I_real -= np.mean(I_real[qmag>0.9*qmag.max()])
                            I_real[I_real<0] = 0
                            
                            self.fft_stig_bg.append(I_real)
                        
                            # Threshold so only low-to-mid spatial frequencies contribute to the pdf
                            thresh = np.percentile(I_real,95)
                            I_real[I_real<thresh]=0
                            
                            self.fft_stig_pair.append(I_real)
                        
                            # 2. Determining ellipse parameters
                        
                            pdf = I_real.ravel()
                            qxl = qxm.ravel()
                            qyl = qym.ravel()
                            _, sigma_x = self.weighted_avg_and_std(qxl[pdf>0],pdf[pdf>0])
                            _, sigma_y = self.weighted_avg_and_std(qyl[pdf>0],pdf[pdf>0])
                            covmat = np.cov(qxl[pdf>0], qyl[pdf>0])
                            corr = covmat[0,1]/np.sqrt(covmat[0,0]*covmat[1,1])
                        
                            # 2D Gaussian parameters
                            # = 1/(2*np.pi*sigma_x*sigma_y*np.sqrt(1-corr**2))
                            B = -1/(2*(1-corr**2)*sigma_x**2)
                            C = (2*corr)/(2*(1-corr**2)*sigma_x*sigma_y)
                            D = -1/(2*(1-corr**2)*sigma_y**2)
                        
                            # Converting gaussians to ellipses
                            theta.append(0.5 * (np.pi/2 - np.arctan2((B-D),C)))
                            lamb,_ = np.linalg.eig(np.array([[B,0.5*C],[0.5*C,D]]))
                            if (lamb[0]-B) <= (lamb[0]-D): # Ensure correct lambda ordering
                                elip.append(np.sqrt(lamb[1]/lamb[0]))
                            else:
                                elip.append(np.sqrt(lamb[0]/lamb[1]))
                        
                        # Move stigmation in appropriate direction based on angle of defocused ellipse and ellipticity change
                        # Can consider two cases, one where ellipticity at optimum focus is nearly circular and one where it is not
                        # In nearly circular case, can just look at ellipse angle of defocused ellipse and ellipticity change
                        # If not nearly circular, need to consider changes in ellipticity along independent xy and 45 deg axes
                        
                        # Angles correspond to stigmation as follows:
                        # Negative defocus: theta = 0 corresponds to -dstig_x
                        # theta = pi/4 corresponds to dstig_y
                        # theta = pi/2 corresponds to dstig_x
                        # theta = 3*(pi/4) corresponds to -dstig_y
                        # This means dstig_x = step*-np.cos(2*theta), dstig_y = step*np.sin(2*theta)
                        # Positive defocus will be flipped, so
                        # dstig_x = step*np.cos(2*theta), dstig_y = step*-np.sin(2*theta)
                        # These are approximate, hard to tell the exact angle to stig correspondence from the data
                        
                        step_stig = 0.0 # fraction of del_elip that will move in stig
                        
                        theta_tot = np.array(theta)
                        elip_tot = np.array(elip)
                        elip_A = np.sqrt((np.sin(theta_tot)**2 + elip_tot**2*np.cos(theta_tot)**2)
                                         /(np.cos(theta_tot)**2 + elip_tot**2*np.sin(theta_tot)**2))
                        elip_B = np.sqrt((1 + elip_tot**2 - (1-elip_tot**2)*np.sin(2*theta_tot))
                                         /(1 + elip_tot**2 + (1-elip_tot**2)*np.sin(2*theta_tot)))
                        del_elip_A = np.log2(elip_A[1]) - np.log2(elip_A[0])
                        del_elip_B = np.log2(elip_B[1]) - np.log2(elip_B[0])
                        del_elip_mag = np.sqrt(del_elip_A**2 + del_elip_B**2)
                        
                        # save ellipticity values for later analysis
                        self.elip_tot_init.append(elip_tot[0])
                        self.elip_tot_stig.append(elip_tot[1])
                        self.elip_A_init.append(elip_A[0])
                        self.elip_A_stig.append(elip_A[1])
                        self.elip_B_init.append(elip_B[0])
                        self.elip_B_stig.append(elip_B[1])
                        
                        print('\n Current ellipticity diff: ', del_elip_mag)
                        print('Total ellipticity (init,stig): ', np.log2(elip_tot))
                        print('Ellipse angle (init, stig): ', theta_tot)
                        print('Initial ellipticity (A,B): ', (np.log2(elip_A[0]), np.log2(elip_B[0])))
                        print('Change in ellipticity (delA, delB): ', (del_elip_A, del_elip_B))
                        
                        
                        del_stig_x = np.sign(stig_df)*step_stig*del_elip_A
                        del_stig_y = np.sign(stig_df)*step_stig*-del_elip_B
                        
                        print('Stig shift (x,y): ', del_stig_x, del_stig_y)
                        
                        if self.interrupt_measurement_called:
                            break
                        
                        # Move stigmators (note that += does not work on remcon settings)
                        remcon.settings['stig_xy'] = remcon.settings['stig_xy'] + [del_stig_x, del_stig_y]
                        print('New stig (x,y): ', remcon.settings['stig_xy'])
                    
                    num_evals += 1
                    
                    if self.interrupt_measurement_called:
                        break
                    
                    

        finally:
            if self.settings['autostig_mode'] == 'measure':
                self.h5_file.close()
                # restore SEM state here
                remcon.settings['WD'] = wd_cur
                remcon.settings['stig_xy'] = [orig_stig_x, orig_stig_y]
            else:
                remcon.settings['WD'] = wd_opt
                
            ## RESTORE SEM SYNC RASTER SETTINGS HERE ##
            for lq_name, val in old_settings.items():
                sync_scan.settings[lq_name] = old_settings[lq_name]
                sync_scan.read_from_hardware = True #restore so other sync scan measurements read



    def update_display(self):
        self.sync_scan.update_display()
    
    ### MATH/PROCESSING FUNCTIONS ###
    
    def map_to_1D_KDE(self, pos, I, n_bins, filt_stdev, filt_mode='constant', return_hists=False):
        # KDE method: bin pos values weighted by intensity I into a 1D histogram with evenly-spaced bins 
        # This gives summed intensity of each bin
        # Then, bin pos values without weight to get the number of points in each bin
        # Smooth both histograms with a gaussian kernel of "filt_stdev" 
        # Lastly, divide the intensity-weighted histogram by the num of points histogram
        # Returns mapped position and intensity arrays
        # 
        # input pos and I can have any shape so long as they match
        # TO DO: n_bins and filt_stdev must be input, but maybe can be predicted instead
        
        pos = pos.ravel()
        I = I.ravel()
        
        # compute weighted and unweighted histograms
        hist_Iwt, bin_edges = np.histogram(pos, n_bins, weights=I)
        hist_pos, _ = np.histogram(pos, n_bins)
        # convolve with gaussian kernels
        hist_Iwt_filt = gaussian_filter1d(hist_Iwt.astype(float), filt_stdev, mode=filt_mode)
        hist_pos_filt = gaussian_filter1d(hist_pos.astype(float), filt_stdev, mode=filt_mode)
        # divide histograms
        I_map = hist_Iwt_filt/hist_pos_filt
        pos_map = bin_edges[:-1]
        
        if return_hists:
            return pos_map, I_map, hist_pos, hist_Iwt, hist_pos_filt, hist_Iwt_filt
        else:
            return pos_map, I_map
    
    def weighted_avg_and_std(self, values, weights):
        """
        Return the weighted average and standard deviation.
    
        values, weights -- Numpy ndarrays with the same shape.
        """
        average = np.average(values, weights=weights)
        variance = np.average((values-average)**2, weights=weights)  # Fast and numerically precise
        return (average, np.sqrt(variance))