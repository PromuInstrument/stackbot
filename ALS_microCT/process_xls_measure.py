from ScopeFoundry.measurement import Measurement
import time
import xlrd # for importing excel spreadsheets


class ChamberProcessXLSMeasure(Measurement):
    
    name = 'chamber_process_xls'
    
    def setup(self):
        
        self.settings.New("xls_fname", dtype='file')
    
    def run(self):
        data_list = read_spreadsheet(self.settings['xls_fname'])
        
        #start data logger
        self.app.measurements['chamber_data_log'].settings['activation'] = True
        
        t0 = time.time()
        
        # Turn on lamps
        self.app.hardware['lambda_zup1'].settings['output_enable'] = True
        self.app.hardware['lambda_zup2'].settings['output_enable'] = True

        try:
            for D in data_list:
                if self.interrupt_measurement_called:
                    break
    
                print( D )
                t = time.time()
                
                while  D['time'] > t:
                    if self.interrupt_measurement_called:
                        break
                    time.sleep(0.001)
                    t = time.time()
                
                row = D.copy()
                row.pop('time')
                
                for lq_path, new_val in row.items():
                    lq = self.app.lq_path(lq_path)
                    lq.update_value(new_val)
        finally:
            # turn off lamps
            self.app.hardware['lambda_zup1'].settings['output_enable'] = False
            self.app.hardware['lambda_zup2'].settings['output_enable'] = False

            
            # set flow to zero
            self.app.hardware['sierra_mfc'].settings['setpoint'] = 0



        
        


#Converts spreadsheet.xlsx file with headers into dictionaries
def read_spreadsheet(filepath):
    workbook=xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)

    # imports first row and converts to a list of header strings
    headerList = []
    for col_index in range(worksheet.ncols):
        headerList.append(str(worksheet.cell_value(0,col_index)))

    dataList = []
    # For each row, create a dictionary and like header name to data 
    # converts each row to following format rowDictionary1 ={'header1':colvalue1,'header2':colvalue2,... }
    # compiles rowDictinaries into a list: dataList = [rowDictionary1, rowDictionary2,...]
    for row_index in range(1,worksheet.nrows):
        rowDictionary = {}
        for col_index in range(worksheet.ncols):
            cellValue = worksheet.cell_value(row_index,col_index)

            #if type(cellValue)==unicode:
            #    cellValue = str(cellValue)
            
            # if cell contains string that looks like a tuple, convert to tuple
            #if '(' in str(cellValue):
            #    cellValue = literal_eval(cellValue)

            # if cell contains string or int that looks like 'True', convert to boolean True
            if str(cellValue).lower() =='true' or (type(cellValue)==int and cellValue==1):
                cellValue = True

            # if cell contains string or int that looks like 'False', convert to boolean False
            if str(cellValue).lower() =='false' or (type(cellValue)==int and cellValue==0):
                cellValue = False

            if cellValue != '': # create dictionary element if cell value is not empty
                rowDictionary[headerList[col_index]] = cellValue
        dataList.append(rowDictionary)

    return(dataList)