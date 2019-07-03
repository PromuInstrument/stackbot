from ScopeFoundry.measurement import Measurement
import pyqtgraph as pg
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class GalvoScannerControlMeasure(Measurement):
    
    name = 'galvo_control'
    
    def setup(self):
        self.stage = self.app.hardware['galvo_scanner']
    
    def setup_figure(self):
        
        #self.ui = self.graph_layout = pg.GraphicsLayoutWidget()
        
        self.ui = load_qt_ui_file(sibling_path(__file__, 'galvo_scanner_control.ui'))
    
        self.ui.pos_plot.showGrid(True,True)
        self.ui.pos_plot.showAxis('right')
        self.ui.pos_plot.showAxis('top')
        self.ui.pos_plot.setContentsMargins(0,0,0,0)
        self.ui.pos_plot.setLimits(xMin=-7.5, xMax=+7.5, yMin=-7.5, yMax=+7.5)
        self.ui.pos_plot.setRange(xRange=(-7.5,+7.5),yRange=(-7.5,+7.5))
        self.ui.pos_plot.setAspectLocked(lock=True, ratio=1)
        
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(100)
        self.ui.pos_plot.addItem(self.current_stage_pos_arrow)
        
        #self.stage = self.app.hardware_components['dummy_xy_stage']
        self.stage.settings.x_position_deg.updated_value.connect(self.update_arrow_pos, pg.QtCore.Qt.UniqueConnection)
        self.stage.settings.y_position_deg.updated_value.connect(self.update_arrow_pos, pg.QtCore.Qt.UniqueConnection)
        
        #self.stage.settings.x_position_deg.connect_to_widget(self.ui.x_doubleSpinBox)
        #self.stage.settings.y_position_deg.connect_to_widget(self.ui.y_doubleSpinBox)
        
        self.circ_roi_size = 1.0
        self.pt_roi = pg.CircleROI( (0,0), (self.circ_roi_size,self.circ_roi_size) , movable=True, pen=(0,9))            
        h = self.pt_roi.addTranslateHandle((0.5,0.5))
        h.pen = pg.mkPen('r')
        h.update()
        self.ui.pos_plot.addItem(self.pt_roi)
        self.pt_roi.removeHandle(0)
        self.pt_roi.sigRegionChangeFinished[object].connect(self.on_update_pt_roi)
        
        self.trajectory_plotline = self.ui.pos_plot.plot(pen=(0,9))
        
    def update_arrow_pos(self):
        x = self.stage.settings['x_position_deg']
        y = self.stage.settings['y_position_deg']
        self.current_stage_pos_arrow.setPos(x,y)

    def on_update_pt_roi(self, roi=None):
        if roi is None:
            roi = self.circ_roi
        roi_state = roi.saveState()
        x0, y0 = roi_state['pos']
        xc = x0 + self.circ_roi_size/2.
        yc = y0 + self.circ_roi_size/2.
        #self.new_pt_pos(xc,yc)
        self.stage.settings['x_target_deg'] = xc
        self.stage.settings['y_target_deg'] = yc
        
        self.trajectory_plotline.setData(self.stage.ao_data[:,0]/1.33, self.stage.ao_data[:,1]/1.33)
        
        
    
    
#     def run(self):
#         self.first_run = True
#     
#     def update_display(self):
#         if self.first_run:
#             self.graph_layout.clear()
#             self.xy_plot =  self.graph_layout.addPlot()
#             