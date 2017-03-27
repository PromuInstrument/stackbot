from ScopeFoundry import Measurement
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import time

class SEMAlignMeasure(Measurement):
    
    name = 'sem_align'
    
    def setup(self):
        
        self.ui = self.dockarea = dockarea.DockArea()
        
        self.sem_controls = self.app.hardware['sem_remcon'].settings.New_UI()
        
        self.dockarea.addDock(name='SEM Settings', position='left', widget=self.sem_controls)
        
            #stig=============
        self.stig_plot = pg.PlotWidget()
        self.stig_plot.setAspectLocked(1.0)
        
        #self.stig_boundary = pg.RectROI([0,0],[100,100], centered=True, movable=False)
        a = 100
        self.stig_plot.plot([-a, a, a, -a, -a], [-a,-a, a, a, -a])
        
        self.stig_pt_roi = pg.RectROI([0,0], size=pg.Point(1,1), movable=True)

        
        self.stig_plot.addItem(self.stig_pt_roi)
        
        #self.stig_pt_roi.removeHandle(0)
        self.stig_pt_roi.handleSize = 25
        #self.stig_pt_roi.addTranslateHandle((0,0))
        
        
        self.dockarea.addDock(name='Stigmation', position='right', widget=self.stig_plot)
        
        self.stig_plot.showGrid(x=True, y=True, alpha=1.0)
        
        self.stig_pt_roi.sigRegionChanged[object].connect(self.on_update_stig_roi)
        
        self.stig_roi_moving=False
        def _start(x):
            print("start moving")
            self.stig_roi_moving=True
        def _finish(x):
            print("finish moving")
            self.stig_roi_moving=False
        self.stig_pt_roi.sigRegionChangeStarted[object].connect(_start)
        self.stig_pt_roi.sigRegionChangeFinished[object].connect(_finish)
         
        self.sem = self.app.hardware['sem_remcon']
        
        self.sem.settings.stig_xy.add_listener(self.on_update_stig_xy)
        
        self.last_stig_update = time.time()
        self.stig_update_interval = 0.050
    
            #focus==============
        self.wd_plot = pg.PlotWidget()
        self.wd_plot.invertY(True)
        self.dockarea.addDock(name='Focus', position='left', widget=self.wd_plot)
        
        self.wd_line = pg.InfiniteLine(1, angle=0, pen=pg.mkPen((0,9), width=4), movable=True)
        self.wd_plot.addItem(self.wd_line)
        self.wd_lim0 = pg.InfiniteLine(0, angle=0, pen=(2,9), movable=False)
        self.wd_plot.addItem(self.wd_lim0)        
        self.wd_lim1 = pg.InfiniteLine(50, angle=0, pen=(2,9), movable=False)
        self.wd_plot.addItem(self.wd_lim1)   
        
        self.wd_line.sigDragged.connect(self.on_update_wd_line)     
        
    
    def on_update_wd_line(self, line=None):
        self.sem.settings['WD'] = self.wd_line.getYPos()

    def on_update_stig_roi(self, roi=None):
        
        if self.stig_roi_moving:
            if roi is None:
                roi = self.stig_pt_roi
            
            roi_state = roi.saveState()
            x, y = roi_state['pos']
            t = time.time()
            if t - self.last_stig_update > self.stig_update_interval:
                #print("time elapsed", t - self.last_stig_update , 'going')
                self.sem.settings['stig_xy'] = [x,y]
                self.last_stig_update = t
            
    def on_update_stig_xy(self):
        if not self.stig_roi_moving:
            self.stig_pt_roi.setPos(*self.sem.settings['stig_xy'])
        
class PointROI(pg.ROI):
    
    def __init__(self, pos, **args):
        #QtGui.QGraphicsRectItem.__init__(self, 0, 0, size[0], size[1])
        pg.ROI.__init__(self, pos, size=pg.Point(0,0), **args)
        
        self.handleSize = 25
        self.addTranslateHandle((0,0))
    
        