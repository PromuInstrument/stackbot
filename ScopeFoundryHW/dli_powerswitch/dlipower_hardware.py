"""Wrapper written by Alan Buckley and Ed Barnard. Dlipower module written by Dwight Hubbard."""
from __future__ import division, absolute_import, print_function
from ScopeFoundry import HardwareComponent
import dlipower
    
import time
import random

class DLIPowerSwitchHW(HardwareComponent):

    def setup(self):

        self.name = "dli_powerswitch"

        # Create logged quantities
        self.sockets = []
        self.names = []
        for ii in range(8):
            name = self.settings.New(name='Outlet_%i_Name' % (ii+1), dtype=str, initial='Outlet_%i' % (ii+1), ro=True)
            self.names.append(name)
            sock = self.settings.New(name='Outlet_%i' % (ii+1), dtype=bool, initial='Socket_%i' % (ii+1), ro=False)
            self.sockets.append(sock)

        ## Credentials

        self.host = self.settings.New(name='host', initial ='131.243.183.254', dtype=str, ro=False)
        self.userid = self.settings.New(name='userid', initial='admin', dtype=str, ro=False)
        self.key = self.settings.New(name='key', initial='lbnl', dtype=str, ro=False)

        #self.int_time.spinbox_decimals = 3


        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)
        
        # connect to gui
        #try:
        #    self.int_time.connect_bidir_to_widget(self.gui.ui.apd_counter_int_doubleSpinBox)
        #except Exception as err:
        #    print "APDCounterHardwareComponent: could not connect to custom GUI", err

        self.add_operation('read_all_states', self.read_all_states)

    def read_status(self, socket):
        status = self.switch[socket].state
        self.log.debug( "dlipower read_status {} {}".format( socket, status ) )

        if status == 'ON':
            return True
        else:
            return False

    def read_name(self, socket):
        outlet_name = self.switch[socket].name
        self.log.debug( "dlipower read_name {} {}".format( socket, outlet_name ) )
        return outlet_name

    def write_status(self, socket, new_val):
        self.log.debug( "dlipower write_status {} {}".format( socket, new_val ))
        if new_val:
            self.switch[socket].state = 'ON'
        else:
            self.switch[socket].state = 'OFF'        

    def connect(self):
        if self.debug_mode.val: self.log.debug( "Connecting to Power Switch (Debug)" )
        
        # Open connection to hardware

        if not self.dummy_mode.val:
            self.switch = dlipower.PowerSwitch(hostname=self.host.val, userid=self.userid.val, password=self.key.val) #ParameterstoLQ
        else:
            if self.debug_mode.val: self.log.debug( "Connecting to Power Switch (Dummy Mode)" )

        # connect logged quantities

        for ii in range(8):
            def read_ii(ii=ii):
                status = self.read_status(ii)
                return status
            def read_name(ii=ii):
                name = self.read_name(ii)
                return name
            #self.sockets[ii].hardware_read_func = read
            self.sockets[ii].hardware_read_func = read_ii
            self.names[ii].hardware_read_func = read_name
            #... = lambda ii=ii: self.read_status(ii)
            def write_ii(new_val, ii=ii):
                return self.write_status(ii, new_val)
            self.sockets[ii].hardware_set_func = write_ii
            #self.sockets[ii].hardware_set_func = lambda new_val, ii=ii: self.write_status(ii, new_val)

            #or: self.socket[ii].updated_value.connect( write_ii )


        #try:
        #    self.apd_count_rate.updated_text_value.connect(self.gui.ui.apd_counter_output_lineEdit.setText)

        #except Exception as err:
        #    print "missing gui", err


    def read_all_states(self):
        status_list = self.switch.statuslist()
        self.log.debug( repr(status_list))
        #[1, u'Cool Outlet 2', u'ON']
        for outlet_data in status_list:
            outlet_num, outlet_name, outlet_status = outlet_data
            outlet_bool = dict(ON=1, OFF=0)[outlet_status]
            self.settings.as_dict()['Outlet_%i' % outlet_num].update_value(outlet_bool, update_hardware=False)
            self.settings.as_dict()['Outlet_%i_Name' % outlet_num].update_value(outlet_name, update_hardware=False)



    def disconnect(self):
        #disconnect hardware
        #self.switch.close()
        
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        # clean up hardware object
        if hasattr(self, 'switch'):
            del self.switch
        