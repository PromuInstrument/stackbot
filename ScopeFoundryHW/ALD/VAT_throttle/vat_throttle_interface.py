'''
Created on Dec 19, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

import serial
import time
from threading import Lock


class VAT_Throttle_Interface(object):
	
	"""
	Interface level ScopeFoundry module for VAT Throttle Valve control.
	Creates serial object used to connect to VAT Throttle Valve Controller via RS232 connection.
	
	Contains serial command library for use with Throttle Valve Controller.
	"""

	name = 'vat_throttle_interface'

	def __init__(self, port='COM1', debug=False):
		"""
		Creates 
		:class:`Serial` object and serial connection to VAT Throttle Valve Controller.
		
		:attr:`self.port` is the serial port address of the valve controller

		"""
		self.port = port
		self.debug = debug
		self.lock = Lock()
		
		self.port = port
		self.ser = serial.Serial(port=self.port, baudrate=38400, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=1, timeout=0.5, write_timeout=0.5)
		self.ser.flush()
		time.sleep(1)		

	def write_cmd(self, cmd):
		"""Sends encoded ASCII command to VAT Throttle Valve Controller."""
		message = cmd+'\r\n'
		with self.lock:
			self.ser.write(message.encode())
			resp = self.ser.readline().decode()
		return resp

	def set_local(self):
		"""
		This command turns over RS232 control to software.
		
		Function called by :meth:`connect` at hardware level.
		"""
		self.write_cmd("c:0100")
		

	def valve_open(self, open=False):
		"""Opens or closes VAT throttle valve.
		=============  ==========  ==========================================================
		**Arguments**  **Type**	   **Description**
		open		   bool		   If True, valve will be set to full open, closed otherwise.
		=============  ==========  ========================================================== 
		"""
		key = {True: 'O:',
				False: 'C:'}
		resp = self.write_cmd(key[bool(open)])
		
	def read_position(self):
		cmd = "A:"
		resp = self.write_cmd(cmd)
# 		print(resp.strip()[2:])
		str_value = resp.strip()[2:]
		return float(str_value)/100
	
	def write_position(self, position):
		cmd = "R:{:06.0f}".format(position*100)
		self.write_cmd(cmd)

	def read_status(self):
		cmd = 'i:76'
		resp = self.write_cmd(cmd)
		return resp

	def close(self):
		self.ser.close()
		del self.ser