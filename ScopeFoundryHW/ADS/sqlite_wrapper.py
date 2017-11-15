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
                  (time TIMESTAMP, prep_voltage REAL, nano_voltage REAL, prep_pressure REAL, nano_pressure REAL)''')

    def setup_index(self):
        self.c.execute('''CREATE INDEX IF NOT EXISTS TimeEntryIndex ON PressureTable (time)''')
    

    def data_entry(self, d1, d2, d3, d4):
        _datetime = datetime.datetime.now()
        self.c.execute("INSERT INTO PressureTable (time, prep_voltage, nano_voltage, prep_pressure, nano_pressure) VALUES (?, ?, ?, ?, ?)",
                  (_datetime, d1, d2, d3, d4))
        self.conn.commit()


    def read_db_all(self):
        self.c.execute("""SELECT * FROM PressureTable""")
        data = self.c.fetchall()
        return(data)

    def filter_time(self, d1, d2):
        self.c.execute("""SELECT * FROM PressureTable WHERE time BETWEEN ? AND ?""", (d1, d2))
        data = self.c.fetchall()
        return(data)

    def filter_pressures_time(self, d1, d2):
        self.c.execute("""SELECT prep_pressure, nano_pressure FROM PressureTable WHERE time BETWEEN ? AND ?""", (d1, d2))
        data = self.c.fetchall()
        return(data)

    def read_all_dates(self):
        dates = []
        data = self.read_db_all()
        for i in data:
            dates.append(i[0])
        return(dates)
        
    def read_all_prep(self):
        prep_data = []
        data = self.read_db_all()
        for i in data:
            prep_data.append(i[1])
        return(prep_data)
            
    def read_all_nano(self):
        nano_data = []
        data = self.read_db_all()
        for i in data:
            nano_data.append(i[2])
        return(nano_data)

    def test_log(self):
        for i in range(10):
            self.data_entry()
            time.sleep(1)
        
    def bobby_tables(self):
        self.c.execute('''DROP TABLE IF EXISTS PressureTable''')
            
    def closeout(self):
        self.c.close()
        self.conn.close()

