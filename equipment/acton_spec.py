import serial
import time

class ActonSpectrometer(object):

    def __init__(self, port, debug=False, dummy=False):
        
        self.debug = debug
        self.dummy = dummy
        
        if not self.dummy:
            self.ser = serial.Serial(port=port, baudrate = 2400, bytesize=8, parity='N',
                                    stopbits=1, xonxoff=0, rtscts=0, timeout=5.0)
         
            self.ser.flushInput()
            self.ser.flushOutput()
        # model info
        #self.write_command("MONO-RESET")
        self.model = self.write_command("MODEL")
        self.serial_number = self.write_command("SERIAL")
        # load grating info
        
    
    def read_done_status(self):
        resp = self.write_command("MONO-?DONE")  # returns either 1 or 0 for done or not done
        return bool(int(resp))
    
    def read_wl(self):
        resp = self.write_command("?NM")
        "700.000 nm"
        self.wl = float(resp.split()[0])
        return self.wl
        
    def write_wl(self, wl, waittime=1.0):
        wl = float(wl)
        resp = self.write_command("%0.3f NM" % wl,waittime=waittime)
        pass

    def write_wl_nonblock(self, wl):
        wl = float(wl)
        resp = self.write_command("%0.3f >NM" % wl)
        pass
        
    def read_grating_info(self):
        grating_string = self.write_command("?GRATINGS", waittime=1.0)
        """
            \x1a1  300 g/mm BLZ=  500NM 
            2  300 g/mm BLZ=  1.0UM 
            3  150 g/mm BLZ=  500NM 
            4  Not Installed     
            5  Not Installed     
            6  Not Installed     
            7  Not Installed     
            8  Not Installed     
            9  Not Installed     
            ok
        """
        # 0x1A is the arrow char, indicates selected grating
        
        gratings = grating_string.splitlines()[0:-1]
        
        self.gratings = []
        
        for grating in gratings:
            if self.debug: print grating
            grating = str(grating).strip("\x1a ").split()
            if self.debug: print grating
            num = int(grating[0])
            name = " ".join(grating[1:])
            self.gratings.append( (num, name) )
        
        self.gratings_dict = {num: name for num,name in self.gratings}
        
        return self.gratings
        
    def read_turret(self):
        resp = self.write_command("?TURRET")
        self.turret = int(resp)
        return self.turret
    
    def write_turret(self, turret):
        assert turret in [1,2,3]
        "%i TURRET"
    
    def read_grating(self):
        resp = self.write_command("?GRATING")
        self.grating = int(resp)
        return self.grating
        
    def write_grating(self, grating):
        assert 0 < grating < 10 
        self.write_command("%i GRATING" % grating)
        pass        
        
    def read_exit_mirror(self):
        resp = self.write_command("EXIT-MIRROR ?MIRROR")
        self.exit_mirror = resp.upper()
        return self.exit_mirror
    
    def write_exit_mirror(self, pos):
        pos = pos.upper()
        assert pos in ['FRONT', 'SIDE']
        "EXIT-MIRROR %s" % pos
        pass
        
    def read_entrance_slit(self):
        resp = self.write_command("SIDE-ENT-SLIT ?MICRONS")
        "480 um"
        self.entrance_slit = int(resp.split()[0])
        return self.entrance_slit
        
    def write_entrance_slit(self, pos):
        assert 10 <= pos <= 3000
        "SIDE-ENT-SLIT %i MICRONS" % pos
        pass
        # should return new pos

    def home_entrance_slit(self):
        "SIDE-ENT-SLIT SHOME"

        
    def read_exit_slit(self):
        resp = self.write_command("SIDE-EXIT-SLIT ?MICRONS")
        "960 um"
        self.exit_slit = int(resp.split()[0])
        return self.exit_slit
        
    def write_exit_slit(self, pos):
        assert 10 <= pos <= 3000
        "SIDE-EXIT-SLIT %i MICRONS" % pos

#    def write_command(self, cmd):
#        if self.debug: print "write_command:", cmd
#        self.ser.write(cmd + "\r\n")
#        response = self.ser.readline()
#        if self.debug: print "\tresponse:", repr(response)
#        assert response[-4:] == "ok\r\n"
#        return response[:-4].strip()
    
    def write_command(self, cmd, waittime=0.5):
        if self.debug: print "cmd: ", cmd
        if self.dummy: return "0"
        self.ser.write(cmd +"\r")
        time.sleep(waittime)
        
        out = bytearray()
        char = ""
        missed_char_count = 0
        while char != "k":
            char = self.ser.read()
            #if self.debug: print "readbyte", repr(char)
            if char == "": #handles a timeout here
                missed_char_count += 1
                if self.debug: print "no character returned, missed %i so far" % missed_char_count
                if missed_char_count > 3:
                    return 0
                continue
            out.append(char)

        
        out += self.ser.read(2) #Should be "\r\n"

        if self.debug: print "complete message", repr(out)
        
        #assert out[-3:] == ";FF"
        #assert out[:7] == "@%03iACK" % self.address   
        
        print "asdf", repr(out[-5:])
        assert out[-5:] == bytearray(" ok\r\n")
        return out[:-5].strip()
        
        self.ser.flushInput()
        self.ser.flushOutput()

        
        return out
        
        