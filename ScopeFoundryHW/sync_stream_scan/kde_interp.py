import numpy as np
from scipy.ndimage.filters import gaussian_filter
#import numba
import time


def bilinear_weighted_map_slow(shape, x, y, z):
    '''
    ======== ========================================================
    z        1D array of data points
    x        1D array of x-coordinates  
    y        1D array of y-coordinates
    shape    2-tuple. min('x'), min('y') must be 
             greater than 0, floor(max('y'), max('x')) <= shape
             to work properly
    
    returns: 2D map of shape 'shape'. 
    ======== ========================================================
    projects z(x,y) onto a new grid of shape 'shape'
    '''

    A = np.zeros(shape, dtype='float')

    for n in range(len(x)):
        i = int(np.floor(x[n]))
        j = int(np.floor(y[n]))
        dx = x[n] - i
        dy = y[n] - j
        A[j, i] += (1 - dx) * (1 - dy) * z[n]
        A[j + 1, i] += (1 - dx) * dy * z[n]
        A[j, i + 1] += (dx * (1 - dy)) * z[n]
        A[j + 1, i + 1] += dx * dy * z[n]

    return A

def bilinear_weighted_map(shape, x,y,z):
    A = np.zeros(shape, dtype='float')
    
    i = np.floor(x)
    j = np.floor(y)
    dx = x - i
    dy = y - j
    
    bins = [np.arange(shape[0]+1), np.arange(shape[1]+1)]
    
    A += np.histogram2d(x=i, y=j, bins=bins, weights=(1 - dx) * (1 - dy) * z)[0]
    A += np.histogram2d(x=i, y=j+1, bins=bins, weights=(1 - dx) * dy * z)[0]
    A += np.histogram2d(x=i+1, y=j, bins=bins, weights=(dx * (1 - dy)) * z)[0]
    A += np.histogram2d(x=i+1, y=j+1, bins=bins, weights= dx * dy * z)[0]
    
    return A


def kde_map_interpolation(shape, x, y, z, sigma, r_threshold=1e-6):
    # map data to new new grid
    r_map = bilinear_weighted_map(shape, x, y, np.ones_like(x)) # density map
    z_r_map = bilinear_weighted_map(shape, x, y, z)
    # blur it    
    r_map_blur = gaussian_filter(r_map, sigma)  # this is the contribution from the density map
    z_r_map_blur = gaussian_filter(z_r_map, sigma)  # data * density map
    r_masked = np.ma.masked_less(r_map_blur, r_threshold)
    # get rid of contributions from bilinear functions.
    interp_map = z_r_map_blur / r_masked
    return interp_map

    
class KDE_Image(object):
    """
    A class to store and build a KDE (kernel density estimation) image from a set of 
    datapoints.
        
    Example:

        import scipy.misc
        import matplotlib.pyplot as plt

        orig_img = scipy.misc.face(gray=True)
        x = np.arange(orig_img.shape[1])
        y = np.arange(orig_img.shape[0])
        X, Y = np.meshgrid(x,y)
    
        k = KDE_Image((10000,10000),sigma=1.0)
        x,y,z = X.flatten()+1, Y.flatten()+1,orig_img.flatten()
        k.add_datapoints(x,y,z)
    
        plt.figure()
        plt.imshow(k.data[:2000,2000])
    
        k.recompute_data(sigma=7)
        plt.figure()
        plt.imshow(k.data[:2000,2000])
    """
    
    def __init__(self,shape, sigma=1.0,r_threshold=1e-6):
        
        self.shape = shape
        self.sigma = sigma
        self.r_threshold = r_threshold
        
        self.r_map = np.zeros(shape,dtype=float)
        self.z_r_map = np.zeros(shape,dtype=float)

        self.r_map_blur = np.zeros(shape,dtype=float)
        self.z_r_map_blur = np.zeros(shape,dtype=float)
        
        self.data = np.zeros(shape,dtype=float)
        
    def add_datapoints(self,x,y,z,sigma=None):
        """
        x,y are a flat arrays of coordinates (x,y)
        z is a flat array of values z(x,y)
        
        sigma is the gaussian kernel size, defaults
        to size specified during initialization
        
        Note: x and y value are pixel values that must be > 0 and less than shape
        """
        t0=time.time()
        
        shape = self.shape
        if sigma is None:
            sigma = self.sigma
        
        #t0 = time.time()
        
        
        r_map = bilinear_weighted_map( shape, x,y,np.ones_like(x))
        z_r_map = bilinear_weighted_map( shape, x,y,z)
        
        self.r_map += r_map
        self.z_r_map += z_r_map
        
        #t1 = time.time()
        #print("bilinear_weighted_map", t1-t0)
        print('time for interpolation', time.time()-t0)
        
        # full gaussian blur        
        # r_map_blur = gaussian_filter(r_map,sigma)
        # z_r_map_blur = gaussian_filter(z_r_map,sigma)    
        # print("gaussian_filter", time.time()-t0)
        # self.r_map_blur += r_map_blur
        # self.z_r_map_blur += z_r_map_blur

        # reduced size blur
        i0 = int(np.floor(max(0, np.min(x) - 2*sigma)))
        i1 = int(np.ceil(min(self.shape[1], np.max(x)+2*sigma)))
        j0 = int(np.floor(max(0, np.min(y) - 2*sigma)))
        j1 = int(np.ceil(min(self.shape[0], np.max(y)+2*sigma)))
        
        r_map_blur_new = gaussian_filter(r_map[j0:j1,i0:i1], sigma)
        z_r_map_blur_new = gaussian_filter(z_r_map[j0:j1,i0:i1], sigma)
        
        self.r_map_blur[j0:j1,i0:i1] += r_map_blur_new
        self.z_r_map_blur[j0:j1,i0:i1] += z_r_map_blur_new
        
        #print("gaussian_filter", time.time()-t0)
        print('time for filtering', time.time()-t0)
        
        r_masked = np.ma.masked_less(self.r_map_blur[j0:j1,i0:i1], self.r_threshold)
        
        self.data[j0:j1,i0:i1] = (self.z_r_map_blur[j0:j1,i0:i1]/
                                    r_masked)
        print('time for add point', time.time()-t0)
        
        
    def recompute_data(self,sigma=None):
        if sigma is None:
            sigma = self.sigma
        
        self.r_map_blur = gaussian_filter(self.r_map,sigma)
        self.z_r_map_blur = gaussian_filter(self.z_r_map,sigma)    

        r_masked = np.ma.masked_less(self.r_map_blur, self.r_threshold)
        self.data = self.z_r_map_blur/r_masked
        