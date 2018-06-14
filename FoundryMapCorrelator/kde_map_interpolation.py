'''
Created on May 16, 2018

@author: Edward Barnard
'''
from scipy.ndimage.filters import gaussian_filter
import numpy as np

def bilinear_weighted_map(shape, x,y,z):
    #z[n] is the data point at x[n],y[n]
    #shape: dimension of the desired interpolated data
    #    the indices become the new coordinates in units of the old 
    #    coordinates, 
    #make sure to work in units where the pair of new 
    #coordinates:
    #    i,j = floor(x[n]),floor(y[n]) is unique


    A=np.zeros(shape, dtype='float')

    for n in range(len(x)):
        i=int(np.floor(x[n]))
        j=int(np.floor(y[n]))
        dx=x[n]-i
        dy=y[n]-j
        A[j,i]+=(1-dx)*(1-dy)*z[n]
        A[j+1,i]+=(1-dx)*dy*z[n]
        A[j,i+1]+=(dx*(1-dy))*z[n]
        A[j+1,i+1]+=dx*dy*z[n]

    return A

def kde_map_interpolation(shape, x,y,z, sigma, r_threshold=1e-6):
    # map data to new new grid
    r_map = bilinear_weighted_map( shape, x,y,np.ones_like(x))
    z_r_map = bilinear_weighted_map( shape, x,y,z)
    # blur it    
    r_map_blur = gaussian_filter(r_map,sigma) #this is the contribution from the billinear map
    z_r_map_blur = gaussian_filter(z_r_map,sigma)   #data * bilinear map
    # get rid of contributions from bilinear functions.
    r_masked = np.ma.masked_less(r_map_blur, r_threshold)
    #r_masked = r_map_blur
    interp_map = z_r_map_blur/r_masked
    #r_map_blur[r_map_blur<=1e-12]=1
    #interp_map = z_r_map_blur/r_map_blur    
    return interp_map