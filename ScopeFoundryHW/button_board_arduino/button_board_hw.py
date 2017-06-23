'''
Created on Jun 21, 2017

@author: Alan Buckley
'''
from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent

import logging

logger = logging.getLogger(__name__)

try: 
    from ScopeFoundryHW.button_board_arduino.button_board_interface import ButtonBoardInterface
except Exception as err:
    logger.error("Cannot load required modules for ButtonBoardInterface, {}".format(err))

class ButtonBoardHW(HardwareComponent):
    
    name = 'button_board_hw'
    
    def setup(self):
        self.port = self.settings.New(name="port", initial="COM4", dtype=str, ro=False)
        
        self.chan1 = self.settings.New(name="Channel_1", initial=False, dtype=bool, ro=False)
        self.chan2 = self.settings.New(name="Channel_2", initial=False, dtype=bool, ro=False)
        self.chan3 = self.settings.New(name="Channel_3", initial=False, dtype=bool, ro=False)
        self.chan4 = self.settings.New(name="Channel_4", initial=False, dtype=bool, ro=False)
    
    def connect(self):
        self.button_interface = ButtonBoardInterface(port=self.port.val, 
                                                     debug=self.settings['debug_mode'])
        
        self.update_chan_lq()
          
        self.chan1.connect_to_hardware(
            write_func = self.write_button1)
        self.chan2.connect_to_hardware(
            write_func = self.write_button2)
        self.chan3.connect_to_hardware(
            write_func = self.write_button3)
        self.chan4.connect_to_hardware(
            write_func = self.write_button4)
        
        self.settings.inst_name1.connect_to_hardware(
            write_func = self.write_inst_name1)
        self.settings.inst_name2.connect_to_hardware(
            write_func = self.write_inst_name2)
        self.settings.inst_name3.connect_to_hardware(
            write_func = self.write_inst_name3)
        self.settings.inst_name4.connect_to_hardware(
            write_func = self.write_inst_name4)
        

    def update_chan_lq(self):
        self.settings['Channel_1'] = self.button_interface.button_poll[0]
        self.settings['Channel_2'] = self.button_interface.button_poll[1]
        self.settings['Channel_3'] = self.button_interface.button_poll[2]
        self.settings['Channel_4'] = self.button_interface.button_poll[3]
    
    def button_listen(self):
        data = self.button_interface.listen()
        if data: 
            button_state = self.settings['Channel_{}'.format(data)]
            print("data:", data)
            print("button_state:", button_state)
            self.settings['Channel_{}'.format(data)] = not button_state
            print("not button_state:", not button_state)
        
    def write_button1(self, value):
        self.button_interface.write_state(1, value)
    
    def write_button2(self, value):
        self.button_interface.write_state(2, value)
    
    def write_button3(self, value):
        self.button_interface.write_state(3, value)
    
    def write_button4(self, value):
        self.button_interface.write_state(4, value)
    
    def write_inst_name1(self, name):
        self.button_interface.write_instrument_name(1, name)
    
    def write_inst_name2(self, name):
        self.button_interface.write_instrument_name(2, name)
    
    def write_inst_name3(self, name):
        self.button_interface.write_instrument_name(3, name)
    
    def write_inst_name4(self, name):
        self.button_interface.write_instrument_name(4, name)
         
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'button_interface'):
            self.button_interface.close()
            del self.button_interface
        

