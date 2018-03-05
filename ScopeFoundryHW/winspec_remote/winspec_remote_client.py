from __future__ import division, print_function
import socket
import time
import struct
from array import array

import ctypes as ct

class data_header(ct.Structure):
    _pack_ = 1
    _fields_ = [
        ('total_size', ct.c_int32),
        ('data_type', ct.c_int32),
        ('xdim', ct.c_int32),
        ('ydim', ct.c_int32),
        ('intg_time', ct.c_double),
        ('grating_pos', ct.c_double),
        ('calib_coeffs', ct.c_double*5),
        ('frame_count', ct.c_int32),
        ('data_size', ct.c_int32),
        ('bin_x', ct.c_int32),
        ('bin_y', ct.c_int32)
        ]

class WinSpecRemoteClient(object):

    def __init__(self, host="192.168.254.200", port=9000, debug=True):
    
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock.settimeout(2.0)
        self.debug = debug
        
    def ask_cmd(self, cmd):
        if self.debug:
            print(("ask", cmd))
        self.sock.send( ( cmd + "\n").encode('utf-8'))
        resp = self.read_socket()
        resp_parts = resp.split()
        
        if resp_parts[0]=='ok':
            return resp_parts
        elif  resp_parts[0]=='err':
            raise IOError(resp)
        
    def read_socket(self):
        
        resp_str = ""
        resp = self.sock.recv(1024)
        
        i = -1
        while(i < 0):
            resp_str += resp.decode('utf-8')
            i = resp_str.find('\n')
    
        assert len(resp_str) == i + 1
        if self.debug:
            print((resp_str.strip()))
        return resp_str.strip()

    def set_acq_time(self, t):
        self.ask_cmd('set_acq_time {:0.6f}'.format(float(t)))
    
    def get_acq_time(self):
        _, t = self.ask_cmd('get_acq_time')
        return float(t)
    
    def start_acq(self):
        self.ask_cmd('acquire')

    def get_status(self):
        _, stat = self.ask_cmd('status')
        return bool(int(stat))
    
    def get_data(self):
        self.sock.send("get_data\n".encode(encoding='utf_8'))
        
        hdr = data_header()
        hdr_size = ct.sizeof(hdr)
        hdr_bytes = self.sock.recv(hdr_size)
        ct.memmove(ct.addressof(hdr), hdr_bytes, hdr_size)
        
        # TODO handle error
        data = b""
        i = 0
        
        while i < hdr.data_size:
            new_data = self.sock.recv(hdr.data_size)
            data += new_data
            i += len(new_data)
        
        a = object()
        if hdr.data_type == 3:
            # 4-byte floats
            a = array('f')
            a.fromstring(data)
            #intensity = struct.unpack('<f')
            #pass
        elif hdr.data_type == 2:
            # 4 bytes signed int
            a = array('l')
            a.fromstring(data)
        elif hdr.data_type == 1:
            # 2 bytes signed int
            a = array('h')
            a.fromstring(data)
        elif hdr.data_type == 6:
            # 2 bytes unsigned int
            a = array('H')
            a.fromstring(data)
        elif hdr.data_type == 5:
            # byte
            a = array('B')
            a.fromstring(data)

        return hdr, a
    
    def reinitialize(self):
        self.ask_cmd('reinitialize')
        
if __name__ == '__main__':
    
    from matplotlib import pyplot as plt

    W = WinSpecRemoteClient(host="192.168.236.128")
    print((W.set_acq_time(5.0)))
    print((W.get_acq_time()))
    print((W.get_status()))
    
    
    W.start_acq()
    time.sleep(1.0)
    hdr, data = W.get_data()
    
    print(hdr)
    print(data)
    
    W.reinitialize()
    
    W.start_acq()
    time.sleep(1.0)
    hdr, data = W.get_data()
    
    print(hdr)
    print(data)
    
    
    plt.figure()
    plt.plot(data)
    plt.show()
    
    