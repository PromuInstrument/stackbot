'''
Created on Aug 5, 2015
@author: Edward Barnard and Benedikt Ursprung
'''
import time
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file,replace_widget_in_layout

import pyqtgraph as pg
from qtpy import QtCore


class LaserLineWriter(Measurement):
    name = 'laser_line_writer'
    
    def setup(self):
        
        # Microscope specific (also provide move_stage_and_wait(x,y) )
        self.stage_hw   = self.app.hardware['attocube_xyz_stage']
        self.shutter_lq = self.app.hardware['pololu_servo_hw'].settings.servo2_toggle
        
        
        self.ui_filename = sibling_path(__file__,"laser_line_writer.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        
    def move_stage_and_wait(self,x,y):
        self.stage_hw.move_and_wait('x', x)
        self.stage_hw.move_and_wait('y', y)
    
    
    def clear_qt_attr(self, attr_name):
        if hasattr(self, attr_name):
            attr = getattr(self, attr_name)
            attr.deleteLater()
            del attr        
        
    def setup_figure(self):
        self.clear_qt_attr('graph_layout')
        self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.clear_qt_attr('img_plot')
        self.img_plot = self.graph_layout.addPlot()

        self.img_items = []
        
        
        self.img_item = pg.ImageItem()
        self.img_items.append(self.img_item)
        
        
        self.img_plot.addItem(self.img_item)
        self.img_plot.showGrid(x=True, y=True)
        self.img_plot.setAspectLocked(lock=True, ratio=1)
        
        
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(100)
        self.img_plot.addItem(self.current_stage_pos_arrow)
        
    
        self.write_pen = pg.mkPen('r', width=5)
        self.line_item = self.img_plot.plot(pen = self.write_pen)
    
        self.img_plot.addItem(self.line_item)

    
    
    def run(self):
        
        ###DEFINE MOVES HERE##################
        # x, y, open

               
        #test pattern
        moves = (
            self.rect(10,10, 20,10) +
            self.cross(50,20, 10,10) 
            )
        
        for ii in range(0,5):
            moves += self.digit(10+ii*10, 60,  w=5, h=10, N=ii)
        for ii in range(5,10):
            moves += self.digit(10+(ii-5)*10, 45,  w=5, h=10, N=ii)
        for ii in range(10,16):
            moves += self.digit(10+(ii-10)*10, 30,  w=5, h=10, N=ii)
        # corner cross and labeling
        #moves = self.labeled_cross(35, 35, 10, N=1)

        #moves = self.h_arrow(10, 35, 50, 20)

        #moves = self.v_arrow(xtip=35, ytip=20, w=20, h=+50)
        moves = self.v_arrow(xtip=35, ytip=10, w=20, h=+50)
        
        moves = [
                 ( 0, 0, False),
                 ( 1, 0, True),
                 ( 1, 1, True),
                 ( 0, 1, True),
                 ( 0, 0, True),
        ]
        
        
        
        
        ############################
        # RUN MOVES
        # close shutter
        self.move_shutter_and_wait(open=False)
        
        for move in moves:
            print(self.name , "move:", move)
            x, y, open = move
            self.move_shutter_and_wait(open=open)
            self.move_stage_and_wait(x=x, y=y)
            if self.interrupt_measurement_called:
                break
            
        # close shutter
        self.move_shutter(open=False)
        
        print(self.name , "done")
        
    
    def move_shutter_and_wait(self, open):
        self.move_shutter(open)
        print(open,self.is_shutter_open(),open != self.is_shutter_open())
        while( True ):               
            print(self.name,'move_shutter_and_wait', open)
            if self.interrupt_measurement_called or (open == self.is_shutter_open()):
                break
            time.sleep(0.100)
        
        
    
    def move_shutter(self, open):
        
        #LASER_IN_SHUTTER_CLOSED_POS = 1        
        #LASER_IN_SHUTTER_OPEN_POS   = 25
        
        if open:
            self.shutter_lq.update_value(True)
            #self.app.hardware['laser_in_shutter'].settings['position'] = self.LASER_IN_SHUTTER_OPEN_POS
            time.sleep(0.100)
        else:
            self.shutter_lq.update_value(False)
            #time.sleep(0.500)
            #self.app.hardware['laser_in_shutter'].settings['position'] = self.LASER_IN_SHUTTER_CLOSED_POS
            time.sleep(0.100)
            
    def is_shutter_open(self):
        return self.shutter_lq.val
        #pos = self.app.hardware['laser_in_shutter'].settings['position']
        #return pos > 12.0
        
    def update_display(self):
        pass
    
    def rect(self, xc, yc, w, h):
        x0 = xc - 0.5*w
        x1 = xc + 0.5*w
        y0 = yc - 0.5*h
        y1 = yc + 0.5*h
        return [
                 ( x0, y0, False),
                 ( x1, y0, True),
                 ( x1, y1, True),
                 ( x0, y1, True),
                 ( x0, y0, True),
        ]
    
    def cross(self, xc, yc, w, h):
        x0 = xc - 0.5*w
        x1 = xc + 0.5*w
        y0 = yc - 0.5*h
        y1 = yc + 0.5*h
        return [
                 ( x0, yc, False),
                 ( x1, yc, True),
                 ( xc, y0, False),
                 ( xc, y1, True),
        ]
        
    def digit(self, xc, yc, w, h, N):
        x0 = xc - 0.5*w
        x1 = xc + 0.5*w
        y0 = yc - 0.5*h
        y1 = yc + 0.5*h
        # Hexadecimal encodings for displaying the digits 0 to F
        num_encoding = [0x7E, 0x30, 0x6D, 0x79, 0x33, 0x5B, 0x5F, 0x70,
                        0x7F, 0x7B, 0x77, 0x1F, 0x4E, 0x3D, 0x4F, 0x47]
        abcdefg = num_encoding[N]
        open_shutter_list = [abcdefg >> i & 1 for i in range(6,-1,-1)]
        a,b,c,d,e,f,g = open_shutter_list
        
        moves = [
         (x0, y1, False),
         (x1, y1, a),
         (x1, yc, b),
         (x1, y0, c),
         (x0, y0, d),
         (x0, yc, e),
         (x0, y1, f),
         (x0, yc, False),
         (x1, yc, g),
        ]
        
        return moves
    
    def R(self, xc,yc, w, h):
        x0 = xc - 0.5*w
        x1 = xc + 0.5*w
        y0 = yc - 0.5*h
        y1 = yc + 0.5*h
        """ 
             x0 x1
          --------
        y1:  1 \
          :  |  2
        yc:  3 /
          :  |\
        y0:  0  4
        """
        
        return [
                (x0, y0, False),
                (x0, y1, True),
                (x1, 0.5*(yc+y1), True),
                (x0, yc, True),
                (x1, y0, True)
                ]
        
    def labeled_cross(self, xc, yc, h, N ):
        moves = []
        moves += self.cross(xc, yc, h, h)
        moves += self.digit(xc-1.5*h, yc, 0.5*h, h, N)
        moves += self.R(xc-2.5*h, yc, 0.5*h, h)
        return moves
    
    def v_arrow(self, xtip,ytip, w, h):
        # h < 0 up arrow
        # h > 0 down arrow
        
        y1 =ytip + h
        yhead = ytip + 0.25*h
        x0 = xtip - 0.5*w
        x1 = xtip + 0.5*w
        
        moves = [
                 (xtip, ytip, False),
                 (x0,   yhead, True),
                 (x1,   yhead, True),
                 (xtip, ytip, True),
                 (xtip, y1, True),
                 ]
        return moves
        
    def h_arrow(self, xtip, ytip, w, h):
        # w > 0 left point arrow
        # w < 0 right pointing arrow
        
        x1 = xtip + w
        xhead = xtip + 0.25*w
        y0 = ytip - 0.5*h
        y1 = ytip + 0.5*h
        
        moves = [
                 (xtip, ytip, False),
                 (xhead,   y0, True),
                 (xhead,   y1, True),
                 (xtip, ytip, True),
                 (x1, ytip, True),
                 ]
        return moves

        
                
        
        
        
        
        
        
        
        
        
       