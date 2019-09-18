from ScopeFoundry.measurement import Measurement
import numpy as np
import pyqtgraph as pg
import time


class TiledLargeAreaMapMeasure(Measurement):
    
    name = "tiled_large_area_map"
    
    def setup(self):
        
        scale = self.settings.New("scale", dtype=float, unit='um', initial=50.)
        scale.add_listener(self.on_new_scale)
        
        self.add_operation('Snap', self.snap)
        
        self.snaps = []
        
        
    
    def setup_figure(self):
        self.graph_layout = self.ui= pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.plot.setAspectLocked(lock=True, ratio=1)
        

    
    
    def update_display(self):
        self.img_item.setImage(self.im)
        self.img_rect = self.get_current_rect()
        self.img_item.setRect(self.img_rect)
        self.img_item.setZValue(100)

    
    def get_current_rect(self, x=None, y=None):
        if x is None:
            fstage = self.app.hardware['mcl_xyz_stage']
            cstage = self.app.hardware['asi_stage']
            
            x = 1e3*cstage.settings['x_position'] + fstage.settings['x_position']
            y = 1e3*cstage.settings['y_position'] + fstage.settings['y_position']

        scale = self.settings['scale']
        
        return pg.QtCore.QRectF(x, y, scale, scale*3/4)
        
        
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

        while not self.interrupt_measurement_called:
            self.im = self.get_rgb_image()
            self.im = np.flip(self.im.swapaxes(0,1),0)
            time.sleep(0.1)
            
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
        
    def on_new_scale(self):
        for snap in self.snaps:
            
            x,y = snap['pos']

            snap['img_rect'] = self.get_current_rect(x,y)
            snap['img_item'].setRect(snap['img_rect'])


from qtpy import QtCore

class SnapsQTabelModel(QtCore.QAbstractTableModel):
    
    def __init__(self, snaps,*args, **kwargs):
        self.snaps  = snaps
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)
        
    def rowCount(self, *args, **kwargs):
        
    