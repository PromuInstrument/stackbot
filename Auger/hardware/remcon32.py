'''
Created on Feb 5, 2015

@author: Frank Ogletree, based on earlier version of Hao Wu
Significant changes for python 3 Frank 3/15/17
Thicker wrapper, some commands left out on purpose (gun off for example)
'''
import serial
import numpy as np
import time
from sympy.physics.units import current

class Remcon32(object):
    
    #direct serial communications, Zeiss Remcon32 response parsing++++++++++++++++++++++++++++++++
    
    def __init__(self, port='COM4',debug=False):
        '''
        The serial setting has to be exact the same as the setting on the RemCon32 Console
        '''
        self.timeout = 0.50    #readline called twice, timeout only for comm errors
        self.port=port
        self.ser = serial.Serial(port=self.port, baudrate=9600, 
                                 bytesize= serial.EIGHTBITS, 
                                 parity=serial.PARITY_NONE, 
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=self.timeout)
    
    def close(self):
        self.ser.close()
        
    def write_cmd(self,cmd):
        #sends bytestring, not unicode, text to Remcon32, appends terminating CR
        cmd = cmd.encode('utf-8') + b'\r'
        #print(cmd)
        self.ser.write(cmd)
        
        
    

    remcon_error = {600: 'Unknown command',
                    601: 'Invalid number of parameters',
                    602: 'Invalid parameter type',
                    603: 'Parameter out of range',
                    604: 'Command timeout',
                    605: 'Catastrophic error - reboot system',
                    611: 'Unexpected external control abort',
                    613: 'Parameter Unattainable',
                    614: 'Option Not Fitted',
                    615: 'Cannot change that parameter',
                    616: 'Cannot execute that command',
                    617: 'Command exceeded the max length of chars'}
    
    def cmd_response(self,cmd,error_ok=False):
        '''
        sends bytestring terminated by \r to Remcon32 program, parses return values
        some commands like read scm return errors if the scm is off, likewise out of range arguments
            if error_ok is set, this info returned instead of throwing errors
        '''
        self.ser.reset_input_buffer()    #clear any leftover stuff
        cmd = cmd.encode('utf-8') + b'\r'
        self.ser.write(cmd)

        r1 =self.ser.readline() #is '@\r\n' for success or '#\r\n' for failure
        r2 =self.ser.readline() 
        #is '>[data]\r\n' for success or '* errnum\r\n' for failure
        #[data] may be empty for set commands, returns info for get

        if ( (len(r1)<1) or (r1[0]!=ord(b'@')) or (len(r2)<1) or (r2[0]!=ord(b'>')) ):
            if error_ok:
                return r2
            elif r2[0]==ord(b'*'):
                key = int(r2[1:-2])
                print( 'remcon error ', key, self.remcon_error[key])
                return r2
            else:
                print('remcon32 error, command:', cmd, r1, r2)
                return
        
        if len(r2) > 3:
            #return data, if any, always single line
            return r2[1:-2]
        
    def limits(self, x, xmin=-100.0, xmax=100.0):
        #force value between limits, many params +- 100
        return min( xmax, max(xmin, x))

    '''
    SEM kV, EHT, blanking++++++++++++++++++++++++++++++++++++++++++++++++++
    '''
    def get_kV(self):
        #gets actual, not requested, value, may be delayed for change kV or EHT on
        return float(self.cmd_response('EHT?'))
    
    def set_kV(self,val):
        #command returns immediately, EHT may take several seconds to reach new value
        #success returns None, system does not echo command
        val = min(val, 30.0)
        return self.cmd_response('EHT %f' % val)
    
    def set_eht_state(self,state=True):
        if state:
            return self.cmd_response('bmon 1') #turns on EHT, also gun if off
        else:
            return self.cmd_response('bmon 2') #turns off EHT, gun stays on
        
    def get_eht_state(self):
        kV = self.get_kV()
        if kV > 0:
            return True
        return False

    def set_blank_state(self,state=True):
        if state:
            return self.cmd_response('bblk 1') #blanks beam
        else:
            return self.cmd_response('bblk 0') 
        
    def get_blank_state(self):
        return bool(int(self.cmd_response('bbl?')))

    '''
    Lens colunm control, aperture, stig, gun etc++++++++++++++++++++++++++++++++++++
    '''
    def set_stig(self,x_val,y_val):
        x_val = self.limits( x_val)
        y_val = self.limits( y_val)
        return self.cmd_response('stim {} {}'.format(x_val, y_val))
        
    def get_stig(self):
        resp = self.cmd_response('sti?')
        return np.fromstring(resp,sep=' ')
        
    def set_ap(self,val):
        #select aperture, fails for Auger
        val = int(self.limits(val,1,6))
        return self.cmd_response('aper %i' % val)
        
    def get_ap(self):
        #value for current selected aperture
        resp = self.cmd_response('apr?')
        return int(resp)
        
    def set_ap_align(self,x_val,y_val):
        #value for current selected aperture'
        x_val = self.limits( x_val)
        y_val = self.limits( y_val)
        return self.cmd_response('aaln {} {}'.format(x_val, y_val))
        
    def get_ap_align(self):
        #value for current selected aperture'
        resp = self.cmd_response('aln?')
        return np.fromstring(resp,sep=' ')
        
    def set_gun_align(self,x_val,y_val):
        #value for current selected aperture'
        x_val = self.limits( x_val)
        y_val = self.limits( y_val)
        return self.cmd_response('galn {} {}'.format(x_val, y_val))
    
    def set_beam_shift(self,x,y):
        #this command +- 1 instead of +- 100%...'
        x = self.limits(x)/100.0
        y = self.limits(y)/100.0
        return self.cmd_response('BEAM {} {}'.format(x,y))
        
#    CAN SET BUT NOT READ...
#    def get_gun_align(self):
#        'value for current selected aperture'
#        resp = self.cmd_response('gal?')
#        return np.fromstring(resp,sep=' ')
#    
    def scm_state(self,state=True):
        #specimen current monitor, when on touch alarm disabled'
        #when off, 10 v bias on sample'
        if state:
            return self.cmd_response('scm 1') #ext scan
        else:
            return self.cmd_response('scm 0') 

    def get_scm(self):
        #in amps
        #this command fails if SCM is off
        value = str(self.cmd_response('prb?',error_ok=False),'utf-8')
        try:
            current = float(value)
        except ValueError:
            current = 0.0
        return current
        


    '''
    detectors and signals++++++++++++++++++++++++++++++++++++
    '''
    def display_focus_state(self,state=True):
        'this controls which display gets/sets brightness, contrast, detector...'
        'missing from remcon, do with macros'
        if state:
            self.run_macro(2) # 'Zone = 0'
        else:
            self.run_macro(3) # 'Zone = 1'
    
    def set_dual_channel(self):
        self.run_macro(1) # 'DualMonitor = On'

        
    def set_bright(self,val=50):
        'this actually sets voltage offset of detector output, best 50% neutral for quantitative data'
        'for currently selected display'
        val = self.limits(val,0,100)
        return self.cmd_response('bgtt %f' % val)
    
    def get_bright(self):
        return float(self.cmd_response('bgt?'))
    
    def set_contrast(self,val=50):
        'this actually sets electron multiplier gain/voltage'
        'for currently selected display'
        val = self.limits(val,0,100)
        return self.cmd_response('crst %f' % val)
    
    def get_contrast(self):
        'of active display, which cannot be set'
        return float(self.cmd_response('cst?'))

    def get_detector(self):
        'for currently selected display'
        return str(self.cmd_response('det?'),'utf-8')
        
    def set_detector(self, name):
        'for currently selected display'
        return self.cmd_response('det %s' % name)
    
    def run_macro(self,n):
        'runs macro REMCONn in SmartSem, macro must exist or error'
        'fill in for missing commands'
        return self.cmd_response('mac %i' % n)
   
    def set_norm(self):
        'makes scanning "normal" ie both unfrozen, non spot'
        return self.cmd_response('norm')
        
    def set_sem_scanning(self,state=True):
        '(re)starts scan, unfreezes'
        'this controls which display gets/sets brightness, contrast, detector...'
        if state:
            return self.cmd_response('disp 0') #primary display
        else:
            return self.cmd_response('disp 1')
    '''
    imaging++++++++++++++++++++++++++++++++++++++++++
    '''   
   
    def set_extscan_state(self,state=True):
        if state:
            return self.cmd_response('edx 1') #ext scan
        else:
            return self.cmd_response('edx 0') 
        
    def get_extscan_state(self):
        return bool(int(self.cmd_response('exs?')))
   
    def set_mag(self,val=500):
        val = self.limits(val,5,5e5)
        return self.cmd_response('mag %f' % val)
    
    def get_mag(self):
        return float(self.cmd_response('mag?'))
   
    def set_wd(self,val=9.2):
        'in mm, max depends on voltage where obj lens current goes to zero'
        val = self.limits(val,0.0,50.0)
        return self.cmd_response('focs %f' % val)
    
    def get_wd(self):
        return float(self.cmd_response('foc?'))
   
    def get_pixel_nm(self):
        'may depend on image resolution settings...1024 assumed?'
        return float(self.cmd_response('pix?'))
   
    def set_spot_mode(self,x_val,y_val):
        x_val = int(self.limits(x_val,0,1023))
        y_val = int(self.limits(y_val,0,767))
        return self.cmd_response('spot {} {}'.format(x_val, y_val))
    
    '''
    stage control (not for Auger)+++++++++++++++++++++++++++++++++++++++++++++
    '''
       
    def get_stage_position(self):
        'for 5/6 axis stage, last param is 1.0 in motion, 0.0 done'
        resp = self.cmd_response('c95?')
        return np.fromstring(resp,sep=' ') #array of 7 floats

    def set_stage_position(self, x, y, z, rot, tilt=0):
        'error if out of physical limits, can be dangerous'
        state = self.get_scm()
        self.scm_state(False)   #turn off scm so touch alarm works!
        cmd = 'c95 {} {} {} {} {} 0.0'.format(x,y,z,tilt,rot)
        resp = self.cmd_response(cmd)
        if type(resp) is float:
            self.scm_state(True) #restore scm if it returned a numerical value (else error string)
        return resp
        
        
     
