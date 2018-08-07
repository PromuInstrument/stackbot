'''
Created on Mar 28, 2018

@author: lab
'''
'''
@author: Alan Buckley
'''
import sqlite3
import time
import datetime
import random

class SQLite_Wrapper(object):

	"""
	This module is a SQLite wrapper which records pressure entries into a database (.db) file. 
	
	The module currently isn't used. 
	"""

	def __init__(self):\
		self.conn = sqlite3.connect('pressure_log.db', detect_types=sqlite3.PARSE_DECLTYPES)
		self.c = self.conn.cursor()

	def setup_table(self):
		self.c.execute('''CREATE TABLE IF NOT EXISTS PressureTable
				  (time TIMESTAMP, TKP1 REAL, TKP2 REAL, PKR3 REAL)''')

	def setup_index(self):
		self.c.execute('''CREATE INDEX IF NOT EXISTS TimeEntryIndex ON PressureTable (time)''')
	

	def data_entry(self, p1, p2, p3):
		"""
		Records three pressures into database.

		=============  ===============  =========================================
		**Arguments**  **Type**		 	**Description**
		p1			   float			Pressure TKP1 (Pirani Gauge)
		p2			   float			Pressure TKP2 (Pirani Gauge)
		p3			   float			Pressure PKR3 (Compact Full Range)
		=============  ===============  =========================================
		"""
		_datetime = datetime.datetime.now()
		self.c.execute("INSERT INTO PressureTable (time, TKP1, TKP2, PKR3) VALUES (?, ?, ?, ?)",
				  (_datetime, p1, p2, p3))
		self.conn.commit()

	def check_db(self):
		"""Checks if database is empty."""
		self.c.execute('SELECT Count(*) FROM PressureTable')
		size = self.c.fetchone()[0]
		if size > 0:
			self.setup_table()
			self.setup_index()
		else:
			pass

	def read_db_all(self):
		"""Select database contents in their entirety.
		:returns: list of tuples. Each tuple contains a datetime object, \
		and three floats corresponding to pressures"""
		self.c.execute("""SELECT * FROM PressureTable""")
		data = self.c.fetchall()
		return(data)

	def filter_time(self, t1, t2):
		"""
		Filter events by time
		:returns: list of tuples. Each tuple contains a datetime object, \
		and three floats corresponding to pressures
		"""
		self.c.execute("""SELECT * FROM PressureTable WHERE time BETWEEN ? AND ?""", (t1, t2))
		data = self.c.fetchall()
		return(data)

	def filter_pressures_time(self, t1, t2):
		"""
		Filter recorded pressures by time
		:returns: list of tuples. Each tuple contains \
		three floats corresponding to pressures
		"""
		self.c.execute("""SELECT TKP1, TKP2, PKR3 FROM PressureTable WHERE time BETWEEN ? AND ?""", (t1, t2))
		data = self.c.fetchall()
		return(data)

	def read_all_dates(self):
		"""
		Lists all date time objects.
		
		:returns: list of datetime objects.
		"""
		dates = []
		data = self.read_db_all()
		for i in data:
			dates.append(i[0])
		return(dates)
		
	def bobby_tables(self):
		"""Drop (Delete) PressureTable."""
		self.c.execute('''DROP TABLE IF EXISTS PressureTable''')
			
	def closeout(self):
		"""Close connection to SQLite database."""
		self.c.close()
		self.conn.close()