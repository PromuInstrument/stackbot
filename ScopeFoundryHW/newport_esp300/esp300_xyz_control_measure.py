from ScopeFoundry import Measurement
from qtpy.QtWidgets import QWidget, QGridLayout, QLabel, QDoubleSpinBox, QCheckBox, QPushButton
from pyqtgraph import SpinBox

class ESP300XYZStageControlMeasure(Measurement):
    
    name = 'esp300_xyz_stage'
    
    def __init__(self, app, name=None, hw_name='esp300_xyz_stage'):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)
        self.hw = self.app.hardware[self.hw_name]
        
    
    def setup(self):
        pass
    
    def setup_figure(self):
        
        self.ui = QWidget()
        
        layout = QGridLayout()
        self.ui.setLayout(layout)
        
        headers = ['name', 'position', 'target_position', 'enabled', 'is_moving', "<<", ">>", 'delta']
        
        for jj, header in enumerate(headers):
            layout.addWidget(QLabel(header), 0,jj)
        # Additional column for stretch
        layout.addWidget(QLabel(""), 0,jj+1)
        layout.setColumnStretch(jj+1, 1)
        
        
        for ii, axis in enumerate(self.hw.ax_names):
            if axis == '_' or axis == None:
                for jj, header in enumerate(headers):
                    layout.addWidget(QLabel("------"), ii+1,jj)
                continue
            
            for jj, header in enumerate(headers):
                
                if header == 'name':
                    layout.addWidget(QLabel(axis), ii+1,jj)
    
                elif header == 'position':
                    widget = QDoubleSpinBox()
                    layout.addWidget(widget, ii+1,jj)               
                    self.hw.settings.get_lq(axis + "_position").connect_to_widget(widget)
                    #widget.setOpts(siPrefix=False)
                elif header == 'target_position':
                    widget = QDoubleSpinBox()
                    layout.addWidget(widget, ii+1,jj)               
                    self.hw.settings.get_lq(axis + "_target_position").connect_to_widget(widget)
                    #widget.setOpts(siPrefix=False)
                elif header == 'enabled':
                    widget = QCheckBox()
                    layout.addWidget(widget, ii+1,jj)               
                    self.hw.settings.get_lq(axis + "_enabled").connect_to_widget(widget)
                elif header == 'is_moving':
                    widget = QCheckBox()
                    layout.addWidget(widget, ii+1,jj)               
                    self.hw.settings.get_lq(axis + "_is_moving").connect_to_widget(widget)
                elif header == '<<':
                    widget = QPushButton("<<")
                    layout.addWidget(widget, ii+1,jj)
                    def on_left(hw=self.hw, axis=axis):
                        hw.move_step_delta(axis, dir=-1)
                    widget.pressed.connect(on_left)
                    
                elif header == '>>':
                    widget = QPushButton(">>")
                    layout.addWidget(widget, ii+1,jj)
                    def on_right(hw=self.hw, axis=axis):
                        hw.move_step_delta(axis, dir=+1)
                    widget.pressed.connect(on_right)
                    
                elif header == "delta":
                    widget = SpinBox()
                    layout.addWidget(widget, ii+1,jj)
                    self.hw.settings.get_lq(axis + "_step_delta").connect_to_widget(widget)
                    
        
        # Additional row for stretch
        layout.addWidget(QLabel(""), ii+2, 0)
        layout.setRowStretch(ii+2,1)
                    