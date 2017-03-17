'''
Created on Feb 5, 2015

@author: Hao Wu, 
Significant changes for python 3 Frank 3/15/17
Thicker wrapper, some commands left out on purpose (gun off for example)
'''
import serial
import numpy as np
import time



class Remcon32(object):
    
    #direct serial communications++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    def __init__(self, port='COM4',debug=False):
        '''
        The serial setting has to be exact the same as the setting on the RemCon32 Console
        '''
        self.timeout = 0.050    #should be long enough for readlines() to get all output
        self.port=port
        self.ser = serial.Serial(port=self.port, baudrate=9600, 
                                 bytesize= serial.EIGHTBITS, 
                                 parity=serial.PARITY_NONE, 
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=self.timeout)
    
    def close(self):
        self.ser.close()
        
    def write_cmd(self,cmd):
        'sends bytestring, not unicode, text to Remcon32, appends terminating CR'
        cmd = cmd.encode('utf-8') + b'\r'
        #print(cmd)
        self.ser.write(cmd)
    
    def cmd_response(self,cmd):
        #self.ser.flushInput()
        self.write_cmd(cmd)
        response=self.ser.readlines()
        return self.parse_response(response)
    
    def set_timeout(self, timeout):
        self.timeout = timeout
        self.ser.timeout = self.timeout
        
    def limits(self, x, xmin=-100.0, xmax=100.0):
        'force value between limits, many params +- 100'
        return min( xmax, max(xmin, x))
           
    # Zeiss SEM communications++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    def parse_response(self,response):
        '''
        The response from RemCon comes in two lines, first line
        shows the status of the task '@' for success or '#' for failure,
        second line contains '>' for success or '*' for failure
        followed by any returned data or the error number
        
        usually works in 50 ms, sometimes late, FIX if return data fails, should try again with delay
        '''
        #print(response)
        short_response = False
        if len(response) > 0:
            cmd_status=response[0][0]
        else:
            short_response = True
            cmd_status = ''
        if len(response) > 1:
            cmd_info=response[1][0]
        else:
            short_response = True
            cmd_info=''

        if short_response:
            print('remcon32 error: not enough return data', response)
            self.reset_input_buffer()                            
        elif cmd_status==ord(b'@'):
            if cmd_info==ord(b'>'):
                if (len(response[1])>3):
                    #output the requested value, if any, always single line
                    return response[1][1:-2]
            else:
                raise ValueError("Did not complete. " % response)
        else:
            print('remcon32 error:', response)
            raise ValueError("Your RemCon32 command is invalid.") 
        
 
    '''
    SEM kV, EHT, blanking++++++++++++++++++++++++++++++++++++++++++++++++++
    '''
    def get_kV(self):
        'gets actual, not requested, value, may be delayed for change kV or EHT on'
        return float(self.cmd_response('EHT?'))
    
    def set_kV(self,val):
        'command returns immediately, EHT may take several seconds to reach new value'
        'success returns None, system does not echo command'
        val = min(val, 20.0)
        return self.cmd_response('EHT %f' % val)
    
    def eht_state(self,state=True):
        if state:
            return self.cmd_response('bmon 1') #turns on EHT, also gun if off
        else:
            return self.cmd_response('bmon 2') #turns off EHT, gun stays on
        
    def get_eht_state(self):
        kV = self.get_kV()
        if kV > 0:
            return True
        return False

    def blank_state(self,state=True):
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
        'select aperture, fails for Auger'
        val = int(self.limits(val,1,6))
        return self.cmd_response('aper %i' % val)
        
    def get_ap(self):
        'value for current selected aperture'
        resp = self.cmd_response('apr?')
        return int(resp)
        
    def set_ap_align(self,x_val,y_val):
        'value for current selected aperture'
        x_val = self.limits( x_val)
        y_val = self.limits( y_val)
        return self.cmd_response('aaln {} {}'.format(x_val, y_val))
        
    def get_ap_align(self):
        'value for current selected aperture'
        resp = self.cmd_response('aln?')
        return np.fromstring(resp,sep=' ')
        
    def set_gun_align(self,x_val,y_val):
        'value for current selected aperture'
        x_val = self.limits( x_val)
        y_val = self.limits( y_val)
        return self.cmd_response('galn {} {}'.format(x_val, y_val))
        
#    CAN SET BUT NOT READ...
#    def get_gun_align(self):
#        'value for current selected aperture'
#        resp = self.cmd_response('gal?')
#        return np.fromstring(resp,sep=' ')
#    
    def scm_state(self,state=True):
        'specimen current monitor, when on touch alarm disabled'
        'when off, 10 v bias on sample'
        if state:
            return self.cmd_response('scm 1') #ext scan
        else:
            return self.cmd_response('scm 0') 

    def get_scm(self):
        'in amps'
        return str(self.cmd_response('prb?'),'utf-8')


    '''
    detectors and signals++++++++++++++++++++++++++++++++++++
    '''
    def select_main_display(self,state=True):
        'not for Auger, maybe not others'
        if state:
            return self.cmd_response('disp 0') #primary display
        else:
            return self.cmd_response('disp 1')
        
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
    
    def set_norm(self):
        'makes scanning "normal" ie both unfrozen, non spot'
        return self.cmd_response('norm')
        
    '''
    imaging++++++++++++++++++++++++++++++++++++++++++
    '''   
   
    def extscan_state(self,state=True):
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
   
#     '''
#     43 Spot Mode
#     '''
#     def set_spot_mode(self,x_val,y_val):
#         if ((x_val>=0 and x_val<1024) and (y_val>=0 and y_val<768)):
#             return self.cmd_response('SPOT '+str(x_val)+' ' +str(y_val) +'\r' )
#         else:
#             raise ValueError("value out of range 1024x768" )  
#         
#     '''
#     44 Line Profile Mode
#     '''
#     def set_line_mode(self,val):
#         if val>=0 and val<=767:
#             return self.cmd_response('LPR %i\r' % val)
#         else:
#             raise ValueError("value %s out of range [0,767]" % val)  
#     
#     '''
#     45 Normal Mode
#     '''
#     def set_normal_mode(self):
#         return self.cmd_response('NORM\r')
#     
#     '''
#     58 59 Stage Control
#     x 0.0-152mm
#     y 0.0-152mm
#     z 0.0-40mm
#     t 0.0-90 degrees
#     r 0.0-360 degrees
#     m 0.0-10.0 degrees
#     '''
       
    def set_stage_x(self,x):
        current_pos_string=self.get_stage_xyz()
        time.sleep(0.05)
        current_pos=current_pos_string.split(' ')
        if len(current_pos)==4:
            y=current_pos[1]
            z=current_pos[2]
            pos=str(x)+' '+str(y)+' '+str(z)
            time.sleep(0.05)
            self.send_cmd('STG '+pos+'\r')
            time.sleep(0.2)
    
    def set_stage_y(self,y):
        current_pos_string=self.get_stage_xyz()
        time.sleep(0.05)
        current_pos=current_pos_string.split(' ')
        if len(current_pos)==4:
            x=current_pos[0]
            z=current_pos[2]
            pos=str(x)+' '+str(y)+' '+str(z)
            time.sleep(0.05)
            self.send_cmd('STG '+pos+'\r')
            time.sleep(0.2)
            
    def get_stage_all(self):
        '''
        output: x y z t r m move_status
        '''
        return self.cmd_response('c95?\r')
        
     
