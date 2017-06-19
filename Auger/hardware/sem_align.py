"""Module specific Xbox controller interfacing and GUI control by Alan Buckley"""


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
        self.controller = self.app.hardware['xbox_controller']
        
        self.ui = self.dockarea = dockarea.DockArea()
        
        self.ui.setWindowTitle("sem_align")
        
        self.sem_controls = self.app.hardware['sem_remcon'].settings.New_UI()
        
        
        
        self.roi_map = {'Focus': 'wd_line',
                'Beam Shift': 'beamshift_roi',
                'Stigmation': 'stig_roi',
                'Aperture Align': 'aper_roi'}
        
        self.lq_map = {'Focus': 'WD',
                'Beam Shift': 'beamshift_xy',
                'Stigmation': 'stig_xy',
                'Aperture Align': 'aperture_xy'}
        
        self.sem_align_widget_choices = ('Focus', 'Stigmation', 'Beam Shift', 'Aperture Align') 
        
        self.settings.New('active_widget', 
                            dtype=str,
                            initial='Focus',
                            ro=False,
                            choices=self.sem_align_widget_choices)
        
        
        
        a = 100
        
        #aperture=========
        self.aper_plot = pg.PlotWidget()
        self.aper_plot.setAspectLocked(1.0)
        self.aper_plot.plot([-a, a, a, -a, -a], [-a,-a, a, a, -a])
        
        self.aper_roi = PointLQROI(pos=[0,0], size=(a,a), pen=(0,9), movable=True)
        self.aper_plot.addItem(self.aper_roi)
        self.aper_roi.connect_lq(self.sem.settings.aperture_xy)
        self.aper_roi.removeHandle(0)
        
        self.aper_plot.showGrid(x=True, y=True, alpha=1.0)
        
        if hasattr(self, 'controller'):
            self.sem.settings.aperture_xy.add_listener(self.aper_roi.setPos, float)
        
        #stig=============
        self.stig_plot = pg.PlotWidget()
        self.stig_plot.setAspectLocked(1.0)
        
        self.stig_plot.plot([-a, a, a, -a, -a], [-a,-a, a, a, -a])
        
        self.stig_roi = PointLQROI(pos=[0,0], size=(a,a), pen=(0,9),  movable=True)
        self.stig_plot.addItem(self.stig_roi)
        self.stig_roi.connect_lq(self.sem.settings.stig_xy)
        
        self.stig_roi.removeHandle(0)
                
        
        self.stig_plot.showGrid(x=True, y=True, alpha=1.0)
        
        if self.controller:
            self.sem.settings.stig_xy.add_listener(self.stig_roi.setPos, float)        
        
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
                
        
        self.beamshift_plot.showGrid(x=True, y=True, alpha=1.0)

        if self.controller:
            self.sem.settings.beamshift_xy.add_listener(self.beamshift_roi.setPos, float) 
            
        #focus==============
        self.wd_widget = QtWidgets.QWidget()
        self.wd_widget.setLayout(QtWidgets.QVBoxLayout())
        
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
        
        
        

        
        
        
        self.dock_config()
        
        self.activate_focus_control()
        
    def dock_config(self):
        
        
        self.dockarea.addDock(name='Stigmation (Y)', position='right', widget=self.stig_plot)

        self.dockarea.addDock(name='Aperture Align (A)', position='right', widget=self.aper_plot)

        self.dockarea.addDock(name='Beam Shift (B)', position='bottom', widget=self.beamshift_plot)
        
        self.focus_dock = self.dockarea.addDock(name='Focus (X)', position='left', widget=self.wd_widget)
        
        self.sem_dock = self.dockarea.addDock(name='SEM Settings', position='left', widget=self.sem_controls)

        self.sem_dock.setMaximumWidth(400)
        self.focus_dock.setMaximumWidth(200)

    def activate_focus_control(self):
        self.settings.active_widget.update_value('Focus')
        obj_inv = self.wd_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]

        
    def activate_stig_control(self):
        self.settings.active_widget.update_value('Stigmation')
        obj_inv = self.stig_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]

        
    def activate_beam_control(self):
        self.settings.active_widget.update_value('Beam Shift')
        obj_inv = self.beamshift_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]

    def activate_aper_control(self):
        self.settings.active_widget.update_value('Aperture Align')
        obj_inv = self.aper_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]
    
    def load_control_profile(self):
        self.controller.settings.Y.add_listener(self.activate_stig_control)
        self.controller.settings.B.add_listener(self.activate_beam_control)
        self.controller.settings.A.add_listener(self.activate_aper_control)
        self.controller.settings.X.add_listener(self.activate_focus_control)
        self.controller.settings.RP.add_listener(self.recenter)

    def update_pos(self):
        profile = self.settings['active_widget']
        dx = self.controller.settings['Axis_4']
        dy = self.controller.settings['Axis_3']
        if abs(dx) < 0.25:
            dx = 0
        if abs(dy) < 0.25:
            dy = 0
        if dx != 0 or dy != 0:
            c = self.controller.settings.sensitivity.val/10
            if profile == 'Focus':
                _, y = getattr(self, self.roi_map[profile]).pos()
                coords = y-.5*c*dy
                getattr(self, self.roi_map[profile]).setPos(coords)
                getattr(self.sem.settings, self.lq_map[profile]).update_value(coords)
            else:
                x, y = getattr(self, self.roi_map[profile]).pos()
                coords = [x+c*dx, y-c*dy]
                getattr(self, self.roi_map[profile]).setPos(coords)
                getattr(self.sem.settings, self.lq_map[profile]).update_value(coords)
            

#             if profile == "Stigmation":
#                 c = self.controller.settings.sensitivity.val/10
#                 x, y = self.sem.settings.stig_xy.val
#                 self.sem.settings.stig_xy.update_value([x+c*dx, y-c*dy])
#             elif profile == "Beam Shift":
#                 c = self.controller.settings.sensitivity.val/10
#                 x, y = self.sem.settings.beamshift_xy.val
#                 self.sem.settings.beamshift_xy.update_value([x+c*dx, y-c*dy])
#             elif profile == "Focus":
#                 c = self.controller.settings.sensitivity.val/10
#                 y = self.sem.settings.WD.val
#                 self.sem.settings.WD.update_value(y+(.5*c*dy))
        else:
            pass       
         
    def update_pan(self):
        profile = self.settings['active_widget']
        du = self.controller.settings['Axis_0']
        dv = self.controller.settings['Axis_1']
        if profile == "Focus":
            c = self.controller.settings.sensitivity.val/2
        else:
            c = self.controller.settings.sensitivity.val/5

        if abs(du) < 0.25:
            du = 0
        if abs(dv) < 0.25:
            dv = 0
        if du != 0 or dv != 0:
            self.vb.translateBy((c*du,-c*dv))    

    def recenter(self):
        profile = self.settings['active_widget']
        if profile == "Focus":
            y = getattr(self, self.roi_map[profile]).getYPos()
            ymin, ymax = self.vb.viewRange()[1]
            midpoint_dist = (ymax - ymin)/2
            self.vb.setYRange(min=y-midpoint_dist, max=y+midpoint_dist)
        else:
            x, y = getattr(self, self.roi_map[profile]).pos()
            xmin, xmax = self.vb.viewRange()[0]
            ymin, ymax = self.vb.viewRange()[1]
            x_mid_dist = (xmax - xmin)/2
            y_mid_dist = (ymax - ymin)/2
            self.vb.setXRange(min=x-x_mid_dist, max=x+x_mid_dist)
            self.vb.setYRange(min=y-y_mid_dist, max=y+y_mid_dist)
            
            
    def update_zoom(self):
        """Zoom around cursor"""
        profile = self.settings['active_widget']
        if profile == 'Focus':
            y = self.wd_line.getYPos()
        else:
            x, y = getattr(self, self.roi_map[profile]).pos()
        ymin, ymax = self.vb.viewRange()[1]
        yrange = ymax - ymin
        self.controller.settings.sensitivity.update_value(yrange/10)
        dz = self.controller.settings['Axis_2']/10
        if abs(dz) < 0.05:
            dz = 0 
        if dz != 0:
            if profile == 'Focus':
                self.vb.scaleBy(s=(dz+1), center=(0,y))
            else:
                self.vb.scaleBy(s=(dz+1), center=(x,y))            

   
    def on_update_wd_line(self, line=None):
        self.sem.settings['WD'] = self.wd_line.getYPos()

    def on_wd_joystick(self, jb, state):
        dx, dy = state
        self.sem.settings['WD'] += -dy*1e-1
        print(jb, state)
        #print(self.wd_joystick.getState())


        
    def run(self):
        #Access equipment class:
        self.controller.connect()
        self.xb_dev = self.controller.xb_dev 
        self.joystick = self.xb_dev.joystick
        self.sensitivity = self.controller.settings['sensitivity']
        self.load_control_profile()
        self.dt = 0.05
        
        while not self.interrupt_measurement_called:  
            self.update_pos()
            self.update_pan()
            self.update_zoom()
            time.sleep(self.dt)
        
        else:
            pass

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
        #print("start moving")
        self.roi_drag=True
        
    def _finish_drag(self, x):
        #print("finish moving")
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
    
        