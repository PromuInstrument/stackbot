import serial

class ESP300(object):
    
    def __init__(self, port='COM5', debug=False):
        self.debug = debug
        self.port = port
        
        self.ser = serial.Serial(port=self.port,
                                 baudrate=19200,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1,
                                 rtscts=True)
        
    
    def write_cmd(self, axis, cmd):
        full_cmd = '{}{}\r'.format(axis, cmd).encode('ascii')
        if self.debug:
            print('ESP300 write_cmd', repr(full_cmd))
        self.ser.write(full_cmd)
    
    def ask_cmd(self,axis,cmd):
        self.write_cmd(axis, cmd)
        resp = self.ser.readline()
        if self.debug:
            print('ESP300 ask_cmd', repr(resp))
        return resp
    
    def write_cmd_chain(self, cmds):
        cmd = []
        for ax, cmd in cmds:
            cmd.append("{}{}".format(ax,cmd))
        cmd = ";".join(cmd)
        self.ser.write(cmd.encode('ascii'))
    
    def read_pos(self, axis):
        return float(self.ask_cmd(axis, "TP?"))
    
    def write_pos_abs(self, axis, pos):
        self.write_cmd(axis, "PA{:+0.5f}".format(pos))

    def write_pos_rel(self, axis, delta_pos):
        self.write_cmd(axis, "PR{+0.5f}".format(delta_pos))

    #def write_pos_abs_and_wait(self, axis, pos):
    #    self.write_cmd_chain(
    #        [(axis, "PA{+0.5f}".format(pos)),
    #         (axis, "WS")]
    #                         )
    #def write_pos_rel_and_wait(self, axis, delta_pos):
    #    self.write_cmd_chain(
    #        [(axis, "PR{+0.5f}".format(delta_pos)),
    #         (axis, "WS")]
    #                         )
    
    def read_is_moving(self,axis):
        resp = self.ask_cmd(axis, "MD?")
        return not bool(int(resp))
       
    def read_enabled(self, axis):
        return bool(self.ask_cmd(axis, "MO?"))

    def write_enabled(self, axis, enabled):
        if enabled:
            self.write_cmd(axis, "MO")
        else:
            self.write_cmd(axis, "MF")
            
    def write_stop(self,axis):
        self.write_cmd(axis, "ST")
        
    def close(self):
        self.ser.close()


if __name__ == '__main__':
    import time
    
    esp = ESP300(port='COM5', debug=True)
    
    print(esp.read_pos(1))
    print(esp.read_enabled(1))
    print(esp.read_is_moving(1))
    #esp.write_pos_abs(1, -80)
    esp.write_pos_abs(1, 60)
    while(esp.read_is_moving(1)):
        time.sleep(2.0)
        print("still waiting" , esp.read_pos(1))
    
    esp.close()


