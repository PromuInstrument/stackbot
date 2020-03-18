import numpy as np
from scipy.ndimage.filters import gaussian_filter
from scipy.fftpack import fft2,ifft2
import numba
import time
import tensorflow as tf



@numba.jit()
def bilinear_weighted_map(shape, x, y, z):
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


def createfilterft(shape, sigma):
    xmin = 0
    xmax = shape[1]
    ymin = 0
    ymax = shape[0]
    x = np.arange(xmin, xmax)
    y = np.arange(ymin, ymax)
    X,Y = np.meshgrid(x,y)
    X0=(xmax-xmin)/2
    Y0=(xmax-xmin)/2
    
    gaussian = np.exp(-((X)**2+(Y)**2)/(2*sigma**2)) 
    
    filterft = np.fft.fft2(gaussian)
    
    return filterft


def fourier_filter(image, ft_filter):
        
    ft_image = np.fft.fft2(image)
    
    ft_filtered = ft_image*ft_filter
    
    filtered = np.fft.ifft2(ft_filtered) 
    
    return (abs(filtered))
   

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
        
        self.filterft = createfilterft(shape, sigma)
        
        
    
            
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
        
        print('time for interpolation', time.time()-t0)
        self.r_map += r_map
        self.z_r_map += z_r_map
        
        #t1 = time.time()
        #print("bilinear_weighted_map", t1-t0)

        # full gaussian blur        
        # r_map_blur = gaussian_filter(r_map,sigma)
        # z_r_map_blur = gaussian_filter(z_r_map,sigma)    
        # print("gaussian_filter", time.time()-t0)
        # self.r_map_blur += r_map_blur
        # self.z_r_map_blur += z_r_map_blur

        # reduced size blur
#         i0 = int(np.floor(max(0, np.min(x) - 2*sigma)))
#         i1 = int(np.ceil(min(self.shape[1], np.max(x)+2*sigma)))
#         j0 = int(np.floor(max(0, np.min(y) - 2*sigma)))
#         j1 = int(np.ceil(min(self.shape[0], np.max(y)+2*sigma)))
#         
        r_map_blur_new = fourier_filter (r_map, self.filterft)
        z_r_map_blur_new = fourier_filter (z_r_map, self.filterft)
        
        print('time for filtering', time.time()-t0)
        
        self.r_map_blur += r_map_blur_new
        self.z_r_map_blur += z_r_map_blur_new
        
        #print("gaussian_filter", time.time()-t0)
                
        r_masked = np.ma.masked_less(self.r_map_blur, self.r_threshold)
        
        self.data = (self.z_r_map_blur/r_masked)
        
        print('time for add point', time.time()-t0)
        
    
   
        
    
    def recompute_data(self,sigma=None):
        if sigma is None:
            sigma = self.sigma
        
        self.r_map_blur = gaussian_filter(self.r_map,sigma)
        self.z_r_map_blur = gaussian_filter(self.z_r_map,sigma)    

        r_masked = np.ma.masked_less(self.r_map_blur, self.r_threshold)
        self.data = self.z_r_map_blur/r_masked
        