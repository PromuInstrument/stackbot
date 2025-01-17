from ScopeFoundry import HardwareComponent

try:
    from equipment.NCEMscope import ScopeWrapper
except Exception as err:
    print "Cannot load required modules for em_hardware:", err
    
#-------------------------------------------------------------------------------
class EMHardwareComponent(HardwareComponent):
    
    #---------------------------------------------------------------------------
    def setup(self):
        self.debug_mode.update_value(True)
        self.name = "em_hardware"

        self.current_defocus = self.add_logged_quantity(
                        name = 'current_defocus',
                        dtype = float, fmt="%e", ro=False,
                        unit="nm",
                        vmin=-100,vmax=100)
        self.current_binning = self.add_logged_quantity(
                        name = 'current_binning',
                        dtype = int, fmt="%e", ro=False,
                        unit=None,
                        vmin=1,vmax=None)
        self.current_exposure = self.add_logged_quantity(
                        name = 'current_exposure',
                        dtype = float, fmt="%e", ro=False,
                        unit="s",
                        vmin=-1.0,vmax=100.0) 
        self.current_dwell = self.add_logged_quantity( #works with uS, equip converts
                        name = 'current_dwell', initial = 12.0,
                        dtype = float, fmt="%e", ro=False,
                        unit="us",
                        vmin=-1.0,vmax=100.0)
        self.current_tilt = self.add_logged_quantity(
                        name = 'current_tilt', initial = 80.0,
                        dtype = float, fmt="%e", ro=False,
                        unit='deg', vmin=-80.0,vmax=80.0)
        self.current_stem_rotation = self.add_logged_quantity(
                        name = 'current_stem_rotation',
                        dtype = float, fmt="%e", ro=False,
                        unit='deg', vmin=0.0,vmax=360.0)
        self.current_stem_magnification = self.add_logged_quantity(
                        name = 'current_stem_magnification',
                        dtype = float, fmt="%e", ro=False,
                        unit='deg', vmin=1,vmax=None)
        self.dummy_mode = self.add_logged_quantity(name='dummy_mode',
                            dtype=bool, initial=False, ro=False)    
            
        self.acquisition_mode = self.add_logged_quantity(name='acquisition_mode',
                            dtype = str, initial='',fmt="%s",unit=None,ro=False)          
    #---------------------------------------------------------------------------
    def connect(self):        
        if not self.dummy_mode.val:
            if self.debug_mode.val: print "Connecting to Scope"
            self.wrapper = ScopeWrapper(self.debug_mode.val)
            self.wrapper.Connect()
            
            #handy to have these references
            self.Scope = self.wrapper.Scope
            self.Acq = self.wrapper.Acq
            self.Ill = self.wrapper.Ill
            self.Proj = self.wrapper.Proj
            self.Stage = self.wrapper.Stage
            
            #set get and set functions for LQs
            self.acquisition_mode.hardware_read_func = \
                self.wrapper.getMode
            self.acquisition_mode.hardware_set_func = None

            self.current_defocus.hardware_read_func = \
                self.wrapper.getDefocus
            self.current_defocus.hardware_set_func = \
                self.wrapper.setDefocus       
                      
            self.current_tilt.hardware_read_func = \
                self.wrapper.getAlphaTilt
            self.current_tilt.hardware_set_func = \
                self.wrapper.setAlphaTilt
            
            self.current_binning.hardware_read_func = \
                self.wrapper.getBinning
            self.current_binning.hardware_set_func = \
                self.wrapper.setBinning  
                
            self.current_exposure.hardware_read_func = \
                self.wrapper.getExposure
            self.current_exposure.hardware_set_func = \
                self.wrapper.setExposure
                
            self.current_dwell.hardware_read_func = \
                self.wrapper.getDwellTime
            self.current_dwell.hardware_set_func = \
                self.wrapper.setDwellTime  
                
            self.current_stem_rotation.hardware_read_func = \
                self.wrapper.getStemRotation
            self.current_stem_rotation.hardware_set_func = \
                self.wrapper.setStemRotation
                     
            self.current_stem_magnification.hardware_read_func = \
                self.wrapper.getStemMagnification
            self.current_stem_magnification.hardware_set_func = \
                self.wrapper.setStemMagnification
                
            if self.wrapper.getMode() == 'STEM': self.stemSetup()
            if self.wrapper.getMode() == 'TEM': self.temSetup()
            self.read_from_hardware()
        else:
            if self.debug_mode.val: print "em_hardware: error while connecting"
    #---------------------------------------------------------------------------
    def disconnect(self):
        #disconnect logged quantities from hardware
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        self.wrapper = None 
     
    #---------------------------------------------------------------------------      
    def acquire(self):
        return self.wrapper.Acq.AcquireImages()
    
    #---------------------------------------------------------------------------      
    def setTemAcqVals(self,binning,exp):
        myCcdAcqParams = self.Acq.Cameras(0).AcqParams
        myCcdAcqParams.Binning = int(binning)
        myCcdAcqParams.ExposureTime = float(exp)
        myCcdAcqParams.ImageCorrection = self.wrapper.ACQIMAGECORRECTION_UNPROCESSED #this has to be unprocessed. Not sure if it affects data from the micoscope itself
        myCcdAcqParams.ImageSize = self.wrapper.ACQIMAGESIZE_FULL
        self.Acq.Cameras(0).AcqParams = myCcdAcqParams
        if self.debug_mode.val: print '-----set TEM vals-----'

    #---------------------------------------------------------------------------
    def setStemAcqVals(self,binning,dwell):
        self.myStemAcqParams = self.Acq.Detectors.AcqParams
        self.myStemAcqParams.Binning = int(bin)
        self.myStemAcqParams.DwellTime = float(dwell)
        self.Acq.Detectors.AcqParams = self.myStemAcqParams
        if self.debug_mode.val: print '-----set STEM vals-----'
        
    #---------------------------------------------------------------------------
    def stemSetup(self):
        if self.debug_mode.val: print 'em_hardware: stemSetup'
        self.mode = 'STEM'
        self.Det = self.wrapper.Det
        
    #---------------------------------------------------------------------------
    def temSetup(self):
        if self.debug_mode.val: print 'em_hardware: temSetup'
        self.mode = 'TEM'
        self.Cam = self.wrapper.Cam
        
    #---------------------------------------------------------------------------
    def setAlphaTilt(self,alpha):
        alpha = round(alpha,2)
        if self.debug_mode.val: print 'setting alpha tilt: ', alpha 
        self.wrapper.setAlphaTilt(alpha)
        
    #---------------------------------------------------------------------------
    def getAlphaTilt(self):
        return self.wrapper.getAlphaTilt()
    
    #---------------------------------------------------------------------------
    def moveStageXY(self,x,y):
        if self.debug_mode.val: print 'moving stage to: ('+str(x)+', '+str(y)+')'
        self.wrapper.setStageXY(x,y)    
        
    #---------------------------------------------------------------------------  
    def getStageXY(self):
        return self.wrapper.getStageXY()
    
    #---------------------------------------------------------------------------
    def getBinnings(self):
        if self.mode == 'TEM': return self.Cam.Info.Binnings
        if self.mode == 'STEM': return self.Det.Info.Binnings
        
    #---------------------------------------------------------------------------
    def setDefocus(self,defocus):
        self.wrapper.setDefocus(defocus)
        
    #---------------------------------------------------------------------------
    def getDefocus(self):
        return self.wrapper.getDefocus
    #---------------------------------------------------------------------------


