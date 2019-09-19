from ScopeFoundry.measurement import Measurement
import numpy as np
import pyqtgraph as pg
import time
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt


class TiledLargeAreaMapMeasure(Measurement):
    
    name = "tiled_large_area_map"
    
    new_snap_signal = QtCore.Signal()
    
    def setup(self):
        
        img_scale = self.settings.New("img_scale", dtype=float, unit='um', initial=50.)
        img_scale.add_listener(self.on_new_img_scale)
        
        
        self.settings.New("center_x", dtype=float, unit='%', initial=50)
        self.settings.New("center_y", dtype=float, unit='%', initial=50)
        
        self.add_operation('Snap', self.snap)
        
        self.snaps = []
        
        
    
    def setup_figure(self):
        self.graph_layout = self.ui= pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.img_item.setZValue(1000)

        self.plot.setAspectLocked(lock=True, ratio=1)
        
        """self.table_view = QtWidgets.QTableView()
        
        self.table_view_model = SnapsQTabelModel(snaps=self.snaps)
        self.table_view.setModel(self.table_view_model)
        self.table_view.show()
        
        self.new_snap_signal.connect(self.table_view_model.on_update_snaps)
        """
        
        self.plot.scene().sigMouseClicked.connect(self.on_scene_clicked)
        
        self.graph_layout_eventProxy = EventProxy(self.graph_layout, self.graph_layout_event_filter)
        
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(1001)
        self.plot.addItem(self.current_stage_pos_arrow)
        
        fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']

        fstage.settings.x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
        fstage.settings.y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
        cstage.settings.x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
        cstage.settings.y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)


        self.fine_stage_border_plotline = self.plot.plot([0,1,1,0],[0,0,1,1],pen='r')

    def update_arrow_pos(self):
        x,y = self.get_current_stage_position()
        
        fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']
        
        fx, fy = fstage.settings['x_position'] , fstage.settings['y_position']
        cx, cy = 1e3*cstage.settings['x_position'] , 1e3*cstage.settings['y_position']

        x0 = cx
        x1 = x0 + fstage.settings['x_max']
        y0 = cy
        y1 = y0 + fstage.settings['y_max']
        
        self.fine_stage_border_plotline.setData(
            [x0, x1,x1,x0, x0], [y0, y0, y1, y1,y0]
            )
        
        self.fine_stage_border_plotline.setZValue(1002)

        #print(x, cx+fx, y, cy+fy)
        
        self.current_stage_pos_arrow.setPos(cx+fx,cy+fy)
    
    
    def update_display(self):
        self.img_item.setImage(self.im)
        self.img_rect = self.get_current_rect()
        self.img_item.setRect(self.img_rect)
        
    def get_current_stage_position(self):
        fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']
        
        x = 1e3*cstage.settings['x_position'] + fstage.settings['x_position']
        y = 1e3*cstage.settings['y_position'] + fstage.settings['y_position']
        return x,y
    
    def get_current_rect(self, x=None, y=None):
        if x is None:
            x,y = self.get_current_stage_position()
        scale = self.settings['img_scale']
        S = self.settings
        return pg.QtCore.QRectF(x-S['center_x']*scale/100,
                                y-S['center_y']*scale*self.im_aspect/100, 
                                scale,
                                scale*self.im_aspect)
        
        
    def get_rgb_image(self):
        cam = self.app.hardware['toupcam'].cam

        data = cam.get_image_data()
        raw = data.view(np.uint8).reshape(data.shape + (-1,))
        bgr = raw[..., :3]
        return bgr[..., ::-1]


    def run(self):
        
        tcam = self.app.hardware['toupcam']
        tcam.settings['connected'] = True
        
        
        fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']

        fstage.settings['connected'] = True
        cstage.settings['connected'] = True
        
        self.im = self.get_rgb_image()
        self.im = np.flip(self.im.swapaxes(0,1),0)
        self.im_aspect = self.im.shape[1]/self.im.shape[0]
        
        from ScopeFoundry import h5_io

        try:
            self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
            H = self.h5_meas_group  =  h5_io.h5_create_measurement_group(self, self.h5_file)
    
            self.snaps_h5 = H.create_dataset('snaps', (self.im.shape + (1,)), dtype=np.uint8, maxshape=(self.im.shape +(None,)))
            self.snaps_c_pos_h5 = H.create_dataset('snaps_coarse_pos', (2,1), dtype='float', maxshape=(2,None))
            self.snaps_f_pos_h5 = H.create_dataset('snaps_fine_pos', (2,1), dtype='float', maxshape=(2,None))
            self.snaps_pos_h5 = H.create_dataset('snaps_pos', (2,1), dtype='float', maxshape=(2,None))
    
            while not self.interrupt_measurement_called:
                self.im = self.get_rgb_image()
                self.im = np.flip(self.im.swapaxes(0,1),0)
                self.im_aspect = self.im.shape[1]/self.im.shape[0]
                time.sleep(0.1)
        finally:
            self.h5_file.close()
            
    def snap(self):

        snap = dict()
        
        snap['img_item'] = pg.ImageItem(self.im)
        snap['img_rect'] = self.get_current_rect()
        snap['img_item'].setRect(snap['img_rect'])
        
        fstage = self.app.hardware['mcl_xyz_stage'] # Fine
        cstage = self.app.hardware['asi_stage'] # Coarse
        
        snap['fine_pos'] = (fstage.settings['x_position'], fstage.settings['y_position'])
        snap['coarse_pos'] = (cstage.settings['x_position']*1e3, cstage.settings['y_position']*1e3)
        
        fx, fy = snap['fine_pos']
        cx, cy = snap['coarse_pos']

        snap['pos'] = (cx+fx, cy+fy)
        
        self.plot.addItem(snap['img_item'])
        self.snaps.append(snap)
        print ("SNAP")
                

        ## Write to H5
        self.snaps_h5.resize((self.im.shape +( len(self.snaps),)))
        self.snaps_h5[:,:,:,-1] = self.im
        print("shape", self.snaps_h5.shape)
        self.snaps_c_pos_h5.resize((2, len(self.snaps)))
        self.snaps_c_pos_h5[:,-1] = snap['coarse_pos']
        self.snaps_f_pos_h5.resize((2, len(self.snaps)))
        self.snaps_f_pos_h5[:,-1] = snap['fine_pos']
        self.snaps_pos_h5.resize((2, len(self.snaps)))
        self.snaps_pos_h5[:,-1] = snap['pos']
        
        # TODO update LQ's in H5
        
        self.new_snap_signal.emit()
        

        
    def on_new_img_scale(self):
        for snap in self.snaps:
            
            x,y = snap['pos']

            snap['img_rect'] = self.get_current_rect(x,y)
            snap['img_item'].setRect(snap['img_rect'])

    def on_scene_clicked(self, event):
        p = self.plot
        viewbox = p.vb
        pos = event.scenePos()
        if not p.sceneBoundingRect().contains(pos):
            return
                
        pt = viewbox.mapSceneToView(pos)
        print("on_scene_clicked", pt.x(), pt.y())
        
        
        x = pt.x()
        y = pt.y()
        
        
        fstage = self.app.hardware['mcl_xyz_stage']
        cstage = self.app.hardware['asi_stage']
        
        fx, fy = fstage.settings['x_position'] , fstage.settings['y_position']
        cx, cy = 1e3*cstage.settings['x_position'] , 1e3*cstage.settings['y_position']

        #x0,y0 = self.get_current_stage_position()
        x0 = cx + fx
        y0 = cy + fy
        
        dx = x - x0
        dy = y - y0
        
        print("dx, dy", dx,dy)
        
        #self.plot.plot([x0,x],[y0,y], pen='r')


        
        
        # Move coarse stage
        if  event.modifiers() == QtCore.Qt.ShiftModifier and event.double():            
            print('Shift+Click', 'double click')
                        
#             cstage.settings['x_target'] = (x-fx)/1000
#             cstage.settings['y_target'] = (y-fy)/1000
            cstage.settings['x_target'] = cstage.settings['x_position'] + 1e-3*dx
            cstage.settings['y_target'] = cstage.settings['y_position'] + 1e-3*dy
            
        # Move fine stage
        if  event.modifiers() == QtCore.Qt.ControlModifier and event.double():            
            print('Shift+Click', 'double click')
            
            
            fstage.settings['x_target'] = fstage.settings['x_position'] + dx
            fstage.settings['y_target'] = fstage.settings['y_position'] + dy

    def graph_layout_event_filter(self, obj,event):
        #print(self.name, 'eventFilter', obj, event)
        try:
            if type(event) == QtGui.QKeyEvent:
                if event.key() == QtCore.Qt.Key_Space:
                    self.snap()
                    print(event.key(), repr(event.text()))
        
        finally:
            # standard event processing            
            return QtCore.QObject.eventFilter(self,obj, event)


class EventProxy(QtCore.QObject):
    def __init__(self, qobj, callback):
        QtCore.QObject.__init__(self)
        self.callback = callback
        qobj.installEventFilter(self)
        
    def eventFilter(self, obj, ev):
        return self.callback(obj, ev)


class SnapsQTabelModel(QtCore.QAbstractTableModel):
    
    def __init__(self, snaps,*args, **kwargs):
        self.snaps  = snaps
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)
        
    def rowCount(self, *args, **kwargs):
        return len(self.snaps)
    
    def columnCount(self, *args, **kwargs):
        return 5
    
    
    def on_update_snaps(self):
        self.layoutChanged.emit()
        
    def data(self, index, role=Qt.DisplayRole):
        print("table model data", index, role)
        if index.isValid():
            print("valid")
            if role == Qt.DisplayRole or role==Qt.EditRole:
                row = index.row()
                col = index.column()
                text = "{} {}".format(row,col)
                print(text, index)
                return text 
        else:
            print("no data", index)
            return None

    