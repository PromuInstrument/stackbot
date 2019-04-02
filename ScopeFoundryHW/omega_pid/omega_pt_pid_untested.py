import serial

class OmegaPtPIDControllerSerialProtocol(object):
    """ Omega PID Controller Pt Platinum  series via Serial Communications protocol
    
    See Manual M5452
    
    Untested
    """
    def __init__(self,port="COM7", address=0x01, debug=False):
        self.port = port
        self.address = address
        self.debug =debug
        
        """If port is a Serial object (or other file-like object)
        use it instead of creating a new serial port"""
        if hasattr(port, 'read'):
            self.ser = self.port
            self.port = None
        else:        
            self.ser = serial.Serial(self.port, baudrate = 9600, bytesize=7, parity='E', 
                    stopbits=1, xonxoff=0, rtscts=0, timeout=0.1)
            
    """
    Protocol
    
    The protocol is command/response, based on 4 command classes:
        Get (G), Put (P), Read (R) and Write (W).
        A Get is used to read the current value resident in RAM, 
        a Put is used to write a parameter to RAM without committing it to non-volatile memory.
        A Read is used to retrieve the value of a parameter stored in non-volatile memory and
        a write is used to commit a parameter value to non-volatile memory.
        
    3.2 Command Structure
    The overall structure of a command packet is as follows:
    -- A start of frame (SOF) character -- usually '*'
    -- A command class (GPRW)
    -- A command ID - a hex number identifying the message.
    -- A mandatory space if there are parameters following the command ID.
    -- A parameter List.
    -- An end of frame (EOF) character -- usually a carriage return.
    A unit address is optional.
    An address is a hex-encoded number in the range 0-199 (00 - C7 hex) between the start of frame and the command class.
    For example, to get the current process value, without an address would be: "*G110 <CR>"
    In this case the command class is 'G', the command ID is 110 (hex) and this command takes no parameters.
    If this were addressed to unit 100 (hex value 64), the command would be: "*64G110 <CR>"
    
    ResponseFormat
    
    The response format depends on whether a command echo has been selected. If selected, the address (if present), command class and command ID precede the parameters returned.
    For example, if an echo is selected, the previous command would return:
    "G110+32.0<CR>" (no address)
    "64G110+32.0<CR> (if the unit responding had address = 64 (hex).
    If echo is not selected, in both cases, only "+32.0<CR>" would be returned.
    For put (P) and Write (W) type transactions, only the command is echoed if echo is on. Thus, "*Pxxx yyyyyy<CR>" will echo "Pxxx<CR>".
    """
    
    def send_cmd(self,cmd_class, cmd_name, param_list=None):
        cmd_id, cmd_classes = self._Pt_Params_by_name[cmd_name]
        assert cmd_class in cmd_classes
        out = "*%s%03X" % (cmd_class[0], cmd_id)
        if param_list:
            out = out + " " + param_list +"\r"
        else:
            out += "\r"
        
        self.ser.write(out)
        
        # read response
        if cmd_class in 'GR':
            resp = self.ser.readline()
            assert resp[-1] == '\r'
            return resp[:-1]
        else:
            # if echo need to read echo
            return True
    
    _Pt_Params = [
        (0x100, 'GPRW', "Input_Configuration"),
        (0x101, 'GPRW', "Filter_Constant"),
        (0x110, 'G'   , "Current_Reading"),
        (0x111, 'G'   , "Peak_Reading"),
        (0x112, 'G'   , "Valley_Reading"),
        (0x120, 'GPRW', "TC_Calibration_Type"),
        (0x121, 'GPRW', "TC_Calibration_Single_Point"),
        (0x122, 'GPRW', "TC_Calibration_Double_Point_Low"),
        (0x123, 'GPRW', "TC_Calibration_Double_Point_High"),
        (0x130, 'GPRW', "Process_Reading_1_Low"),
        (0x131, 'GPRW', "Process_Range_Input_1_Low"),
        (0x132, 'GPRW', "Process_Reading_2_High"),
        (0x132, 'GPRW', "Process_Range_Input_2_High"),
        
        (0x200, 'GPRW', "Display_Configuration"),
        (0x210, 'GPRW', "Excitation_Voltage"),
        (0x220, 'GPRW', "Safety_Configuration"),
        (0x221, 'GPRW', "Loop_Break_Configuration"),
        (0x222, 'GPRW', 'Set_Point_Low_Limit'),
        (0x223, 'GPRW', 'Set_Point_High_Limit'),
        
        #0x300's are communication controls
        
        (0x400, 'GPRW', "Setpoint_1"),
        (0x401, 'GPRW', "Remote_Setpoint_Configuration"),
        (0x410, 'GPRW', "Setpoint_2"),
        (0x420, 'GPRW', "Remote_Process_Range_Setpoint_Min"),
        (0x421, 'GPRW', "Remote_Process_Range_Input_Min"),
        (0x422, 'GPRW', "Remote_Process_Range_Setpoint_Max"),
        (0x423, 'GPRW', "Remote_Process_Range_Input_Max"),
        
        (0x500, 'GPRW', "PID_Configuration"),
        (0x501, 'GPRW', "PID_Low_Clamping_Limit"),
        (0x502, 'GPRW', "PID_High_Clamping_Limit"),
        (0x503, 'GPRW', "PID_P_Param"),
        (0x504, 'GPRW', "PID_I_Param"),
        (0x505, 'GPRW', "PID_D_Param"),
        
        (0x600, 'GPRW', "Output_Mode"),
        (0x601, 'GPRW', "Output_Type"),
        (0x610, 'GPRW', "Output_ON_OFF_Configuration"),
        (0x620, 'GPRW', "Output_Alarm_Configuration"),
        (0x621, 'GPRW', "Output_Alarm_High_Value"),
        (0x622, 'GPRW', "Output_Alarm_Low_Value"),
        (0x623, 'GPRW', "Output_Alarm_On_Delay"),
        (0x624, 'GPRW', "Output_Alarm_Off_Delay"),
        (0x625, 'GPRW', "Output_Alarm_HiHi_Mode"),
        (0x626, 'GPRW', "Output_Alarm_HiHi_Offset"),
        
        #More
        
        (0xF20, 'G'   , "Version_Number"),
        (0xF22, 'G'   , "Bootloader_Version"),
        (0xF30, 'P'   , "Set_Factory_Defaults"),
        ]
    
    _Pt_Params_by_name = {cmd_name:(cmd_id, cmd_classes) for cmd_id, cmd_classes,cmd_name in _Pt_Params }
    
    def get_setpoint1(self):
        resp = self.write_cmd("G", "Setpoint_1")
        sv = float(resp)
        return sv
        
    def put_setpoint1(self, sv):
        self.write_cmd('P', "Setpoint_1", "%+1.2f" % sv)
    
    def get_current_reading(self):
        resp = self.write_cmd("G", "Current_Reading")
        pv = float(resp)
        return pv
    
    output_modes = ["OFF", "PID", "ON-OFF", "scaled", "Alarm1", "Alarm2", "RampSoak_RE.ON", "RampSoak_SE.ON"]
    output_mode_ids = {name:ii for ii, name in enumerate(output_modes)}
    
    def get_output_mode(self, nout=1):
        assert nout in (1,2,3,4)
        resp = self.write_cmd("G", "Output_Mode", "%i" % nout)
        mode_num = int(resp)
        mode = self.output_modes[mode_num]
        return mode
    
    def put_output_mode(self, mode_name, nout=1):
        mode_id = self.output_mode_ids[mode_name]
        assert nout in (1,2,3,4)
        return self.write_cmd("G", "Output_Mode", "%i%i" % (nout, mode_id))
    
    def get_version_num(self):
        return self.send_cmd('G', 'Version_Number')
