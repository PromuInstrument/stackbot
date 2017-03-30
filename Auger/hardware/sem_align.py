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
                
        self.dockarea.addDock(name='Beam Shift', position='right', widget=self.beamshift_plot)
        
        self.beamshift_plot.showGrid(x=True, y=True, alpha=1.0)

        if self.controller:
            self.sem.settings.beamshift_xy.add_listener(self.beamshift_roi.setPos, float) 
            
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
        
    
    def update_focus_from_controller(self):
        dy = self.controller.settings['Axis_1']
        y = self.sem.settings.WD.val
        if abs(dy) < 0.15:
            dy = 0
        if dy != 0:
            self.sem.settings.WD.update_value(y+(0.25*dy))
        else:
            pass
        
    def update_stig_from_controller(self):
        dx = self.controller.settings['Axis_4']
        dy = self.controller.settings['Axis_3']
        c = self.controller.settings.sensitivity.val
        x, y = self.sem.settings.stig_xy.val
        if abs(dx) < 0.15:
            dx = 0
        if abs(dy) < 0.15:
            dy = 0
        if dx != 0 and dy != 0:
            self.sem.settings.stig_xy.update_value([x+c*dx, y+c*dy])
        else:
            pass
        
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
        self.sensitivity = self.controller.settings.sensitivity.val
        self.dt = 0.05

        
        while not self.interrupt_measurement_called:  
        
            self.update_stig_from_controller()
            self.update_focus_from_controller()
            if self.controller.settings['A'] == True:
                self.sem.settings.r_stick_control.update_value(1)
            elif self.controller.settings['B'] == True:
                self.sem.settings.r_stick_control.update_value(2)
            
            time.sleep(self.dt)
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.JOYAXISMOTION:
                    for i in range(self.xb_dev.num_axes):
                        self.controller.settings['Axis_' + str(i)] = self.joystick.get_axis(i)

                elif event.type == pygame.JOYHATMOTION:
                    for i in range(self.xb_dev.num_hats):
                        # Clear Directional Pad values
                        for k in set(self.controller.direction_map.values()):
                            self.controller.settings[k] = False

                        # Check button status and record it
                        resp = self.joystick.get_hat(i)
                        try:
                            self.controller.settings[self.controller.direction_map[resp]] = True
                        except KeyError:
                            self.log.error("Unknown dpad hat: "+ repr(resp))

                elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
                    button_state = (event.type == pygame.JOYBUTTONDOWN)

                    for i in range(self.xb_dev.num_buttons):
                        if self.joystick.get_button(i) == button_state:
                            try:
                                self.controller.settings[self.controller.button_map[i]] = button_state
                            except KeyError:
                                self.log.error("Unknown button: %i (target state: %s)" % (i,
                                    'down' if button_state else 'up'))

                else:
                    self.log.error("Unknown event type: {}".format(event.type))



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
    
        