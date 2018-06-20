
import serial
import time
from threading import Lock

class Ellipsometer(object):

	name = 'ellipsometer'

	def __init__(self, port='COM1', debug=False):
		self.port = port
		self.debug = debug
		self.lock = Lock()

		self.ser = serial.Serial(port=self.port, baudrate=9600, timeout=0.5, write_timeout=0.5)
		self.ser.flush()
		time.sleep(0.5)

	def write_cmd(self, cmd):
		self.ser.flush()
		message = cmd+'\r\n'
		with self.lock:
			self.ser.write(message)
			resp = self.ser.readline()
		return resp

	def close(self):
		self.ser.close()
		del self.ser