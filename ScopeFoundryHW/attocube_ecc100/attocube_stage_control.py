from ScopeFoundry import Measurement
import time
from qtpy import  QtWidgets

class AttoCubeStageControlMeasure(Measurement):
    
    def setup(self):
        
        S = self.app.hardware['attocube_xyz_stage'].settings
        
        self.ui = QtWidgets.QWidget()
        self.ui.setLayout(QtWidgets.QVBoxLayout())
        self.ctr_box = QtWidgets.QGroupBox("ECC 100")
        self.ctr_box.setLayout(QtWidgets.QHBoxLayout())
        self.ui.layout().addWidget(self.ctr_box, stretch=0)

        self.connect_checkBox = QtWidgets.QCheckBox("Connect to Hardware")
        self.ctr_box.layout().addWidget(self.connect_checkBox)
        S.connected.connect_to_widget(self.connect_checkBox)
        
        self.run_checkBox = QtWidgets.QCheckBox("Live Update")
        self.ctr_box.layout().addWidget(self.run_checkBox)
        self.settings.activation.connect_to_widget(self.run_checkBox)


        self.axes_box = QtWidgets.QGroupBox("Axes")
        self.axes_box.setLayout(QtWidgets.QHBoxLayout())
        self.ui.layout().addWidget(self.axes_box, stretch=0)
        for axis in 'xyz':
            names = [name for name in S.as_dict().keys() if name[0] == axis]
            widget = S.New_UI(names)
            self.axes_box.layout().addWidget(widget)
        
        self.ui.layout().addWidget(QtWidgets.QWidget(), stretch=1)
        
            
    def setup_figure(self):
        pass
    
    def run(self):
        
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
            self.app.hardware['attocube_xyz_stage'].read_from_hardware()
            pass
        
    def update_display(self):
        pass