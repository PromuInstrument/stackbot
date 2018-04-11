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

    def __init__(self):
        self.conn = sqlite3.connect('pressure_log.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.c = self.conn.cursor()

    def connect(self):
        self.conn = sqlite3.connect('pressure_log.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.c = self.conn.cursor()

    def setup_table(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS PressureTable
                  (time TIMESTAMP, TKP1 REAL, TKP2 REAL, PKR3 REAL)''')

    def setup_index(self):
        self.c.execute('''CREATE INDEX IF NOT EXISTS TimeEntryIndex ON PressureTable (time)''')
    

    def data_entry(self, p1, p2, p3):
        _datetime = datetime.datetime.now()
        self.c.execute("INSERT INTO PressureTable (time, TKP1, TKP2, PKR3) VALUES (?, ?, ?, ?)",
                  (_datetime, p1, p2, p3))
        self.conn.commit()

    def check_db(self):
    	self.c.execute('SELECT Count(*) FROM PressureTable')
    	size = self.c.fetchone()[0]
    	if size > 0:
    		self.setup_table()
    		self.setup_index()
    	else:
    		pass

    def read_db_all(self):
        self.c.execute("""SELECT * FROM PressureTable""")
        data = self.c.fetchall()
        return(data)

    def filter_time(self, t1, t2):
        self.c.execute("""SELECT * FROM PressureTable WHERE time BETWEEN ? AND ?""", (t1, t2))
        data = self.c.fetchall()
        return(data)

    def filter_pressures_time(self, t1, t2):
        self.c.execute("""SELECT TKP1, TKP2, PKR3 FROM PressureTable WHERE time BETWEEN ? AND ?""", (t1, t2))
        data = self.c.fetchall()
        return(data)

    def read_all_dates(self):
        dates = []
        data = self.read_db_all()
        for i in data:
            dates.append(i[0])
        return(dates)
        
    def bobby_tables(self):
        self.c.execute('''DROP TABLE IF EXISTS PressureTable''')
            
    def closeout(self):
        self.c.close()
        self.conn.close()