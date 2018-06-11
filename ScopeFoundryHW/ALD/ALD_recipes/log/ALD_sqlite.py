'''
@author: Alan Buckley
'''
import sqlite3
import time
import datetime
import random

class ALD_sqlite(object):

    def __init__(self):
        self.conn = sqlite3.connect('ald_log.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.c = self.conn.cursor()

    def connect(self):
        self.conn = sqlite3.connect('ald_log.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.c = self.conn.cursor()

    def setup_table(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS ParameterTable \
                  (time TIMESTAMP, cycle_no INTEGER, step_no INTEGER, \
                  step_name TEXT, shutter_on INTEGER, PKR_pressure REAL, \  
                mano_pressure REAL, forward_power INTEGER, reflected_power INTEGER, \
                  mfc_flow REAL,  valve_position REAL, pv_temp REAL, setpoint REAL, \
                  p REAL, i INTEGER, d INTEGER)''')

    def setup_index(self):
        self.c.execute('''CREATE INDEX IF NOT EXISTS TimeEntryIndex ON \
        		ParameterTable (time)''')
    

    def data_entry(self, entries):
        _datetime = datetime.datetime.now()
        assert len(entries) == 15
        self.c.execute("INSERT INTO ParameterTable (time, cycle_no, step_no, \
        		step_name, shutter_on, PKR_pressure, mano_pressure, forward_power, \
        		reflected_power, mfc_flow, valve_position, pv_temp, setpoint, \
        		p, i, d) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (_datetime, *entries))
        self.conn.commit()


    def read_db_all(self):
        self.c.execute("""SELECT * FROM ParameterTable""")
        data = self.c.fetchall()
        return(data)

    def filter_time(self, d1, d2):
        self.c.execute("""SELECT * FROM ParameterTable WHERE time BETWEEN ? AND ?""", (d1, d2))
        data = self.c.fetchall()
        return(data)

    def read_all_dates(self):
        dates = []
        data = self.read_db_all()
        for i in data:
            dates.append(i[0])
        return(dates)
        
    def bobby_tables(self):
        self.c.execute('''DROP TABLE IF EXISTS ParameterTable''')
            
    def closeout(self):
        self.c.close()
        self.conn.close()
        del self.c
        del self.conn
