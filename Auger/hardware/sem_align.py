from ScopeFoundry import Measurement
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import time
from qtpy import QtWidgets
import pygame.event

class SEMAlignMeasure(Measurement):
    
    name = 'sem_align'
   
    def setup(self):
        self.sem = self.app.hardware['sem_remcon']
        
        self.ui = self.dockarea = dockarea.DockArea()
        
        self.sem_controls = self.app.hardware['sem_remcon'].settings.New_UI()
        
        self.dockarea.addDock(name='SEM Settings', position='left', widget=self.sem_controls)
        
        #stig=============
        self.stig_plot = pg.PlotWidget()
        self.stig_plot.setAspectLocked(1.0)
        
        a = 100
        # Boundary
        self.stig_plot.plot([-a, a, a, -a, -a], [-a,-a, a, a, -a])
        
        self.stig_pt_roi = PointLQROI(pos=[0,0], size=(a,a), pen=(0,9),  movable=True)
        self.stig_plot.addItem(self.stig_pt_roi)
        self.stig_pt_roi.connect_lq(self.sem.settings.stig_xy)
        
        self.stig_pt_roi.removeHandle(0)
                
        self.dockarea.addDock(name='Stigmation', position='right', widget=self.stig_plot)
        
        self.stig_plot.showGrid(x=True, y=True, alpha=1.0)
        
        
        #beam shift=============
        self.beamshift_plot = pg.PlotWidget()
        self.beamshift_plot.setAspectLocked(1.0)
        
        a = 100
        # Boundary
        self.beamshift_plot.plot([-a, a, a, -a, -a], [-a,-a, a, a, -a])
        
        self.beamshift_roi = PointLQROI(pos=[0,0], size=(a,a), pen=(0,9),  movable=True)
        self.beamshift_plot.addItem(self.beamshift_roi)
        self.beamshift_roi.connect_lq(self.sem.settings.beamshift_xy)
        
        self.beamshift_roi.removeHandle(0)
                
        self.dockarea.addDock(name='Beam Shift', position='right', widget=self.beamshift_plot)
        
        self.beamshift_plot.showGrid(x=True, y=True, alpha=1.0)
            
        #focus==============
        self.wd_widget = QtWidgets.QWidget()
        self.wd_widget.setLayout(QtWidgets.QVBoxLayout())
        self.dockarea.addDock(name='Focus', position='left', widget=self.wd_widget)
        
        self.wd_joystick = pg.JoystickButton()
        self.wd_joystick.sigStateChanged.connect(self.on_wd_joystick)
        self.wd_widget.layout().addWidget(self.wd_joystick, stretch=1)
        
        self.wd_plot = pg.PlotWidget()
        self.wd_plot.invertY(True)
        self.wd_widget.layout().addWidget(self.wd_plot, stretch=1)
        
        
        self.wd_line = pg.InfiniteLine(1, angle=0, pen=pg.mkPen((0,9), width=4), movable=True)
        self.wd_plot.addItem(self.wd_line)
        self.wd_lim0 = pg.InfiniteLine(0, angle=0, pen=(2,9), movable=False)
        self.wd_plot.addItem(self.wd_lim0)        
        self.wd_lim1 = pg.InfiniteLine(50, angle=0, pen=(2,9), movable=False)
        self.wd_plot.addItem(self.wd_lim1)   
        
        self.wd_line.sigDragged.connect(self.on_update_wd_line)     
        self.sem.settings.WD.add_listener(self.wd_line.setPos, float)
        
            
    def on_update_wd_line(self, line=None):
        self.sem.settings['WD'] = self.wd_line.getYPos()

    def on_wd_joystick(self, jb, state):
        dx, dy = state
        self.sem.settings['WD'] += -dy*1e-1
        print(jb, state)
        #print(self.wd_joystick.getState())

        



class PointLQROI(pg.CrosshairROI):
    """
    An ROI that can track an (x,y) style array logged quantity
    """
    
    def __init__(self, pos=None, size=None, **kargs):
        pg.CrosshairROI.__init__(self, pos=pos, size=size, **kargs)
        
        self.lq = None
        self.roi_drag=False

        self.sigRegionChangeStarted[object].connect(self._start_drag)
        self.sigRegionChangeFinished[object].connect(self._finish_drag)
        self.sigRegionChanged[object].connect(self.on_update_roi)
        
        #self.removeHandle(0)
        
    def connect_lq(self, lq):
        self.lq = lq
        lq.add_listener(self.on_update_lq)
        

    def _start_drag(self, x):
        print("start moving")
        self.roi_drag=True
        
    def _finish_drag(self, x):
        print("finish moving")
        self.roi_drag=False
        
    def on_update_roi(self, _=None):
        if self.roi_drag:
            roi_state = self.saveState()
            x, y = roi_state['pos']

            if self.lq:
                self.lq.update_value([x,y])

    def on_update_lq(self):
        if not self.roi_drag:
            x, y = self.lq.val
            self.setPos(x,y)


class PointROI(pg.ROI):
    
    def __init__(self, pos, **args):
        #QtGui.QGraphicsRectItem.__init__(self, 0, 0, size[0], size[1])
        pg.ROI.__init__(self, pos, size=pg.Point(0,0), **args)
        
        self.handleSize = 25
        self.addTranslateHandle((0,0))
    
        