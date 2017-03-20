'''
Created on Feb 4, 2015

@author: Hao Wu, modified by Frank Ogletree
'''

'remote control of Zeiss Gemini SEM using the Remcon32 serial interface'

from ScopeFoundry import HardwareComponent
from Auger.hardware.remcon32 import Remcon32


REMCON_PORT='COM4' #default value

class SEM_Remcon_HW(HardwareComponent):
    
    name = 'sem_remcon'
     
    def setup(self):
        self.name='sem_remcon'
        self.debug='false'
        #create logged quantities
        
        
        self.settings.New('kV', dtype=float, initial=3.0,unit = 'kV',vmin=0,vmax = 30.0)
        #+- 10 V dac output moves within "size" box determined by mag, calculate mag with pixel size
        self.settings.New('size',dtype=float, initial=100e-6,unit = 'm',si=True,vmin=1e-9,vmax =3e-3)
        
        '''
        
        bool.....
            EHT on
            Beam blank
            ext scan
            SCM
       
        chan 0/1
            detector, contrast, brightness
        
        gun xy; stig xy; app xy; beam_shift xy; 
        WD
        SCM current
        
        stage xyzrt
        
        self.settings.New('ke_steps', dtype=int, initial=10,vmin=1)
        self.settings.New('dwell', dtype=float, initial=0.05,unit = 's', si=True,vmin=1e-4)
        self.settings.New('pass_energy', dtype=float, initial=50,unit = 'V', vmin=5,vmax=500)
        self.settings.New('crr_ratio', dtype=float, initial=5, vmin=1.5,vmax=20)
        self.settings.New('CAE_mode', dtype=bool, initial=False)

        '''
        
        
        
        
        self.magnification = self.add_logged_quantity('magnification', 
                                                   dtype=float,
                                                   ro=False,
                                                   vmin=5.0,
                                                   vmax=5.0e5,
                                                   unit='x')
        self.EHT = self.add_logged_quantity('EHT', 
                                                   dtype=float,
                                                   ro=False,
                                                   vmin=0.0,
                                                   vmax=40.0,
                                                   unit='kV')
        
#         self.beam_status = self.add_logged_quantity('beam_status', 
#                                                    dtype=int,
#                                                    ro=False,
#                                                    vmin=1,
#                                                    vmax=2,
#                                                    unit='',
#                                                    choices=[('EHT Off',2),('EHT On',1)])
        
        self.beam_blanking = self.add_logged_quantity('beam_blanking', 
                                                   dtype=int,
                                                   ro=False,
                                                   vmin=0,
                                                   vmax=1,
                                                   unit='',
                                                   choices=[('Off',0),('On',1)])
        
        self.stigmatorX = self.add_logged_quantity('stigmatorX', 
                                                   dtype=float,
                                                   ro=False,
                                                   vmin=-100.0,
                                                   vmax=100.0,
                                                   unit='%')
         
        self.stigmatorY = self.add_logged_quantity('stigmatorY', 
                                                   dtype=float,
                                                   ro=False,
                                                   vmin=-100.0,
                                                   vmax=100.0,
                                                   unit='%')
          
        self.WD = self.add_logged_quantity('WD', 
                                                   dtype=float,
                                                   ro=False,
                                                   vmin=0.0,
                                                   vmax=121.0,
                                                   unit='mm')
        
        self.detector=self.add_logged_quantity(name='detector',
                                               dtype=str,
                                               ro=False,
                                               initial='SE2',
                                               choices=[('SE2','SE2'),('VPSE','VPSE'),('InLens','InLens')])
         
        self.stage_x=self.add_logged_quantity(name='stage_x',
                                               dtype=float,
                                               ro=False,
                                               vmin=5.0,
                                               vmax=95.0,
                                               initial=50,
                                               unit='mm')
         
        self.stage_y=self.add_logged_quantity(name='stage_y',
                                               dtype=float,
                                               ro=False,
                                               vmin=5.0,
                                               vmax=95.0,
                                               initial=50,
                                               unit='mm')
         
        self.stage_z=self.add_logged_quantity(name='stage_z',
                                               dtype=float,
                                               ro=False,
                                               vmin=0.0,
                                               vmax=25.0,
                                               initial=1.0,
                                               unit='mm')
        
#         self.probe_current = self.add_logged_quantity('probe_current', 
#                                                    dtype=float,
#                                                    ro=False,
#                                                    vmin=1.0e-14,
#                                                    vmax=2.0e-5,
#                                                    unit='A')
#         
#         
        aperture_choices=list([('[1] 30.00 um',1),
                               ('[2] 10.00 um',2),
                               ('[3] 20.00 um',3),
                               ('[4] 60.00 um',4),
                               ('[5] 120.00 um',5),
                               ('[6] 300.00 um',6)])
           
        self.select_aperture = self.add_logged_quantity('select_aperture', 
                                                   dtype=int,
                                                   ro=True,
                                                   vmin=1,
                                                   vmax=6,
                                                   unit='',
                                                   choices=aperture_choices)
        
        self.external_scan = self.add_logged_quantity('external_scan', 
                                                   dtype=int,
                                                   ro=False,
                                                   vmin=0,
                                                   vmax=1,
                                                   unit='',
                                                   choices=[('Off',0),('On',1)])
        
        
        #connect to GUI
        if False:
            self.magnification.connect_bidir_to_widget(self.gui.ui.sem_magnification_doubleSpinBox)
            self.beam_blanking.connect_bidir_to_widget(self.gui.ui.beam_blanking_checkBox)
            '''
        
    def connect(self):
        if self.debug: print "connecting to REMCON32"
        '''
        #connecting to hardware
        self.remcon=ZeissSEMRemCon32(REMCON_PORT)
        
        #connect logged quantity
        self.magnification.hardware_read_func= \
                self.remcon.read_magnification
        self.magnification.hardware_set_func= \
                self.remcon.write_magnification
        
        self.EHT.hardware_read_func= \
                self.remcon.read_EHT
        self.EHT.hardware_set_func= \
                self.remcon.write_EHT
        
        self.beam_blanking.hardware_read_func=\
                self.remcon.read_beam_blanking
        self.beam_blanking.hardware_set_func= \
                self.remcon.write_beam_blanking
        
        self.stigmatorX.hardware_read_func=\
                self.remcon.read_stigmatorX
        self.stigmatorX.hardware_set_func= \
                self.remcon.write_stigmatorX
                
        self.stigmatorY.hardware_read_func=\
                self.remcon.read_stigmatorY
        self.stigmatorY.hardware_set_func= \
                self.remcon.write_stigmatorY
        
        self.WD.hardware_read_func=\
                self.remcon.read_WD
        self.WD.hardware_set_func= \
                self.remcon.write_WD
                
#         self.probe_current.hardware_read_func=\
#                 self.remcon.read_probe_current
#         self.probe_current.hardware_set_func= \
#                 self.remcon.write_probe_current
                
        self.select_aperture.hardware_read_func=\
                self.remcon.read_select_aperture
        self.select_aperture.hardware_set_func= \
                self.remcon.write_select_aperture
                
        
        self.external_scan.hardware_read_func=\
                self.remcon.read_external_scan
        self.external_scan.hardware_set_func= \
                self.remcon.write_external_scan
        
#         self.beam_status.hardware_set_func=\
#                 self.remcon.turn_EHT
#         self.beam_status.hardware_read_func=\
#                 self.remcon.read_EHT_status
#     
        self.stage_x.hardware_read_func=\
            self.remcon.read_stage_x
        self.stage_x.hardware_set_func=\
            self.remcon.write_stage_x    
             
        self.stage_y.hardware_read_func=\
            self.remcon.read_stage_y
        self.stage_y.hardware_set_func=\
            self.remcon.write_stage_y
             
        self.stage_z.hardware_read_func=\
            self.remcon.read_stage_z   
         
        self.detector.hardware_read_func=\
            self.remcon.read_detector
        self.detector.hardware_set_func=\
            self.remcon.write_detector
        '''
            
    def disconnect(self):
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        if self.connected.val:
            self.remcon.close()
            del self.remcon