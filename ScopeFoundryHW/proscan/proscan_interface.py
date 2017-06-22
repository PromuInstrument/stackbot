'''
@author: Alan Buckley
'''
import logger
import serial


class ProscanInterface(object):

    def __init__(self, port="COM1", debug = False):
        self.port = port
        self.debug = debug
        if self.debug:
            logger.debug("ProscanInterface.__init__, port={}".format(self.port))
            
        self.ser = serial.Serial(port=self.port, baudrate=9600, bytesize=8, 
                                 parity='N', stopbits=1, timeout = 0.1)
        
        self.axis_lim = {0b00000001: "+X",
                         0b00000010: "-X",
                         0b00000100: "+Y",
                         0b00001000: "-Y",
                         0b00010000: "+Z",
                         0b00100000: "-Z",
                         0b01000000: "+4",
                         0b10000000: "-4"}
        self.axis_motion = {0b000001: "X",
                            0b000010: "Y",
                            0b000100: "Z",
                            0b001000: "A",
                            0b010000: "F1",
                            0b100000: "F2"}
                                             
    def ps_cmd(self, cmd):
        """
        ==============  =========  =================================================
        **Arguments:**  **Type:**  **Description:**
        cmd             str        Command to be sent to the ProScan unit via RS232.
        ==============  =========  =================================================
        :returns: Response of the ProScan unit.
        """
        message = cmd.encode()+b'\r'
        resp = self.ser.write(message)
        if len(resp) < 2:
            raise IOError("No readout from Proscan device. Received response: {}".format(resp))
        if self.debug:
            logger.debug("ps_cmd response: {}".format(resp))
        return resp
    
    def abort(self):
        """
        Aborts the current move and empties the queue.
        :returns: None
        """
        message = b"I"
        resp = self.ps_cmd(message)
        if self.debug:
            logger.debug("ps abort triggered. Queue emptied.")
    
    def limit_query(self):
        """
        Queries the ProScan device after reached axis limits.
        :returns: limit status integer describing which limits have been reached. See `self.axis_lim` for boolean conversion table.""" 
        resp = self.ps_cmd(b"=")
        return resp
    
    def move_query(self):
        """
        Asks after the movement status of each and every axis.
        :returns: movement status integer describing which axes are still in motion. See `self.axis_motion` for boolean conversion table.
        """
        resp = self.ps_cmd(b"$")
        return resp
    
    def get_com_protocol(self):
        """
        Reports the command protocol currently in use.
        After a reset or software upgrade, the ProScan unit defaults to Compatibility mode.
        :returns: bool
        =========  ==================
        **Value**  **Description**
        0          Standard Mode
        1          Compatibility Mode
        =========  ==================
        """
        resp = self.ps_cmd(b"COMP")
        result = resp
        return result
    
    def set_com_protocol(self, m):
        """Sets the controller compatibility mode for users who want to wait for ‘R’ at the end of the move. 
        Compatibility is on if m = 1 and off if m = 0.
        ===============  =========  ==================
        **Argument**     **Value**  **Description**
        m                0          Standard Mode
                         1          Compatibility Mode
        ===============  =========  ==================
        :returns: bool (zero)
        """
        self.ps_cmd(b"COMP,{}".format(m))

        
    def full_stop(self):
        """
        Stops movement in a controlled manner to reduce the risk of losing position. The command queue is also emptied.
        """
        self.ps_cmd(b"I")
    
    def goto_abs_position(self, array):
        """
        Go to the absolute position x, y, z.
        ===============  =========  ==========================================
        **Argument**     **Value**  **Description**
        array            [x,y,z]    Integer array describing absolute position      
        ===============  =========  ==========================================
        """
        x, y, z = array
        self.ps_cmd(b"G,{},{},{}".format(x,y,z))
        
    def get_abs_position(self):
        """Reports absolute position of x,y and z axes. 
        This can be used whilst any axis is moving to give ‘position on the fly’ 
        Note <CR> only will also return position.
        :returns: array in the format [x,y,z]
        """
        resp = self.ps_cmd(b"P")
        str_array = str(resp).strip().split(",")
        array = list(map(int, str_array))
        return array
    
    def set_abs_position(self, array):
        """
        Sets absolute position of x, y, and z axis. 
        No axis can be moving for this command to work
        """
        x, y, z = array
        self.ps_cmd("P,{},{},{}".format(x,y,z))
        
    
    def joystick_input_on(self):
        """
        Turns ON the joystick (Stage and Z axes). This command is acted upon immediately.
        """
        self.ps_cmd(b"H")
        
    def joystick_input_off(self):
        """
        Turns OFF the joystick (Stage and Z axes) after completion of any current joystick move. 
        The joystick is re-enabled using ‘J’ Command. The joystick is always enabled on power up.
        """
        self.ps_cmd(b"J")
        
    def set_joystick_speed(self, s):
        """Sets the speed of the stage under joystick control. s is percentage in range 1 to 100.
        ===============  =========  ==========================================
        **Argument**     **Value**  **Description**
        s                1-100      Joystick speed percentage
        ===============  =========  =========================================="""
        self.ps_cmd(b"O,{}".format(s))
    
    def set_focus_motor_speed(self, S):
        """Sets the speed of the focus motor under joystick/digipot control. s is percentage in range 1 to 100.
        ===============  =========  ==========================================
        **Argument**     **Value**  **Description**
        S                1-100      Focus motor speed percentage
        ===============  =========  =========================================="""
        self.ps_cmd(b"OF,{}".format(S))
    
    def set_scan_res(self, axis, resolution):
        """Sets the desired resolution for the stage, s is X and Y axes, r can be a non integer number setting the 
        resolution for the axis in units of microns. (e.g. RES,S,1.0) meaning set resolution to 1.0 micron. Not all 
        resolutions are achievable accurately. Only those that are direct multiples of the base microstep resolution.
        See Appendix B and SS commands."""
        assert axis in ["X","Y","Z"]
        self.ps_cmd(b"RES,{},{}".format(axis, float(resolution)))
    
    def get_scan_res(self, axis):
        """Returns resolution for axis a."""
        assert axis in  ["X", "Y", "Z"]
        resp = self.ps_cmd(b"RES,{}".format(axis))
        
    def zero_stage(self):
        """
        Moves stage and focus to zero (0,0,0)
        """
        self.ps_cmd(b"M")
        
        
        