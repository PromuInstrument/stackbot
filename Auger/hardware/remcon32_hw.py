'''
Created on Feb 4, 2015

@author: Hao Wu, modified by Frank Ogletree 

Revised by Alan Buckley
'''

'remote control of Zeiss Gemini SEM using the Remcon32 serial interface'

from ScopeFoundry import HardwareComponent
from Auger.hardware.remcon32 import Remcon32


REMCON_PORT='COM4' #default value

class SEM_Remcon_HW(HardwareComponent):
    ''' Auger system uses a different subset of commands from standard Zeiss Gemini'''
    
    name = 'sem_remcon'
     
    def setup(self):
        self.name='sem_remcon'
        self.debug='false'
        #create logged quantities
        
        
        self.settings.New(name='kV', dtype=float, initial=3.0, unit='kV', vmin=0, vmax = 30.0)
        #+- 10 V dac output moves within "size" box determined by mag, calculate mag with pixel size
        self.settings.New(name='size', dtype=float, initial=100e-6, unit = 'm', si=True, vmin=1e-9, vmax=3e-3)
        
        '''
        
        bool.....
            > EHT on
            >  Beam blank
            > ext scan
            > SCM
       
        chan 0/1
            detector,
            contrast,
            brightness (set but don't allow change)
        
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
        
        
        
        self.external_scan = self.settings.New(name='external_scan', 
                                                   dtype=bool,
                                                   ro=False
                                                   )                                                  
        
        self.settings.New('eht_on', dtype=bool, initial=False)
         
        self.beam_blanking = self.settings.New(name='beam_blanking', 
                                                   dtype=bool,
                                                   ro=False,
                                                   )
        self.settings.New('kV', dtype=float, unit='kV', vmin=0, vmax=30, initial=3, )
        self.settings.New('contrast0', dtype=float, unit=r'%', vmin=0, vmax=100)
        self.settings.New('contrast1', dtype=float, unit=r'%', vmin=0, vmax=100)
        self.magnification = self.settings.New(name='magnification', 
                                                   dtype=float,
                                                   ro=False,
                                                   vmin=5.0,
                                                   vmax=5.0e5,
                                                   unit='x')
        

        
        
        self.WD = self.settings.New(name='WD', dtype=float,
                                                   ro=False,
                                                   vmin=0.0,
                                                   fmt='%.3f',
                                                   unit='mm')
        
        self.settings.New(name='detector0',
                                       dtype=str,
                                       ro=False,
                                       initial='SE2',
                                       choices=('SE2','VPSE','InLens'))

        self.settings.New(name='detector1',
                                       dtype=str,
                                       ro=False,
                                       initial='SE2',
                                       choices=('SE2','VPSE','InLens'))

        
        self.settings.New('stig_xy', dtype=float, array=True, fmt='%1.1f', initial=[0,0], vmin=-100, vmax=100, unit=r'%')
        
#         self.stage_x=self.settings.New(name='stage_x',
#                                                dtype=float,
#                                                ro=False,
#                                                vmin=5.0,
#                                                vmax=95.0,
#                                                initial=50,
#                                                unit='mm')
#          
#         self.stage_y=self.settings.New(name='stage_y',
#                                                dtype=float,
#                                                ro=False,
#                                                vmin=5.0,
#                                                vmax=95.0,
#                                                initial=50,
#                                                unit='mm')
#          
#         self.stage_z=self.settings.New(name='stage_z',
#                                                dtype=float,
#                                                ro=False,
#                                                vmin=0.0,
#                                                vmax=25.0,
#                                                initial=1.0,
#                                                unit='mm')
#         
#         self.probe_current = self.settings.New(name='probe_current', 
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
           
        self.select_aperture = self.settings.New(name='select_aperture', 
                                                   dtype=int,
                                                   ro=True,
                                                   vmin=1,
                                                   vmax=6,
                                                   unit='',
                                                   choices=aperture_choices)
        
        
        self.settings.New('scm_state', dtype=bool, description='Specimen Current Monitor On/Off')
        self.settings.New('scm_current', dtype=float,ro=True, si=True, unit='A')
        
        self.settings.New('port', dtype=str, initial='COM4')
        
        #connect to GUI
        if False:
            self.magnification.connect_bidir_to_widget(self.gui.ui.sem_magnification_doubleSpinBox)
            self.beam_blanking.connect_bidir_to_widget(self.gui.ui.beam_blanking_checkBox)
            
        
    def connect(self):
        #if self.debug: print "connecting to REMCON32"
        S = self.settings
        
        #connecting to hardware
        R = self.remcon = Remcon32(port=S['port'])
        
        
        #connect logged quantity
        S.magnification.connect_to_hardware(
                read_func = R.get_mag,
                write_func = R.set_mag
                )
        
        S.eht_on.connect_to_hardware(
                read_func = R.get_eht_state,
                write_func = R.set_eht_state
                )
                
        S.beam_blanking.connect_to_hardware(
                read_func = R.get_blank_state,
                write_func = R.set_blank_state
                )
                
        S.stig_xy.connect_to_hardware(
            read_func=R.get_stig,
            write_func=lambda XY: R.set_stig(*XY),
            )
        

        S.WD.connect_to_hardware(
                read_func = R.get_wd,
                write_func = R.set_wd
                )
                
        S.select_aperture.connect_to_hardware(
                read_func = R.get_ap,
                write_func = R.set_ap
                )
                
        
        S.external_scan.connect_to_hardware(
                read_func = R.get_ap,
                write_func = R.set_ap
                )

        S.eht_on.connect_to_hardware(
                read_func = R.get_eht_state,
                write_func = R.set_eht_state
                )
        
#         S.beam_status.hardware_set_func=\
#                 self.remcon.turn_EHT
#         S.beam_status.hardware_read_func=\
#                 self.remcon.read_EHT_status
#     


#         S.stage_x.hardware_read_func=\
#             self.remcon.read_stage_x
#         S.stage_x.hardware_set_func=\
#             self.remcon.write_stage_x    
#              
#         S.stage_y.hardware_read_func=\
#             self.remcon.read_stage_y
#         
#         S.stage_y.hardware_set_func=\
#             self.remcon.write_stage_y
#              
#         S.stage_z.hardware_read_func=\
#             self.remcon.read_stage_z   
## Array implementation needed.
         
        S.detector0.connect_to_hardware(
                read_func = R.get_detector,
                write_func = R.set_detector
                )
        
        S.kV.connect_to_hardware(
            read_func = R.get_kV,
            write_func = R.set_kV)
        
        S.scm_state.connect_to_hardware(
            write_func=R.scm_state
            )

        S.scm_current.connect_to_hardware(
            read_func=R.get_scm
            )
        
        
            
    def disconnect(self):
#         for lq in self.logged_quantities.values():
#             lq.hardware_read_func = None
#             lq.hardware_set_func = None
        if self.connected.val:
            self.remcon.close()
            del self.remcon
            
class Auger_Remcon_HW(SEM_Remcon_HW):
    '''subclass SEM_Remcon_HW to handle Auger-specific command set'''
    def setup(self):
        SEM_Remcon_HW(self).setup()
        for key in self.settings.as_dict().keys():
            print( 'Auger_Remcon_HW', key )
        print( 'done with Auger_Remcon_HW setup')
            

