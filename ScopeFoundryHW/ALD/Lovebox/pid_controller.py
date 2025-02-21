'''
@author: Ed Barnard
Updated by Alan Buckley (2/6, 3/15, 5/15 of 2018)
'''

from __future__ import division
from threading import Lock
import serial
import struct
import numpy as np


class PIDController(object):
    """
    Generic PID Controller communicating via RS-485 Modbus ASCII protocol.
    
    Communications library works with PID controllers including but not 
    limited to the following models:
    
    * Omega CN7500
    * Dwyer Love Controls 4B
    
    """
    def __init__(self,port="COM1", address=0x01, debug=False):
        self.port = port
        self.address = address
        self.debug = debug
        self.lock = Lock()
        
        """If port is a Serial object (or other file-like object)
        use it instead of creating a new serial port"""
        if hasattr(port, 'read'):
            self.ser = self.port
            self.port = None
        else:        
            self.ser = serial.Serial(self.port, baudrate = 9600, bytesize=7, parity='E', 
                    stopbits=1, xonxoff=0, rtscts=0, timeout=0.1)
        
    def read_for_data_log(self):
        self.temp, self.setp = 0.1 * np.array(self.send_analog_read(0x1000, 2))
        self.outp1, self.outp2 = 0.1 * np.array(self.send_analog_read(0x1012, 2))
        return (self.temp, self.setp, self.outp1, self.outp2)
    
    def load_settings(self):
        """
        Reads all settings from controller
        """
        self.temp, self.setp = 0.1 * np.array(self.send_analog_read(0x1000, 2))
        #need more
        self.read_ctrl_method()
        self.read_heat_cool_ctrl()
        self.outp1, self.outp2 = 0.1 * np.array(self.send_analog_read(0x1012, 2))
        self.software_version = self.send_analog_read(0x102F)
        
    def autotune(self, status):
        """
        Initiate/Stop autotune feature which automatically tunes PID parameters.
        
        =============  ===========  =======================  ===================================
        **Arguments**  **Type**     **Description**          **Valid Range**
        status         boolean int  Proportional term value  (0, 1)
        =============  ===========  =======================  ===================================

        """
        assert status in [0,1]
        self.send_analog_write(0x0813, int(status))
    
    def read_temp(self):
        """
        Reads Process Value from temperature controller.
        
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.pv_temp`
        
        :returns: (float) Process Value in Celsius.
        """
        self.temp = 0.1 * self.send_analog_read(0x1000)
        return self.temp
    
    def read_setpoint(self):
        """
        Reads stored Set Point Value from temperature controller

        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.sv_setpoint`

        :returns: (float) Stored Set Point Value in Celsius.
        """
        self.setp = 0.1 * self.send_analog_read(0x1001)
        return self.setp

    
    def set_setpoint(self, setp):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.sv_setpoint`
        
        Stores Set Point Value to temperature controller

        =============  ==========  ==========================================================
        **Arguments**  **Type**    **Description**
        setp           str         Desired set point value in units of Celsius.
        =============  ==========  ==========================================================

        :returns: (float) Stored Set Point value written to the temperature controller. \
        (This is not a response from the controller)
        """
        self.send_analog_write(0x1001, int(setp*10) )
        self.setp = setp
        return self.setp
    
    def read_output1(self):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.output1`
        
        :returns: (float) Output 1 percentage value in units of 0.1 %.
        """
        self.outp1 = 0.1 * self.send_analog_read(0x1012)
        return self.outp1
        
    def read_output2(self):
        """
        :returns: (float) Output 2 percentage value in units of 0.1 %.
        """
        self.outp2 = 0.1 * self.send_analog_read(0x1013)
        return self.outp2
        
    def set_output1(self, outp1):
        """
        Set output percentage in units of 0.1%
        Write operation valid only in manual tuning mode.
        
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.output1`
        
        =============  ==========  ==========================================================
        **Arguments**  **Type**    **Description**
        outp1          str         Desired
        =============  ==========  ==========================================================
        
        :returns: (float) Output 1 percentage value in units of 0.1 %.
        """
        
        self.send_analog_write(0x1012, int(outp1*10) )
        self.outp1 = outp1
        return self.outp1
        
    def set_output2(self, outp2):
        """
        Set output percentage in units of 0.1%
        Write operation valid only in manual tuning mode.
        
        =============  ==========  ==========================================================
        **Arguments**  **Type**    **Description**
        outp2          str         Desired
        =============  ==========  ==========================================================
        
        :returns: (float) Output 2 percentage value in units of 0.1 %."""
        self.send_analog_write(0x1012, int(outp2*10) )
        self.outp2 = outp2
        return self.outp2

    def read_prop_band(self):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.Proportional_band`
        
        :returns: (float) PID Proportional term value.
        """
        prop = 0.1*self.send_analog_read(0x1009)
        return prop

    def set_prop_band(self, p):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.Proportional_band`
        
        =============  ==========  =======================  ===================================
        **Arguments**  **Type**    **Description**          **Valid Range**
        p              float       Proportional term value  (0.1, 999.9)
        =============  ==========  =======================  ===================================
        
        """
        assert 0. <= p <= 999.9
        self.send_analog_write(0x1009, int(10*p))
    
    def read_integral_time(self):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.Integral_time`
        
        :returns: (int) PID Integral term value.
        """
        integral_t = self.send_analog_read(0x100A)
        return integral_t
    
    def set_integral_time(self, integral_t):
        """
        Sets PID Integral term value.

        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.Integral_time`
        
        =============  ==========  =======================  ===============
        **Arguments**  **Type**    **Description**          **Valid Range**
        integral_t     int         Integral term value      (0, 9999)
        =============  ==========  =======================  ===============
        
        """
        assert 0 <= int(integral_t) <= 9999
        self.send_analog_write(0x100A, int(integral_t))
    
    def read_derivative_time(self):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.Derivative_time`
        
        :returns: (int) PID Derivative term value.
        """
        derivative_t = self.send_analog_read(0x100B)
        return derivative_t
        
    def set_derivative_time(self, derivative_t):
        """
        Sets PID Derivative term value.
        
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.Derivative_time`
        
        =============  ==========  =======================  ===============
        **Arguments**  **Type**    **Description**          **Valid Range**
        derivative_t   int         Derivative term value    (0, 9999)
        =============  ==========  =======================  ===============
        
        """
        assert 0 <= int(derivative_t) <= 9999
        self.send_analog_write(0x100B, derivative_t)

    def read_ctrl_method(self):
        """
        ==================  ===================
        **Value**           **Control Method**
        0                   PID
        1                   ON/OFF
        2                   Manual tuning
        3                   PID program control
        ==================  ===================
        
        :returns: (int) Active temperature approach method
        """
        self.ctrl_method_i = self.send_analog_read(0x1005)
        self.ctrl_method_name = self.CTRL_METHODS[self.ctrl_method_i]
        
        return (self.ctrl_method_i, self.ctrl_method_name)
    
    def set_ctrl_method(self, ctrl_method_i):
        """
        Sets active temperature approach method.
        
        =============  ==========  ================================  ===============
        **Arguments**  **Type**    **Description**                   **Valid Range**
        ctrl_method_i  int         Integer corresponding to desired  (0, 3)
                                   mode of operation. See table 
                                   below.
        =============  ==========  ================================  ===============
        
        ==================  ==================
        **Value**           **Control Method**
        0                   PID
        1                   ON/OFF
        2                   Manual tuning
        3                   PID program control
        ==================  ==================
        
        """
        
        ctrl_method_i = int(ctrl_method_i)
        assert 0 <= ctrl_method_i <= 3

        self.send_analog_write(0x1005, ctrl_method_i)
        
        self.ctrl_method_i = ctrl_method_i
        self.ctrl_method_name = self.CTRL_METHODS[self.ctrl_method_i]

        return (self.ctrl_method_i, self.ctrl_method_name)

    def read_heat_cool_ctrl(self):
        """
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.heat_cool_control`

        ==================  ==================
        **Value**           **Control Method**
        0                   Heating
        1                   Cooling
        2                   Heating/Cooling
        3                   Cooling/Heating
        ==================  ==================
        
        :returns: tuple: (int, str). Active Heating/Cooling control method. See above table for reference.
        """
        self.heat_cool_ctrl_i = self.send_analog_read(0x1006)
        self.heat_cool_ctrl_name = self.HEAT_COOL_CTRLS[self.heat_cool_ctrl_i]
        
        return (self.heat_cool_ctrl_i, self.heat_cool_ctrl_name)
    
    def set_heat_cool_ctrl(self, heat_cool_ctrl_i):
        """
        Sets Heating/Cooling mode of operation.
        
        ================  ==========  ================================  ===============
        **Arguments**     **Type**    **Description**                   **Valid Range**
        heat_cool_ctrl_i  int         Integer corresponding to desired  (0, 3)
                                      mode of operation. See table 
                                      below.
        ================  ==========  ================================  ===============
        
        
        ==================  ==================
        **Value**           **Control Method**
        0                   Heating
        1                   Cooling
        2                   Heating/Cooling
        3                   Cooling/Heating
        ==================  ==================
        
        :returns: tuple: (int, str). Intended Heating/Cooling control method. See above table for reference.
        """
        heat_cool_ctrl_i = int(heat_cool_ctrl_i)
        assert 0 <= heat_cool_ctrl_i <= 3

        self.send_analog_write(0x1006, heat_cool_ctrl_i)
        
        self.heat_cool_ctrl_i = heat_cool_ctrl_i
        self.heat_cool_ctrl_name = self.HEAT_COOL_CTRLS[self.heat_cool_ctrl_i]

        return (self.heat_cool_ctrl_i, self.heat_cool_ctrl_name)
    
    def set_pid_preset(self, pid):
        """
        In PID control mode, 
        this command reads currently selected PID mode out of 
        4 possible PID preset modes.
        If n=4 is selected, the unit will perform auto-tuning. (Auto PID parameter)
        
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.PID_preset`
        
        ================  ==========  ================================  ===============
        **Arguments**     **Type**    **Description**                   **Valid Range**
        pid               int         Integer corresponding to desired  (0, 4)
                                      PID preset. See table below.
        ================  ==========  ================================  ===============

        ==================  ==================
        **Value**           **PID Preset**
        (0, 3)              PID mode
        4                   Auto PID mode
        ==================  ==================
        
        """
        assert pid in range(0,5)
        self.send_analog_write(0x101c, pid)
        
    def read_pid_preset(self):
        """
        In PID control mode, 
        this command reads currently selected PID mode out of 
        4 possible PID preset modes.
        If n=4 is selected, the unit will perform auto-tuning. (Auto PID parameter)
        
        Connected to *LoggedQuantity*   
        :attr:`app.hardware.lovebox.settings.PID_preset`
        
        :returns: (int) Selected PID preset.
        """
        pid = self.send_analog_read(0x101c)
        return pid
    
    def set_pid_sv(self, sv):
        """
        Writes set point value in current PID control mode.
                
        ================  ==========  ================================
        **Arguments**     **Type**    **Description**
        sv                float       Desired PID setpoint value.
        ================  ==========  ================================
        
        """
        self.send_analog_write(0x101d, 10*sv)
    
    def read_pid_sv(self):
        """
        Reads set point value in current PID control mode.
        
        :returns: (float) Current set point value.
        """
        sv = 0.1 * self.send_analog_read(0x101d)
        return sv
    
    def set_ctrl_run(self, run):
        """
        Sets regular program Run/Stop status.
        
        ================  ==========  ================================  ===============
        **Arguments**     **Type**    **Description**                   **Valid Range**
        run               int         Boolean integer which tells the   (0, 1)
                                      controller whether or not to run
                                      its PID control mode.
                                      See table below.
        ================  ==========  ================================  ===============
        
        =========  ===============
        **Value**  **Description**
        0          Stop
        1          Run
        =========  ===============
        
        """
        self.send_analog_write(0x0814, int(run))
        
    def read_ctrl_run(self):
        """
        Reads regular control Run/Stop setting.
        
        =========  ===============
        **Value**  **Description**
        0          Stop
        1          Run
        =========  ===============
        
        :returns: (bool) Value representing program Run/Stop status.
        """
        run_status = self.send_analog_read(0x0814)
        return bool(run_status)
        
    def set_pid_ctrl_run(self, run):
        """
        Sets PID program control status.
        
        ================  ==========  ================================  ===============
        **Arguments**     **Type**    **Description**                   **Valid Range**
        run               int         Boolean integer which tells the   (0, 1)
                                      controller whether or not to run
                                      its PID control mode.
                                      See table below.
        ================  ==========  ================================  ===============
        
        =============  ===============
        **Argument**   **Description**
        True (1)       Run            
        False (0)      Stop           
        =============  ===============
        
        """
        self.send_analog_write(0x0815, not int(run))
    
    def read_pid_ctrl_run(self):
        """
        Reads PID program control status.
        
        =========  ===============  ===================
        **Value**  **Description**  **Returned Value**
        0          Running          True
        1          Stopped          False
        =========  ===============  ===================
        
        :returns: (bool) Value representing whether PID program control is running.
        """
        run_status = self.send_analog_read(0x0815)
        return not bool(run_status)
        
    def modbus_command(self, command, register, data):
        address = self.address
        message = bytearray([address, command, register >> 8, register % 0x100, data >> 8, data %0x100])
    
        lrc = (0x100 + 1 + ~(sum(message) % 0x100)) % 0x100
        message.append(lrc)          # Add to the end of the message
        
        ascii_message = ":" + "".join( "%02X" % b for b in message) + "\r\n"
        
        if self.debug:print(repr(message))
        if self.debug:print(repr(ascii_message))
    
        return ascii_message.encode()
            
    def analog_read_command(self, register, length):
        return self.modbus_command(0x03, register, data=length)

    def send_analog_read(self, register, length=None):
        """
        Sends an analog read command FC 0x03 to device.
        
        :returns: (int16) Array of length "length".
        """
        return_single = False
        if length == None:
            return_single = True
            length = 1
        
        register = int(register)
        length = int(length)
        assert 1 <= length <= 8

        with self.lock:
            self.ser.write(self.analog_read_command(register, length))#.decode())
            output = self.ser.readline() # is \r\n included !? Yes.
            """:01030200EA10"""

        assert output[0] == ord(':')
        

        #create byte array from output
        output_hexstr = output[1:-2] # remove starting ":" and ending \r\n
        output_bytes = bytearray( 
			[ int(output_hexstr[i:i+2], 16) for i in range(0, len(output_hexstr), 2) ] )
        
        if self.debug: print("output_bytes", [hex(a) for a in output_bytes])
        
        lrc = (0x100 + 1 + ~(sum(output_bytes[:-1]) % 0x100)) % 0x100
        assert output_bytes[-1] == lrc # error check
        
        assert output_bytes[0] == self.address
        assert output_bytes[1] == 0x03
        assert output_bytes[2] == length*2
        
        data_bytes = output_bytes[3:-1]
        
        if self.debug: print("data_bytes", [hex(a) for a in data_bytes])
        
        #return struct.unpack("<%ih" % length, data_bytes)
        data_shorts = [
            ( (data_bytes[i] << 8) + data_bytes[i+1] ) 
                for i in range(0, len(data_bytes), 2 ) ]
        if return_single:
            return data_shorts[0]
        else:
            return data_shorts
        
    def analog_write_command(self, register, data):
        return self.modbus_command(0x06, register, data)

    def send_analog_write(self, register, data):
        """
        Sends analog write command to register 0x06.
        """
        cmd = self.analog_write_command(register, data)
        with self.lock:
            self.ser.write(cmd)#.decode())
            output = self.ser.readline()

    def close(self):
        """
        Closes serial connection. Removes serial object.
        """
        self.ser.close()
        del self.ser


    CTRL_METHODS = ("PID", "ON/OFF", "Manual", "PID Program Ctrl")
    HEAT_COOL_CTRLS = ("Heating", "Cooling", "Heating/Cooling", "Cooling/Heating")

    _CN7x00_registers = [        
        ( 0x1000 , "Process value (PV)" ),
        ( 0x1001 , "Set point (SV)" ),      # Unit is 0.1, oC or oF
        ( 0x1002 , "Upper-limit of temperature range" ),
        ( 0x1003 , "Lower-limit of temperature range" ),
        ( 0x1004 , "Input temperature sensor type" ), 
        ( 0x1005 , "Control method" ), #0: PID, 1: ON/OFF, 2: manual tuning, 3: PID program control
        ( 0x1006 , "Heating/Cooling control selection" ), #0: Heating, 1: Cooling, 2: Heating/Cooling, 3: Cooling/Heating
        ( 0x1007 , "1st group of Heating/Cooling control cycle" ), 
        ( 0x1008 , "2nd group of Heating/Cooling control cycle" ),
        ( 0x1009 , "PB Proportional band" ),
        ( 0x100A , "Ti Integral time" ),
        ( 0x100B , "Td Derivative time" ),
        ( 0x100C , "Integration default 0~100%, unit is 0.1% " ),
        ( 0x100D , "Proportional control offset error value, when Ti = 0 " ),
        ( 0x100E , "The setting of COEF when Dual Loop output control are used" ),
        ( 0x100F , "The setting of Dead band when Dual Loop output control are used" ),
        ( 0x1010 , "Hysteresis setting value of the 1st output group" ),
        ( 0x1011 , "Hysteresis setting value of the 2nd output group" ),
        ( 0x1012 , "Output value read and write of Output 1" ),
        ( 0x1013 , "Output value read and write of Output 2" ),
        ( 0x1014 , "Upper-limit regulation of analog linear output" ),
        ( 0x1015 , "Lower-limit regulation of analog linear output" ),
        ( 0x1016 , "Temperature regulation value" ),
        ( 0x1017 , "Analog decimal setting" ),
        ( 0x101C , "PID parameter selection" ),
        ( 0x101D , "SV value corresponded to PID value" ),
        ( 0x1020 , "Alarm 1 type" ),
        ( 0x1021 , "Alarm 2 type" ),
        ( 0x1022 , "Alarm 3 type" ),
        ( 0x1023 , "System alarm setting" ),
        ( 0x1024 , "Upper-limit alarm 1" ),
        ( 0x1025 , "Lower-limit alarm 1" ),
        ( 0x1026 , "Upper-limit alarm 2" ),
        ( 0x1027 , "Lower-limit alarm 2" ),
        ( 0x1028 , "Upper-limit alarm 3" ),
        ( 0x1029 , "Lower-limit alarm 3" ),
        ( 0x102A , "Read LED status" ),
        ( 0x102B , "Read push button status" ),
        ( 0x102C , "Setting lock status" ),
        ( 0x102F , "Software version" ),
        ( 0x1030 , "Start pattern number" ),
    ]    
        #1040H~ 1047H ,Actual step number setting inside the correspond pattern 
        #1050H~ 1057H ,Cycle number for repeating the execution of the correspond pattern 
        #1060H~ 1067H ,Link pattern number setting of the correspond pattern 
        #2000H~ 203FH ,Pattern 0~7 temperature set point setting Pattern 0 temperature is set to 2000H~2007H 
        #2080H~ 20BFH ,Pattern 0~7 execution time setting Pattern 0 time is set to 2080H~2087H 
        

        
# if __name__ == '__main__':
#     pid1 = OmegaPIDController(port="COM7", address=0x01, debug=True)    
#     print "TEMP:", pid1.read_temp()