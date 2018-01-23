from ScopeFoundry import Measurement
import time
from qtpy import  QtWidgets
from PyQt5.Qt import QFormLayout

class AttoCubeStageControlMeasure(Measurement):
    
    def __init__(self, app, name=None, hw_name='attocube_xyz_stage'):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)
    
    def setup(self):
        
        self.hw = self.app.hardware[self.hw_name]
        S = self.hw.settings
        
        self.ui = QtWidgets.QWidget()
        self.ui.setLayout(QtWidgets.QVBoxLayout())
        self.ctr_box = QtWidgets.QGroupBox("Attocube ECC 100: {} {}".format(self.name, self.hw_name))
        self.ctr_box.setLayout(QtWidgets.QHBoxLayout())
        self.ui.layout().addWidget(self.ctr_box, stretch=0)

        self.connect_checkBox = QtWidgets.QCheckBox("Connect to Hardware")
        self.ctr_box.layout().addWidget(self.connect_checkBox)
        S.connected.connect_to_widget(self.connect_checkBox)
        
        self.run_checkBox = QtWidgets.QCheckBox("Live Update")
        self.ctr_box.layout().addWidget(self.run_checkBox)
        self.settings.activation.connect_to_widget(self.run_checkBox)
        
        self.dev_id_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.ctr_box.layout().addWidget(self.dev_id_doubleSpinBox)
        S.device_id.connect_to_widget(self.dev_id_doubleSpinBox)


        self.axes_box = QtWidgets.QGroupBox("Axes")
        self.axes_box.setLayout(QtWidgets.QHBoxLayout())
        self.ui.layout().addWidget(self.axes_box, stretch=0)
        for i,axis in enumerate(self.hw.ax_names):
            names = [name for name in S.as_dict().keys() if name.split('_')[0] == axis]
            widget = S.New_UI(names)
            widget.layout().insertRow(0, "Axis {}".format(i+1), QtWidgets.QLabel("<B>{}</B>".format(axis)))
            self.axes_box.layout().addWidget(widget)
        
        self.ui.layout().addWidget(QtWidgets.QWidget(), stretch=1)
        
            
    def setup_figure(self):
        pass
    
    def run(self):
        
        while not self.interrupt_measurement_called:
            time.sleep(0.1)
            self.hw.read_from_hardware()
            pass
        
    def update_display(self):
        pass