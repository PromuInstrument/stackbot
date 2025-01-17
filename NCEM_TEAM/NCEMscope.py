'''
Created on Oct 13, 2015
ScopeFoundry Equipment Module for FEI Microscope (STEM/TEM)

@author: Zach
'''

import win32com.client
import pythoncom
from math import degrees,radians
#-------------------------------------------------------------------------------
class ScopeWrapper(object):
    #---------------------------------------------------------------------------
    def __init__(self,debug=True):       
        self.debug                  = debug  
        self.Scope                  = None
        self.Acq                    = None
        self.Cam                    = None
        self.Det                    = None
        
    #---------------------------------------------------------------------------
    def Connect(self):
        #connect to TEMScripting wrapper
        self.Scope = win32com.client.Dispatch('TEMScripting.Instrument')
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        if self.debug: print("Connected to microscope")
        
        #connect to TIA
        self.TIA = win32com.client.Dispatch("ESVision.Application")
        if self.debug: print("Connected to TIA")  
        
        #get aliases
        self.Acq = self.Scope.Acquisition
        self.Proj = self.Scope.Projection
        self.Ill = self.Scope.Illumination 
        self.Stage = self.Scope.Stage
        
        #Get the default state values
        self.ACQIMAGECORRECTION_DEFAULT         = win32com.client.constants.AcqImageCorrection_Default
        self.ACQIMAGECORRECTION_UNPROCESSED     = win32com.client.constants.AcqImageCorrection_Unprocessed
        
        self.ACQIMAGESIZE_FULL                  = win32com.client.constants.AcqImageSize_Full
        self.ACQIMAGESIZE_HALF                  = win32com.client.constants.AcqImageSize_Half
        self.ACQIMAGESIZE_QUARTER               = win32com.client.constants.AcqImageSize_Quarter
        
        self.ACQIMAGEFILEFORMAT_TIFF            = win32com.client.constants.AcqImageFileFormat_TIFF
        self.ACQIMAGEFILEFORMAT_JPG             = win32com.client.constants.AcqImageFileFormat_JPG
        self.ACQIMAGEFILEFORMAT_PNG             = win32com.client.constants.AcqImageFileFormat_PNG
       
        #get the mode, ensure set up
        mode = self.Scope.InstrumentModeControl.InstrumentMode
        if mode == 0: self.TEMMODE()
        if mode == 1: self.STEMMODE()  
           
    #--------------------------------------------------------------------------- 
    def getMode(self):
        mode = self.Scope.InstrumentModeControl.InstrumentMode
        if mode == 0: self.mode = 'TEM'
        if mode == 1: self.mode = 'STEM'
        return self.mode
        
    #---------------------------------------------------------------------------
    def TEMMODE(self):
        self.mode = 'TEM'
        self.Acq.RemoveAllAcqDevices()
        self.Cam = self.Acq.Cameras(0)
        self.Acq.AddAcqDevice(self.Cam)
        self.Cam.AcqParams.ImageCorrection = self.ACQIMAGECORRECTION_UNPROCESSED #this has to be unprocessed. Not sure if it affects data from the micoscope itself
        self.Cam.AcqParams.ImageSize = self.ACQIMAGESIZE_FULL  
        if self.debug: print("Scope is TEM Mode")  
    
    #---------------------------------------------------------------------------
    def STEMMODE(self):
        self.mode = 'STEM'
        self.Acq.RemoveAllAcqDevices()
        self.Det = self.Acq.Detectors(0)
        self.Acq.AddAcqDevice(self.Det)
        if self.debug: print("Scope is STEM Mode")  
    
    #--------------------------------------------------------------------------- 
    def getBinning(self):
        if self.mode == 'TEM': return self.Cam.AcqParams.Binning
        if self.mode == 'STEM': return self.Acq.Detectors.AcqParams.Binning
        if self.debug: print("getting bin")
        
    #---------------------------------------------------------------------------
    def setBinning(self,binning):
        if self.mode == 'TEM': self.Cam.AcqParams.Binning = int(binning)
        if self.mode == 'STEM': self.Acq.Detectors.AcqParams.Binning = int(binning)
        if self.debug: print("setting bin")
    
    #---------------------------------------------------------------------------
    def getDwellTime(self):
        if self.mode == 'TEM': return -1
        if self.mode == 'STEM': return self.Acq.Detectors.AcqParams.DwellTime/1e-6
        if self.debug: print("getting dwell")
        
    #---------------------------------------------------------------------------
    def setDwellTime(self,dwell):
        if self.mode == 'STEM':
            dwell *= 1e-6
            self.Acq.Detectors.AcqParams.DwellTime = float(dwell)
            if self.debug: print 'setting dwell:', dwell
            
    #---------------------------------------------------------------------------
    def getExposure(self):
        if self.mode == 'TEM': return self.Cam.AcqParams.ExposureTime
        if self.mode == 'STEM': return -1.0
        if self.debug: print("getting exp")
  
    #---------------------------------------------------------------------------
    def setExposure(self,exposure):
        if self.mode == 'TEM': 
            self.Cam.AcqParams.ExposureTime = float(exposure)
            if self.debug: print("setting exp")   
            if self.debug: print 'exp:', exposure 
        
    #---------------------------------------------------------------------------
    def getDefocus(self):
        return self.Proj.Defocus*1e9
        if self.debug: print("getting def")
    #---------------------------------------------------------------------------
    def setDefocus(self,defocus):
        self.Proj.Defocus = float(defocus*1e-9)
        if self.debug: print "setting def", defocus    
         
    #---------------------------------------------------------------------------
    def getAlphaTilt(self):
        return self.Stage.Position.A
        if self.debug: print("getting alphatilt")
        
    #---------------------------------------------------------------------------
    def setAlphaTilt(self,alpha):
#         position = self.Stage.Position
#         position.A = alpha
#         self.Stage.Goto(position,8) 
        if self.debug: print "setting alphatilt", alpha  

        
    #---------------------------------------------------------------------------
    def getStageXY(self):
        return [self.Stage.Position.X,self.Stage.Position.Y]
        if self.debug: print("getting stagex")
        
    #---------------------------------------------------------------------------
    def setStageXY(self,x,y):
#         position = self.Stage.Position
#         position.X = x
#         position.Y = y
#         self.Stage.Goto(position,3) 
        if self.debug: print "moving stage: ",'(',x,', ',y,')'
        
    #--------------------------------------------------------------------------
    def getStemRotation(self):
        rtrn = round(degrees(self.Ill.StemRotation),2)
        if rtrn<0: rtrn += 360.0
        return rtrn
        if self.debug: print("getting rotation")
        
    #--------------------------------------------------------------------------
    def setStemRotation(self,rot):
        if rot<0: rot += 360.0
        if self.debug: print "moving stemRot: ",rot,' deg'
        if self.debug: print "moving stemRot: ",radians(rot),' rad'
        self.Ill.StemRotation = float(radians(rot))

    #--------------------------------------------------------------------------
    def getStemMagnification(self):
        return self.Ill.StemMagnification
        if self.debug: print("getting stem mag")
        
    #--------------------------------------------------------------------------
    def setStemMagnification(self,mag):
        if self.debug: print "setting stem mag: ",mag
        self.Ill.StemMagnification = float(mag)
        
    #--------------------------------------------------------------------------

    
    