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
        self.stage_hw   = self.app.hardware['pi_piezo_stage']
        self.shutter_lq = self.app.hardware['shutter'].settings.laser_shutter
        
        self.settings.New('live_cam_show', dtype=bool, initial=True)
        self.settings.New('live_cam_cx', dtype=float, initial=512, unit='pixel')
        self.settings.New('live_cam_cy', dtype=float, initial=384, unit='pixel')
        self.settings.New('live_cam_scale', dtype=float, initial=0.001, spinbox_decimals=4, unit='um/pixel')

        
        self.ui_filename = sibling_path(__file__,"laser_line_writer.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        
        self.ui.update_move_display_pushButton.clicked.connect(self.update_move_display)
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)

    def move_stage_and_wait(self,x,y):
        #self.stage_hw.move_and_wait('x', x)
        #self.stage_hw.move_and_wait('y', y)
        S =self.stage_hw.settings 
        
        S['x_target'] = x
        S['y_target'] = y
        
        while not self.interrupt_measurement_called:
            S.x_position.read_from_hardware()
            S.y_position.read_from_hardware()
            x_ont = S.x_on_target.read_from_hardware()
            y_ont = S.y_on_target.read_from_hardware()
            time.sleep(0.005)
            
            if x_ont and y_ont:
                break
        
        
    
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
        
        self.stage_hw.settings.x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
        self.stage_hw.settings.y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)

        
    
        self.write_pen = pg.mkPen('r', width=5)
        self.line_item = self.img_plot.plot(pen = self.write_pen)
    
        self.img_plot.addItem(self.line_item)
        
        self.moves_item = MoveGraphicsItem(self.generate_moves)
        self.img_plot.addItem(self.moves_item)


        self.live_cam_img_item = pg.ImageItem()
        self.img_plot.addItem(self.live_cam_img_item)


        
    def generate_moves(self):
            #test pattern
        moves = (
            self.rect(10,10, 20,10) +
            self.cross(50,20, 10,10) +
            self.cross(100,100, 10,10) 
            )
        
        for ii in range(0,5):
            moves += self.digit(10+ii*10, 60,  w=5, h=10, N=ii)
        for ii in range(5,10):
            moves += self.digit(10+(ii-5)*10, 45,  w=5, h=10, N=ii)
        for ii in range(10,16):
            moves += self.digit(10+(ii-10)*10, 30,  w=5, h=10, N=ii)
        return moves
    
    def run(self):
        
        ###DEFINE MOVES HERE##################
        # x, y, open

        moves = self.generate_moves()
        # corner cross and labeling
        #moves = self.labeled_cross(35, 35, 10, N=1)

        #moves = self.h_arrow(10, 35, 50, 20)

        #moves = self.v_arrow(xtip=35, ytip=20, w=20, h=+50)
        #moves = self.v_arrow(xtip=35, ytip=10, w=20, h=+50)
        
#         moves = [
#                  ( 0, 0, False),
#                  ( 1, 0, True),
#                  ( 1, 1, True),
#                  ( 0, 1, True),
#                  ( 0, 0, True),
#         ]
        
        
        
        
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
        #print(open,self.is_shutter_open(),open != self.is_shutter_open())
        #while( True ):               
        #    print(self.name,'move_shutter_and_wait', open)
        #    if self.interrupt_measurement_called or (open == self.is_shutter_open()):
        #        break
        #    time.sleep(0.100)
        
        
    
    def move_shutter(self, open):
        
        #LASER_IN_SHUTTER_CLOSED_POS = 1        
        #LASER_IN_SHUTTER_OPEN_POS   = 25
        
        if open:
            self.shutter_lq.update_value(True)
            #self.app.hardware['laser_in_shutter'].settings['position'] = self.LASER_IN_SHUTTER_OPEN_POS
            #time.sleep(0.100)
        else:
            self.shutter_lq.update_value(False)
            #time.sleep(0.500)
            #self.app.hardware['laser_in_shutter'].settings['position'] = self.LASER_IN_SHUTTER_CLOSED_POS
            #time.sleep(0.100)
            
    def is_shutter_open(self):
        return self.shutter_lq.val
        #pos = self.app.hardware['laser_in_shutter'].settings['position']
        #return pos > 12.0
        
    def update_display(self):
        if self.settings['live_cam_show']:
            self.live_cam_img_item.setVisible(True)
            toup_cam_M = self.app.measurements['toupcam_live']
            im = toup_cam_M.get_rgb_image()
            self.live_cam_img_item.setImage(
                im.swapaxes(0,1), autoLevels=toup_cam_M.settings['auto_level'])
            
            Ny, Nx,_ = im.shape
            
            cx = self.settings['live_cam_cx']
            cy = self.settings['live_cam_cy']
            img_scale = self.settings['live_cam_scale'] # um/pixel
            
            x = self.stage_hw.settings['x_position']
            y = self.stage_hw.settings['y_position']

            w = Nx*img_scale
            h = Ny*img_scale
            self.live_cam_img_item.setRect(QtCore.QRectF(x-w/2, y-h/2, w, h))
            self.live_cam_img_item.setZValue(-1)
        else:
            self.live_cam_img_item.setVisible(False)
    
    def update_move_display(self):
        self.moves_item.generatePicture()
        self.moves_item.update()
    
    def update_arrow_pos(self):
        x = self.stage_hw.settings['x_position']
        y = self.stage_hw.settings['y_position']
        self.current_stage_pos_arrow.setPos(x,y)
        if self.shutter_lq.val:
            self.current_stage_pos_arrow.setStyle(brush=pg.mkBrush(color='r'))
        else:
            self.current_stage_pos_arrow.setStyle(brush=pg.mkBrush(color='b'))



    ############ MOVE PATTERNS
        
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

        
              
              

from qtpy import QtGui  
        
        
class MoveGraphicsItem(pg.GraphicsObject):
    def __init__(self, move_func):
        pg.GraphicsObject.__init__(self)
        self.move_func = move_func
        self.generatePicture()
    
    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        #w = (self.data[1][0] - self.data[0][0]) / 3.
        moves = self.move_func()
        for i, move in enumerate(moves[:-1]):
            x, y, open = move
            x1, y1, open1 = moves[i+1]

            print("move", i,'from',  x,y, open, 'to', x1,y1,open1)

            if open1:
                p.setBrush(pg.mkBrush('r'))
                p.setPen(pg.mkPen('r', width=2))
            else:
                p.setBrush(pg.mkBrush('g'))
                p.setPen(pg.mkPen(color='888',style=QtCore.Qt.DashLine))
            p.drawLine(QtCore.QPointF(x, y), QtCore.QPointF(x1, y1))

        p.end()
    
    def paint(self, p, *args):
        #self.generatePicture()
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QtCore.QRectF(self.picture.boundingRect())
        
        
        
        
        
        
       