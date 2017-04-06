"""Module specific Xbox controller interfacing and GUI control by Alan Buckley"""


from ScopeFoundry import Measurement
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea
import time
from qtpy import QtWidgets
import pygame.event

class SEMAlignMeasure(Measurement):
    
    name = 'sem_align'
   
    controller_map = {'B': 'stig',
                      'A': 'beam',
                      'X': 'focus'}
   
    def setup(self):
        self.sem = self.app.hardware['sem_remcon']
        self.controller = self.app.hardware['xbox_controller']
        
        self.ui = self.dockarea = dockarea.DockArea()
        
        self.sem_controls = self.app.hardware['sem_remcon'].settings.New_UI()
        
        
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
                
        
        self.stig_plot.showGrid(x=True, y=True, alpha=1.0)
        
        if self.controller:
            self.sem.settings.stig_xy.add_listener(self.stig_pt_roi.setPos, float)        
        
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
        
        self.sem_align_widget_choices = ('Focus', 'Stigmation', 'Beam Shift') 
        
        self.settings.New('active_widget', 
                            dtype=str,
                            initial='Focus',
                            ro=False,
                            choices=self.sem_align_widget_choices)
        
        
        
        self.dock_config()
        self.load_control_profile()
        self.activate_focus_control()
        
    def dock_config(self):
        
        
        self.dockarea.addDock(name='Stigmation (B)', position='right', widget=self.stig_plot)

        self.dockarea.addDock(name='Beam Shift (A)', position='bottom', widget=self.beamshift_plot)
        
        self.dockarea.addDock(name='Focus (X)', position='left', widget=self.wd_widget)
        
        self.dockarea.addDock(name='SEM Settings', position='left', widget=self.sem_controls)


    def activate_focus_control(self):
        self.settings.active_widget.update_value('Focus')
        obj_inv = self.wd_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]
        self.update_pos()
        self.update_pan()
        
    def activate_stig_control(self):
        self.settings.active_widget.update_value('Stigmation')
        obj_inv = self.stig_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]
        self.update_pos()
        self.update_pan()
        
    def activate_beam_control(self):
        self.settings.active_widget.update_value('Beam Shift')
        obj_inv = self.beamshift_plot.items()
        self.vb = list(filter(lambda x: isinstance(x, pg.graphicsItems.ViewBox.ViewBox), obj_inv))[0]
        self.update_pos()
        self.update_pan()
            
    def load_control_profile(self):
        self.controller.settings.B.add_listener(self.activate_stig_control)
        self.controller.settings.A.add_listener(self.activate_beam_control)
        self.controller.settings.X.add_listener(self.activate_focus_control)
        

    def update_pos(self):
        profile = self.settings['active_widget']
        dx = self.controller.settings['Axis_4']
        dy = self.controller.settings['Axis_3']
        c = self.controller.settings.sensitivity.val
        if abs(dx) < 0.25:
            dx = 0
        if abs(dy) < 0.25:
            dy = 0
        if dx != 0 or dy != 0:
            if profile == "Stigmation":
                x, y = self.sem.settings.stig_xy.val
                self.sem.settings.stig_xy.update_value([x+c*dx, y-c*dy])
            elif profile == "Beam Shift":
                x, y = self.sem.settings.beamshift_xy.val
                self.sem.settings.beamshift_xy.update_value([x+c*dx, y-c*dy])
            elif profile == "Focus":
                y = self.sem.settings.WD.val
                self.sem.settings.WD.update_value(y+(c*dy))
        else:
            pass       
        
    def update_pan(self):
        c = self.controller.settings.sensitivity.val
        du = self.controller.settings['Axis_0']*c
        dv = self.controller.settings['Axis_1']*-c
                                      
        if abs(du) < 0.25:
            du = 0
        if abs(dv) < 0.25:
            dv = 0
        if du != 0 or dv != 0:
            self.vb.translateBy((du,dv))    

   
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
        self.dt = 0.05
        self.controller_measure = self.app.measurements['xbcontrol_mc']
        
        self.controller_measure.start()

        
        while not self.interrupt_measurement_called:  
            self.update_pos()
            self.update_pan()
            time.sleep(self.dt)
        
        else:
            self.controller_measure.interrupt()


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
    
        