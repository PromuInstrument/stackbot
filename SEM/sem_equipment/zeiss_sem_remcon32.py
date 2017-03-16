'''
Created on Feb 5, 2015

@author: Hao Wu, In process for python 3 Frank 3/15/17

### NOT DONE

Communicating with RemCon32 on the SEM computer through RS232 Serial communcation
'''
import serial
import numpy as np
import time



class ZeissSEMRemCon32(object):
    
    def __init__(self, port='COM4',debug=False):
        '''
        The serial setting has to be exact the same as the setting on the RemCon32 Console
        '''
        self.port=port
        self.ser = serial.Serial(port=self.port, baudrate=9600, 
                                 bytesize= serial.EIGHTBITS, 
                                 parity=serial.PARITY_NONE, 
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=0.1)
    
    def send_cmd(self,cmd):
        self.ser.write(cmd)
    
    def write_cmd(self,cmd):
        #self.ser.flushInput()
        self.send_cmd(cmd)
        resp=self.ser.readlines()
        return self.conv_resp(resp)
    
    def conv_resp(self,resp):
        '''
        The response from RemCon comes in two lines, first line
        shows the status of the task '@' for success or '#' for failure,
        second line contains '>' followed by the parameter or error number
        '''
        #print(resp)
        cmd_status=resp[0][0]
        success=resp[1][0]
        if cmd_status==ord(b'@'):
            if success==ord(b'>'):
                if (len(resp[1])>3):
                    #output the requested value, if any
                    return resp[1][1:-2]
            else:
                if (len(resp[1])>3):
                    raise ValueError("Did not complete. Error Code: %s" % resp[1][1:-2])
                else:
                    raise ValueError("Did not complete")
        else:
            raise ValueError("Your RemCon32 command is invalid. Error Code: %s" % resp[1][1:-2])
        
        '''
        Below is a list of wrappers
        '''
    '''
    6 7 EHT
    '''
    def read_EHT(self):
        return self.write_cmd(b'EHT?\r')
    
    def write_EHT(self,val):
        return self.write_cmd(b'EHT %f\r' % val)

    
    '''
    8 Electron Gun Status
    '''
    def read_gun(self):
        return self.write_cmd(b'GUN?\r')
    
    '''
    9 10 Beam Blanking
    '''
    def read_beam_blanking(self):
        return self.write_cmd(b'BBL?\r')
    
    def write_beam_blanking(self,val):
        if val==0 or val==1:
            return self.write_cmd(b'BBLK %i\r' % val)
        else:
            raise ValueError("blanking state %s instead of 0, or 1" % val)
    
    '''
    12 Set Gun tilt
    '''
    
#     def write_gun_tilt(self,val):
#         if val>=-1.0 and val<=1.0:
#             return self.write_cmd('GTLT %f\r' % val)
#         else:
#             raise ValueError("value %s out of range [-1.00,1.00]" % val)
        
    '''
    13 Set Gun shift
    '''
    
#     def write_gun_shift(self,val):
#         if val>=-1.0 and val<=1.0:
#             return self.write_cmd('GSHF %f\r' % val)
#         else:
#             raise ValueError("value %s out of range [-1.00,1.00]" % val)       

    '''
    17 18 Scan Rate
    '''
    def read_scan_rate(self):
        return self.write_cmd(b'RAT?\r')
    
    def write_scan_rate(self,val):
        if val>=0 and val<=15:
            return self.write_cmd(b'RATE %i\r' % val)
        else:
            raise ValueError("value %s out of range [0,15]" % val)  
        
    '''
    24 92 Stigmator
    '''
    def _read_stigmator(self):
        return self.write_cmd(b'STI?\r')
    
    def _write_stigmator(self,x_val,y_val):
            return self.write_cmd(b'STIM {} {}/r'.format(x_val, y_val))
        
    def _read_stigmator_array(self):
        return np.fromstring(self._read_stigmator(),sep=' ')
    
    def read_stigmatorX(self):
        return self._read_stigmator_array()[0]
    
    def read_stigmatorY(self):
        return self._read_stigmator_array()[1]
    
    def write_stigmatorX(self,val):
        if (val>=-100.0 and val<=100.0):
            stig=self._read_stigmator_array()
            self._write_stigmator(val,stig[1])
        else:
            raise ValueError("value out of range [-100,100]" )  
        
    def write_stigmatorY(self,val):
        if (val>=-100.0 and val<=100.0):
            stig=self._read_stigmator_array()
            self._write_stigmator(stig[0],val)
        else:
            raise ValueError("value out of range [-100,100]" )  
    '''
     27 28 Brightness
    '''
    def read_brightness(self):
        return self.write_cmd(b'BGT?\r')
    
    def write_brightness(self,val):
        if val>=0.0 and val<=100.0:
            return self.write_cmd(b'BRGT %f\r' % val)
        else:
            raise ValueError("value %s out of range [0.0,100.0]" % val)  
        
    '''
   29 30 Brightness
    '''
    def read_contrast(self):
        return self.write_cmd(b'CST?\r')
    
    def write_contrast(self,val):
        if val>=0.0 and val<=100.0:
            return self.write_cmd(b'CRST %f\r' % val)
        else:
            raise ValueError("value %s out of range [0.0,100.0]" % val)  
     
    '''
    35 Magnification
    '''
    def read_magnification(self):
        return self.write_cmd(b'MAG?\r')
    
    def write_magnification(self, val):
        return self.write_cmd(b'MAG %f\r' % val)
    
    '''
    37 38 WD
    '''
    def read_WD(self):
        return self.write_cmd(b'FOC?\r')
    
    def write_WD(self,val):
        if val>=0.0 and val<=121.0:
            return self.write_cmd(b'FOCS %f\r' % val)
        else:
            raise ValueError("value %s out of range [0.0,121.0]" % val)  
        
    '''
    69 External Scan
    '''
    def read_external_scan(self):
        return self.write_cmd(b'EXS?\r')
    
    def write_external_scan(self,val):
        if val==1:
            return self.write_cmd('EDX %i\r' % val)
        if val==0:
            self.send_cmd('EDX %i\r' % val)
        else:
            raise ValueError("value %s out of range [0,10]" % val)  
        
    '''
    70 77 Probe Current
    '''
    def read_probe_current(self):
        return self.write_cmd('PRB?\r')
    
    def write_probe_current(self,val):
        if val>=1.0e-14 and val<=2.0e-5:
            return self.write_cmd('PROB %f\r' % val)
        else:
            raise ValueError("value %s out of range [1.0e-14,2.0e-5]" % val)  
        
    '''
    74 75 Select Aperture
    '''
    def read_select_aperture(self):
        return self.write_cmd('APR?\r')
    
    def write_select_aperture(self,val):
        if val>=1 and val<=6:
            return self.write_cmd('APER %i\r' % val)
        else:
            raise ValueError("value %s out of range [1,6]" % val)  
        
    def turn_EHT(self,val):
        if val>=1 and val<=2:
            return self.write_cmd('BMON %i\r' % val)
        else:
            raise ValueError("value %s out of range [1,6]" % val)  
        
    def read_EHT_status(self):
        value=float(self.read_EHT())
        if value==0:
            return 2
        else:
            return 1
#     '''
#     43 Spot Mode
#     '''
#     def write_spot_mode(self,x_val,y_val):
#         if ((x_val>=0 and x_val<1024) and (y_val>=0 and y_val<768)):
#             return self.write_cmd('SPOT '+str(x_val)+' ' +str(y_val) +'\r' )
#         else:
#             raise ValueError("value out of range 1024x768" )  
#         
#     '''
#     44 Line Profile Mode
#     '''
#     def write_line_mode(self,val):
#         if val>=0 and val<=767:
#             return self.write_cmd('LPR %i\r' % val)
#         else:
#             raise ValueError("value %s out of range [0,767]" % val)  
#     
#     '''
#     45 Normal Mode
#     '''
#     def write_normal_mode(self):
#         return self.write_cmd('NORM\r')
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
       
    def read_stage_xyz(self):
        return self.write_cmd(b'STG?\r')
    
    def read_stage_x(self):
        current_pos=self.write_cmd('STG?\r').split(' ')
        time.sleep(0.05)
        return current_pos[0]
    
    def read_stage_y(self):
        current_pos=self.write_cmd('STG?\r').split(' ')
        time.sleep(0.05)
        return current_pos[1]
    
    def read_stage_z(self):
        current_pos=self.write_cmd('STG?\r').split(' ')
        time.sleep(0.05)
        return current_pos[2]
    
    def write_stage_x(self,x):
        current_pos_string=self.read_stage_xyz()
        time.sleep(0.05)
        current_pos=current_pos_string.split(' ')
        if len(current_pos)==4:
            y=current_pos[1]
            z=current_pos[2]
            pos=str(x)+' '+str(y)+' '+str(z)
            time.sleep(0.05)
            self.send_cmd('STG '+pos+'\r')
            time.sleep(0.2)
    
    def write_stage_y(self,y):
        current_pos_string=self.read_stage_xyz()
        time.sleep(0.05)
        current_pos=current_pos_string.split(' ')
        if len(current_pos)==4:
            x=current_pos[0]
            z=current_pos[2]
            pos=str(x)+' '+str(y)+' '+str(z)
            time.sleep(0.05)
            self.send_cmd('STG '+pos+'\r')
            time.sleep(0.2)
            
    def read_stage_all(self):
        '''
        output: x y z t r m move_status
        '''
        return self.write_cmd('c95?\r')
        
    def write_detector(self,val):
        self.write_cmd('DET '+val+'\r')
        
    def read_detector(self):
        return self.write_cmd(b'DET?\r')
    
    def close(self):
        self.ser.close()
     
'''
Test Cases
'''   

if __name__=='__main__':    
    rem=ZeissSEMRemCon32()
    resp=rem.write_stage_x(55)
    #resp=rem.write_stage_xyz(60,60)
    #resp=rem.read_stage_xyz()
    #resp=rem.write_cmd('BMON 2\r')
    print(resp)
#     resp=rem.read_stage_cords_array()
#     print('read_stage_cord_array:'+str(resp))
#     resp=rem.read_stage_status()
#     print('read stage_status:'+str(resp))
#     resp=rem.read_stage_x()
#     print('read stage_x:'+str(resp))
#     resp=rem.read_stage_y()
#     print('read stage_y:'+str(resp))
#     resp=rem.read_stage_z()
#     print('read stage_z:'+str(resp))
#     resp=rem.read_stage_tilt()
#     print('read stage_t:'+str(resp))
#     resp=rem.read_stage_rotation()
#     print('read stage_r:'+str(resp))
#     resp=rem.read_stage_m()
#     print('read stage_m:'+str(resp))
