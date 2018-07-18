
import socket
import time
from threading import Lock


class Ellipsometer_Interface(object):

	name = 'ellipsometer_interface'

	def __init__(self, host='192.168.0.1', port=4444, debug=False):
		self.debug = debug
		self.lock = Lock()

		self.socket = socket
		self.host = host  #address of computer running CompleteEASE
		self.port = port  #port number that CompleteEASE is listening on
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.settimeout(5.0)
		

	def write_cmd(self, cmd):
		message = cmd+'\r\n'
		with self.lock:
			self.sock.sendall(message.encode())
			data = self.sock.recv(1024)
		return data

	def close(self):
		self.sock.close()
		del self.sock