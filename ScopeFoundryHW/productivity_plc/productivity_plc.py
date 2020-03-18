from ScopeFoundry.hardware import HardwareComponent
import pandas
import re
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import time
from ScopeFoundry.base_app import BaseMicroscopeApp

class ProductivityPLC(HardwareComponent):
    
    name = "productivity_plc"
    
    # tag, addres_start, address_stop, dtype
    
    
    def __init__(self, app, debug=False, name=None, tags_csv_filename=None):
        self.tags_csv_filename = tags_csv_filename
        
        # Parse tag database
        self.tags_df = df = pandas.read_csv(self.tags_csv_filename, engine='python', 
                                       skiprows = [1],  header=0, index_col=False)
        
        self.modbus_tags_df = df[df['MODBUS Start Address'].notnull()]
        
        self.tag_db = dict()
        
        clean = lambda varStr: re.sub('\W|^(?=\d)','_', varStr) # convert tag names to valid python variable names
        
        for i, x in self.modbus_tags_df.iterrows():
            tag_info = dict()
            tag_info['name']  = clean( x['Tag Name'] )
            tag_info['modbus_start'] = int( x['MODBUS Start Address'] )
            tag_info['modbus_stop'] = int( x['MODBUS End Address'] )
            tag_info['initial_value'] = x['Initial Value']
            
            tag_info['dtype'] = 'int'
            tag_info['unit'] = None
            
            mb0 = tag_info['modbus_start'] -1            
            tag_info['read_only'] = False
            if 300000 <= mb0 < 400000:
                tag_info['read_only'] = True
            elif 100000 <= mb0 < 200000:
                tag_info['read_only'] = True
            
            
            self.tag_db[tag_info['name']] = tag_info

        
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    
    def setup(self):
        
        self.settings.New("ip_address", dtype=str, initial="192.168.2.11")
        
        
        for name, tag in self.tag_db.items():
            
            self.settings.New(name, dtype=tag['dtype'], unit=tag['unit'], ro = tag['read_only'])
            
            
    def connect(self):
        pass
    
    def disconnect(self):
        pass


    def threaded_update(self):
        self.read_all_tags()
        time.sleep(0.1)
    
    
    def read_all_tags(self):
        try:
            c = ModbusClient(host="192.168.2.11", port=502, debug=False)
            c.open()
            
            for name, tag in self.tag_db.items():
                mb0 = tag['modbus_start'] -1
                mb1 = tag['modbus_stop'] -1
                size = 1+mb1-mb0
                #print(name, mb0, mb1, size)
                #print(tag)
                if 0 <= mb0 < 100000:
                    val = c.read_coils(mb0)[0]
                elif 100000 <= mb0 < 200000:
                    val = c.read_discrete_inputs(mb0-100000)[0]
                elif 300000 <= mb0 < 400000:
                    val = c.read_input_registers(mb0-300000,  size)
                    if size == 1: val = val[0]
                    elif size == 2:
                        val = utils.word_list_to_long(val, big_endian=False)[0]
                elif 400000 <= mb0 < 500000:
                    val = c.read_holding_registers(mb0-400000,  size )
                    if size == 1: val = val[0]
                    elif size == 2:
                        val = utils.word_list_to_long(val, big_endian=False)[0]
                
                if tag['dtype'] == 'float32':
                    val = utils.decode_ieee(val)
                
                #print(name, val)
                self.settings[name] = val
                    
        except Exception as err:
            print("Error in read_all_tags", err)
            c.close()        
            
            
if __name__ == '__main__':
    
    class TestApp(BaseMicroscopeApp):
        def setup(self):
            self.add_hardware(ProductivityPLC(self, tags_csv_filename='modbus_test_plc_Basic.csv'))
    
    app = TestApp()
    app.exec_()