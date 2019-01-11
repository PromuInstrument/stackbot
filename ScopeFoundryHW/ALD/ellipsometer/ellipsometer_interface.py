
import socket
import time
from threading import Lock


class Ellipsometer_Interface(object):
	
	"""
	Interface level ScopeFoundry module for Woolam Ellipsometer control.
	Creates object used to connect to Ellipsometer via RJ45 connection over TCP/IP protocol.
	"""

	name = 'ellipsometer_interface'

	def __init__(self, host='192.168.0.1', port=4444, debug=False):
		"""
		Creates 
		:class:`Lock` object and TCP/IP connection to Woolam Ellipsometer.
		
		* :attr:`self.host` is the IP address of the computer
		* :attr:`self.port` is the port CompleteEASE is listening on.
		(Convert to table if successfully rendered)
		"""
		
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