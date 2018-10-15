'''
Created on Apr 11, 2018

@author: Alan Buckley <alanbuckley@berkeley.edu>
                      <alanbuckley@lbl.gov>
'''

from ScopeFoundry import Measurement
from ScopeFoundry.ndarray_interactive import ArrayLQ_QTableModel
from PyQt5 import QtWidgets
from ScopeFoundryHW.ALD.ALD_recipes import resources
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
import numpy as np
import datetime
import time
import os


class ALD_Display(Measurement):
    
    '''
    - Generates the user interface layout including user input fields and \
    output fields displaying ALD sensor data
    - Creates and updates any plots with data stored in arrays.
    - This module also checks whether certain conditions in the ALD system environment are met.
    
    *LoggedQuantities* in \
    :class:`ALD_Recipe` are connected to indicators defined here within 
    :meth:`setup_conditions_widget`.
    

    '''
    
    
    name = 'ALD_display'
    
    def __init__(self, app):
        Measurement.__init__(self, app)        
        
    def setup(self):
        self.cb_stylesheet = '''
        QCheckBox::indicator {
            width: 25px;
            height: 25px;
        }
        QCheckBox::indicator:checked {
            image: url(://icons//GreenLED.png);
        }
        QCheckBox::indicator:unchecked {
            image: url(://icons//RedLED.png);
        }
        '''

        self.settings.New('RF_pulse_duration', dtype=int, initial=1)
        self.settings.New('history_length', dtype=int, initial=1e6, vmin=1, ro=True)
        self.settings.New('shutter_open', dtype=bool, initial=False, ro=True)
        self.settings.New('display_window', dtype=int, initial=1e4, vmin=1)

        self.setup_buffers_constants()
        self.resources = resources
        
        self.settings.New('save_path', dtype=str, initial=self.full_file_path, ro=False)

        self.ch1_scaled = self.settings.New(name='ch1_pressure', dtype=float, initial=0.0, fmt='%.4e', si=True, spinbox_decimals=6, ro=True)
        self.ch2_scaled = self.settings.New(name='ch2_pressure', dtype=float, initial=0.0, fmt='%.4e', si=True, spinbox_decimals=6, ro=True)
        self.ch3_scaled = self.settings.New(name='ch3_pressure', dtype=float, initial=0.0, fmt='%.4e', si=True, spinbox_decimals=6, ro=True)
        

        
        if hasattr(self.app.hardware, 'seren_hw'):
            self.seren = self.app.hardware.seren_hw
            if self.app.measurements.seren.psu_connected:
                print('Seren PSU Connected')
            else:
                print('Connect Seren HW component first.')

        if hasattr(self.app.hardware, 'ald_shutter'):
            self.shutter = self.app.hardware.ald_shutter
        else:
            print('Connect ALD shutter HW component first.')
        
        if hasattr(self.app.hardware, 'lovebox'):
            self.lovebox = self.app.hardware.lovebox
        
        if hasattr(self.app.hardware, 'mks_146_hw'):
            self.mks146 = self.app.hardware.mks_146_hw
        
        if hasattr(self.app.hardware, 'mks_600_hw'):
            self.mks600 = self.app.hardware.mks_600_hw
        
        if hasattr(self.app.hardware, 'pfeiffer_vgc_hw'):
            self.vgc = self.app.hardware.pfeiffer_vgc_hw
        
        if hasattr(self.app.measurements, 'ALD_Recipe'):
            self.recipe = self.app.measurements.ALD_Recipe
        else:
            print('ALD_Recipe not setup')
            
        self.ui_enabled = True
        if self.ui_enabled:
            self.ui_setup()
                    
        self.connect_indicators()
        self.ui_initial_defaults()

    
    def connect_indicators(self):
        '''Connects *LoggedQuantities* to UI indicators using :meth:`connect_to_widget`'''
        self.recipe.settings.pumping.connect_to_widget(self.pump_down_indicator)
        self.recipe.settings.predeposition.connect_to_widget(self.pre_deposition_indicator)
        self.recipe.settings.deposition.connect_to_widget(self.deposition_indicator)
        self.recipe.settings.vent.connect_to_widget(self.vent_indicator)
        self.recipe.settings.pumped.connect_to_widget(self.pumped_indicator)
        self.recipe.settings.gases_ready.connect_to_widget(self.gases_ready_indicator)
        self.recipe.settings.substrate_hot.connect_to_widget(self.substrate_indicator)
        self.recipe.settings.recipe_running.connect_to_widget(self.recipe_running_indicator)
        self.recipe.settings.recipe_completed.connect_to_widget(self.recipe_ready_indicator)
        self.seren.settings.RF_enable.connect_to_widget(self.plasma_on_indicator)
        
    
    def update_subtable(self):
        """
        Updates subroutine table tableWidget (UI element)
        Called by :meth:`app.measurements.ALD_recipe.subroutine_sum` after the 
        subroutine time table summation has been calculated.
        """
        self.subtableModel.on_lq_updated_value()

    def update_table(self):
        """
        Updates the main time table tableWidget (UI element)
        Called by :attr:`app.measurements.ALD_recipe.sum_times` after the 
        time table summation has been calculated.
        """
        self.tableModel.on_lq_updated_value()

    def ui_setup(self):
        '''Calls all functions needed to set up UI programmatically.
        This object is called from :meth:`setup`'''
        self.ui = DockArea()
        self.layout = QtWidgets.QVBoxLayout()
        self.ui.show()
        self.ui.setWindowTitle('ALD Control Panel')
        self.ui.setLayout(self.layout)
        self.widget_setup()
        self.dockArea_setup()

    def dockArea_setup(self):
        """
        Creates dock objects and determines order of dockArea widget placement in UI.
        
        This function is called from 
        :meth:`ui_setup`
        """
        self.rf_dock = Dock('RF Settings')
        self.rf_dock.addWidget(self.rf_widget)
        self.ui.addDock(self.rf_dock)

        self.thermal_dock = Dock('Thermal History')
        self.thermal_dock.addWidget(self.thermal_widget)
        self.ui.addDock(self.thermal_dock, position='right', relativeTo=self.rf_dock)
        
        self.recipe_dock = Dock('Recipe Controls')
        self.recipe_dock.addWidget(self.recipe_control_widget)
        self.ui.addDock(self.recipe_dock, position='bottom')

        self.display_ctrl_dock = Dock('Display Controls')
        self.display_ctrl_dock.addWidget(self.display_control_widget)
        self.ui.addDock(self.display_ctrl_dock, position='bottom', relativeTo=self.recipe_dock)

        self.hardware_dock = Dock('Hardware')
        self.hardware_dock.addWidget(self.hardware_widget)
        self.ui.addDock(self.hardware_dock, position='top')
        
        self.conditions_dock = Dock('Conditions')
        self.conditions_dock.addWidget(self.conditions_widget)
        self.ui.addDock(self.conditions_dock, position='left', relativeTo=self.hardware_dock)

        self.operations_dock = Dock('Operations')
        self.operations_dock.addWidget(self.operations_widget)
        self.ui.addDock(self.operations_dock, position='left', relativeTo=self.conditions_dock)
        
    def load_ui_defaults(self):
        pass
    
    def save_ui_defaults(self):
        pass
    
    def ui_initial_defaults(self):
        '''Reverts the indicator arrays to their original state after deposition operations 
        have concluded or have been interrupted.
        This function is called from 
        :meth:`widget_setup` and 
        :meth:`setup`
        '''
        
        self.pump_down_button.setEnabled(False)
        self.pre_deposition_button.setEnabled(True)
        self.deposition_button.setEnabled(False)
        self.vent_button.setEnabled(False)
        
        self.pumped_button.setEnabled(False)
        self.gases_ready_button.setEnabled(False)
        self.plasma_on_button.setEnabled(False)
        self.substrate_button.setEnabled(False)
        self.recipe_running_button.setEnabled(False)
        self.recipe_complete_button.setEnabled(False)
        self.pre_deposition_button.clicked.connect(self.recipe.predeposition)
        self.deposition_button.clicked.connect(self.recipe.run_recipe)
        self.vent_button.clicked.connect(self.recipe.shutoff)

        
    
    def widget_setup(self):
        """
        Runs collection of widget setup functions each of which creates the widget 
        and then populates them.
        This function is called from :meth:`ui_setup`
        """
        self.setup_operations_widget()
        self.setup_conditions_widget()
        self.setup_thermal_control_widget()
        self.setup_rf_flow_widget()
        self.setup_recipe_control_widget()
        self.setup_display_controls()
        self.setup_hardware_widget()

        self.ui_initial_defaults()
        
    def setup_conditions_widget(self):
        """
        Creates conditions widget which is meant to provide end user with an 
        array of LED indicators (and greyed out pushbuttons serving as labels.)
        which serve as indicators of desired conditions within the ALD recipe process.
        """
        
        self.conditions_widget = QtWidgets.QGroupBox('Conditions Widget')
        self.conditions_widget.setLayout(QtWidgets.QGridLayout())
        self.conditions_widget.setStyleSheet(self.cb_stylesheet)
        
        self.pumped_indicator = QtWidgets.QCheckBox()
        self.pumped_button = QtWidgets.QPushButton('Pumped')
        self.conditions_widget.layout().addWidget(self.pumped_indicator, 0, 0)
        self.conditions_widget.layout().addWidget(self.pumped_button, 0, 1)
        
        self.gases_ready_indicator = QtWidgets.QCheckBox()
        self.gases_ready_button = QtWidgets.QPushButton('Gases Ready')
        self.conditions_widget.layout().addWidget(self.gases_ready_indicator, 1, 0)
        self.conditions_widget.layout().addWidget(self.gases_ready_button, 1, 1)
    
        self.substrate_indicator = QtWidgets.QCheckBox()
        self.substrate_button = QtWidgets.QPushButton('Stage Temp. Ready')
        self.conditions_widget.layout().addWidget(self.substrate_indicator, 2, 0)
        self.conditions_widget.layout().addWidget(self.substrate_button, 2, 1)

        self.recipe_running_indicator = QtWidgets.QCheckBox()
        self.recipe_running_button = QtWidgets.QPushButton('Recipe Running')
        self.conditions_widget.layout().addWidget(self.recipe_running_indicator, 3, 0)
        self.conditions_widget.layout().addWidget(self.recipe_running_button, 3, 1)        
        
        self.plasma_on_indicator = QtWidgets.QCheckBox()
        self.plasma_on_button = QtWidgets.QPushButton('Plasma On')
        self.conditions_widget.layout().addWidget(self.plasma_on_indicator, 4, 0)
        self.conditions_widget.layout().addWidget(self.plasma_on_button, 4, 1)
        
        self.recipe_complete_indicator = QtWidgets.QCheckBox()
        self.recipe_complete_button = QtWidgets.QPushButton('Recipe Done')
        self.conditions_widget.layout().addWidget(self.recipe_complete_indicator, 5, 0)
        self.conditions_widget.layout().addWidget(self.recipe_complete_button, 5, 1)
    
    def setup_operations_widget(self):
        """Creates operations widget which is meant to provide end user with push buttons 
        which initiate specific subroutines of the ALD recipe process."""
        self.operations_widget = QtWidgets.QGroupBox('Operations Widget')
        self.operations_widget.setLayout(QtWidgets.QGridLayout())
        self.operations_widget.setStyleSheet(self.cb_stylesheet)
        
        self.pump_down_indicator = QtWidgets.QCheckBox()
        self.pump_down_button = QtWidgets.QPushButton('Pump Down')
        self.operations_widget.layout().addWidget(self.pump_down_indicator, 0, 0)
        self.operations_widget.layout().addWidget(self.pump_down_button, 0, 1)
        
        self.pre_deposition_indicator = QtWidgets.QCheckBox()
        self.pre_deposition_button = QtWidgets.QPushButton('Pre-deposition')
        self.operations_widget.layout().addWidget(self.pre_deposition_indicator, 1, 0)
        self.operations_widget.layout().addWidget(self.pre_deposition_button, 1, 1)
        
        self.deposition_indicator = QtWidgets.QCheckBox()
        self.deposition_button = QtWidgets.QPushButton('Deposition')
        self.operations_widget.layout().addWidget(self.deposition_indicator, 2, 0)
        self.operations_widget.layout().addWidget(self.deposition_button, 2, 1)
        
        self.vent_indicator = QtWidgets.QCheckBox()
        self.vent_button = QtWidgets.QPushButton('Vent')
        self.operations_widget.layout().addWidget(self.vent_indicator, 3, 0)
        self.operations_widget.layout().addWidget(self.vent_button, 3, 1)
        

    def setup_hardware_widget(self):
        """
        Creates Hardware widget which contains the Plasma and Temperature readout subpanels 
        and the Pressures and Flow subpanel. 
        This enclosing widget was created solely for the purpose of organizing subpanel 
        arrangement in UI.
        """
        self.hardware_widget = QtWidgets.QGroupBox('Hardware Widget')
        self.hardware_widget.setLayout(QtWidgets.QHBoxLayout())

        self.left_widget = QtWidgets.QWidget()
        self.left_widget.setLayout(QtWidgets.QVBoxLayout())
        
        self.right_widget = QtWidgets.QGroupBox('Pressures and Flow')
        self.right_widget.setLayout(QtWidgets.QHBoxLayout())
        
        self.temp_field_panel = QtWidgets.QGroupBox('Temperature Readout Panel ['+u'\u00b0'+'C]')
        self.temp_field_panel.setLayout(QtWidgets.QGridLayout())
        
        self.sp_temp_label = QtWidgets.QLabel('Set Point')
        self.sp_temp_field = QtWidgets.QDoubleSpinBox()
        self.lovebox.settings.sv_setpoint.connect_to_widget(self.sp_temp_field)
        
        self.pv_temp_label = QtWidgets.QLabel('Process Value')
        self.pv_temp_field = QtWidgets.QDoubleSpinBox()
        self.lovebox.settings.pv_temp.connect_to_widget(self.pv_temp_field)
        
        self.temp_field_panel.layout().addWidget(self.sp_temp_label, 0, 0)
        self.temp_field_panel.layout().addWidget(self.sp_temp_field, 0, 1)
        self.temp_field_panel.layout().addWidget(self.pv_temp_field, 0, 2)
        self.temp_field_panel.layout().addWidget(self.pv_temp_label, 0, 3)
        
        self.left_widget.layout().addWidget(self.temp_field_panel)

        self.hardware_widget.layout().addWidget(self.left_widget)
        self.hardware_widget.layout().addWidget(self.right_widget)
        self.setup_plasma_subpanel()
        self.setup_pressures_subpanel()
    
    def setup_plasma_subpanel(self):
        """
        Creates plasma subpanel which displays information relevant to the 
        connected RF power supply. Subpanel also includes fields allowing for 
        user defined setpoints to be sent to the power supply software side.

        Creates UI elements related to the ALD RF power supply,
        establishes signals and slots, as well as connections between UI elements 
        and their associated *LoggedQuantities*.
        """
        self.plasma_panel = QtWidgets.QGroupBox('Plasma Panel [W]')
        self.left_widget.layout().addWidget(self.plasma_panel)

        self.fwd_power_input_label = QtWidgets.QLabel('FWD Power Input')
        self.fwd_power_input = QtWidgets.QDoubleSpinBox()
        self.fwd_power_readout_label = QtWidgets.QLabel('FWD Power Readout')
        self.fwd_power_readout = QtWidgets.QDoubleSpinBox()
        
        self.plasma_left_panel = QtWidgets.QWidget()
        self.plasma_left_panel.setLayout(QtWidgets.QGridLayout())
        self.plasma_right_panel = QtWidgets.QWidget()
        self.plasma_right_panel.setLayout(QtWidgets.QGridLayout())
        self.plasma_right_panel.setStyleSheet(self.cb_stylesheet)
        
        self.plasma_left_panel.layout().addWidget(self.fwd_power_input_label, 0, 0)
        self.plasma_left_panel.layout().addWidget(self.fwd_power_input, 0, 1)
        self.plasma_left_panel.layout().addWidget(self.fwd_power_readout_label, 1, 0)
        self.plasma_left_panel.layout().addWidget(self.fwd_power_readout, 1, 1)
        
        self.rf_indicator = QtWidgets.QCheckBox()
        self.rf_pushbutton = QtWidgets.QPushButton('RF ON/OFF')
        if hasattr(self, 'shutter'):
            self.seren.settings.RF_enable.connect_to_widget(self.rf_indicator)
            self.rf_pushbutton.clicked.connect(self.seren.RF_toggle)
 
        self.rev_power_readout_label = QtWidgets.QLabel('REFL Power Readout')
        self.rev_power_readout = QtWidgets.QDoubleSpinBox()
                
        self.plasma_right_panel.layout().addWidget(self.rf_indicator, 0, 1)
        self.plasma_right_panel.layout().addWidget(self.rf_pushbutton, 0, 0)
        self.plasma_right_panel.layout().addWidget(self.rev_power_readout, 1, 0)
        self.plasma_right_panel.layout().addWidget(self.rev_power_readout_label, 1, 1)
        
        self.seren.settings.set_forward_power.connect_to_widget(self.fwd_power_input)
        self.seren.settings.forward_power_readout.connect_to_widget(self.fwd_power_readout)
        self.seren.settings.reflected_power.connect_to_widget(self.rev_power_readout)
        
        self.plasma_panel.setLayout(QtWidgets.QHBoxLayout())
        self.plasma_panel.layout().addWidget(self.plasma_left_panel)
        self.plasma_panel.layout().addWidget(self.plasma_right_panel)

    def setup_pressures_subpanel(self):
        """Creates pressures subpanel which display pressure sensor measurements. 
        Subpanel includes measurement value fields and input fields which allow for 
        user defined setpoints to be sent to pressure controllers. 
        
        Creates UI elements related to ALD pressure controllers,
        establishes signals and slots, as well as connections between UI elements 
        and their associated *LoggedQuantities*.
        """
        self.flow_input_group = QtWidgets.QGroupBox('Flow Inputs')
        self.flow_output_group = QtWidgets.QGroupBox('Flow Outputs')
        self.pressures_group = QtWidgets.QGroupBox('Pressure Outputs')

        self.right_widget.layout().addWidget(self.flow_input_group)
        self.right_widget.layout().addWidget(self.flow_output_group)
        self.right_widget.layout().addWidget(self.pressures_group)

        self.flow_input_group.setStyleSheet(self.cb_stylesheet)
        self.flow_input_group.setLayout(QtWidgets.QGridLayout())
        self.flow_output_group.setLayout(QtWidgets.QGridLayout())
        self.pressures_group.setLayout(QtWidgets.QGridLayout())

        self.MFC1_label = QtWidgets.QLabel('MFC1 Flow')
        self.set_MFC1_field = QtWidgets.QDoubleSpinBox()
        
        self.throttle_pressure_label = QtWidgets.QLabel('Throttle Pressure \n [mTorr]')
        self.set_throttle_pressure_field = QtWidgets.QDoubleSpinBox()
        
        self.throttle_pos_label = QtWidgets.QLabel('Throttle Valve \n Position [%]')
        self.set_throttle_pos_field = QtWidgets.QDoubleSpinBox()
        
        self.shutter_indicator = QtWidgets.QCheckBox()
        self.shutter_pushbutton = QtWidgets.QPushButton('Shutter Open/Close')
        if hasattr(self, 'shutter'):
            self.shutter.settings.shutter_open.connect_to_widget(self.shutter_indicator)
            self.shutter_pushbutton.clicked.connect(self.shutter.shutter_toggle)

        self.input_spacer = QtWidgets.QSpacerItem(10,30, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.flow_input_group.layout().addWidget(self.MFC1_label, 0, 0)
        self.flow_input_group.layout().addWidget(self.set_MFC1_field, 0, 1)
        self.flow_input_group.layout().addWidget(self.throttle_pressure_label, 1, 0)
        self.flow_input_group.layout().addWidget(self.set_throttle_pressure_field, 1, 1)        
        self.flow_input_group.layout().addWidget(self.throttle_pos_label, 2, 0)
        self.flow_input_group.layout().addWidget(self.set_throttle_pos_field, 2, 1)
        self.flow_input_group.layout().addWidget(self.shutter_indicator, 3, 0)
        self.flow_input_group.layout().addWidget(self.shutter_pushbutton, 3, 1)
        self.flow_input_group.layout().addItem(self.input_spacer, 4, 0)
        
        self.read_MFC1_field = QtWidgets.QDoubleSpinBox()
        self.read_throttle_pressure_field = QtWidgets.QDoubleSpinBox()
        self.read_throttle_pos_field = QtWidgets.QDoubleSpinBox()
        self.output_spacer = QtWidgets.QSpacerItem(10,30, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        
        self.flow_output_group.layout().addWidget(self.read_MFC1_field, 0, 0)
        self.flow_output_group.layout().addWidget(self.read_throttle_pressure_field, 1, 0)
        self.flow_output_group.layout().addWidget(self.read_throttle_pos_field, 2, 0)
        self.flow_output_group.layout().addItem(self.output_spacer, 3, 0)
        
        self.ch1_readout_field = QtWidgets.QDoubleSpinBox()
        self.ch1_readout_label = QtWidgets.QLabel('Ch1 Pressure')
        self.ch2_readout_field = QtWidgets.QDoubleSpinBox()
        self.ch2_readout_label = QtWidgets.QLabel('Ch2 Pressure')
        self.ch3_readout_field = QtWidgets.QDoubleSpinBox()
        self.ch3_readout_label = QtWidgets.QLabel('Ch3 Pressure')
        
        self.pressures_group.layout().addWidget(self.ch1_readout_label, 0, 0)
        self.pressures_group.layout().addWidget(self.ch1_readout_field, 0, 1)
        self.pressures_group.layout().addWidget(self.ch2_readout_label, 1, 0)
        self.pressures_group.layout().addWidget(self.ch2_readout_field, 1, 1)
        self.pressures_group.layout().addWidget(self.ch3_readout_label, 2, 0)
        self.pressures_group.layout().addWidget(self.ch3_readout_field, 2, 1)
        self.pressures_group.layout().addItem(self.output_spacer, 3, 0)
        
        self.mks146.settings.set_MFC0_SP.connect_to_widget(self.set_MFC1_field)
        self.mks600.settings.sp_set_value.connect_to_widget(self.set_throttle_pressure_field)
        self.mks600.settings.set_valve_position.connect_to_widget(self.set_throttle_pos_field)

        self.mks146.settings.MFC0_flow.connect_to_widget(self.read_MFC1_field)
        self.mks600.settings.pressure.connect_to_widget(self.read_throttle_pressure_field)
        self.mks600.settings.read_valve_position.connect_to_widget(self.read_throttle_pos_field)

        self.vgc.settings.ch1_pressure_scaled.connect_to_widget(self.ch1_readout_field)
        self.vgc.settings.ch2_pressure_scaled.connect_to_widget(self.ch2_readout_field)
        self.vgc.settings.ch3_pressure_scaled.connect_to_widget(self.ch3_readout_field)
        
    def setup_thermal_control_widget(self):
        """Creates temperature plotting widget, UI elements meant to allow the user to monitor
        ALD system conditions, specifically temperature, through the use of live plots."""
        self.thermal_widget = QtWidgets.QGroupBox('Thermal Plot')
        self.thermal_widget.setLayout(QtWidgets.QVBoxLayout())
        self.thermal_channels = 1
        

        self.thermal_plot_widget = pg.GraphicsLayoutWidget()
        self.thermal_plot = self.thermal_plot_widget.addPlot(title='Temperature History')
        self.thermal_plot.showGrid(y=True)
        self.thermal_plot.addLegend()
        self.thermal_widget.layout().addWidget(self.thermal_plot_widget)
        self.thermal_plot_names = ['Heater Temperature']
        self.thermal_plot_lines = []
        for i in range(self.thermal_channels):
            color = pg.intColor(i)
            plot_line = self.thermal_plot.plot([1], pen=pg.mkPen(color, width=2),
                                                    name = self.thermal_plot_names[i])
            self.thermal_plot_lines.append(plot_line)
        self.vLine1 = pg.InfiniteLine(angle=90, movable=False)
        self.hLine1 = pg.InfiniteLine(angle=0, movable=False)
        self.thermal_plot.addItem(self.vLine1)
        self.thermal_plot.addItem(self.hLine1)
    
    def setup_rf_flow_widget(self):
        """Creates RF/MFC plotting widget. UI elements are created, which are meant to 
        allow the user to monitor ALD system conditions through the use of live plots."""
        self.rf_widget = QtWidgets.QGroupBox('RF Plot')
        self.layout.addWidget(self.rf_widget)
        self.rf_widget.setLayout(QtWidgets.QVBoxLayout())
        
        self.rf_plot_widget = pg.GraphicsLayoutWidget()
        self.rf_plot = self.rf_plot_widget.addPlot(title='RF power and scaled MFC flow')
        self.rf_plot.showGrid(y=True)
        self.rf_plot.addLegend()
        self.rf_widget.layout().addWidget(self.rf_plot_widget)
        self.rf_plot_names = ['Forward', 'Reflected', 'MFC flow (scaled)']
        self.rf_plot_lines = []
        for i in range(self.RF_CHANS):
            color = pg.intColor(i)
            plot_line = self.rf_plot.plot([1], pen=pg.mkPen(color, width=2),
                                          name = self.rf_plot_names[i])
            self.rf_plot_lines.append(plot_line)
        self.vLine2 = pg.InfiniteLine(angle=90, movable=False)
        self.hLine2 = pg.InfiniteLine(angle=0, movable=False)
        self.rf_plot.addItem(self.vLine2)
        self.rf_plot.addItem(self.hLine2)
        
        
    def setup_shutter_control_widget(self):
        """
        Creates shutter control widget, UI elements related to ALD shutter controls,
        establishes signals and slots, as well as connections between UI elements 
        and their associated *LoggedQuantities*
        """
        self.shutter_control_widget = QtWidgets.QGroupBox('Shutter Controls')
        self.shutter_control_widget.setLayout(QtWidgets.QGridLayout())
        self.shutter_control_widget.setStyleSheet(self.cb_stylesheet)

        self.shutter_status = QtWidgets.QCheckBox(self.shutter_control_widget)
        self.shutter_control_widget.layout().addWidget(self.shutter_status, 0, 0)
        self.shutter.settings.shutter_open.connect_to_widget(self.shutter_status)

        self.shaul_shutter_toggle = QtWidgets.QPushButton('Shaul\'s Huge Shutter Button')
        self.shaul_shutter_toggle.setMinimumHeight(200)
        font = self.shaul_shutter_toggle.font()
        font.setPointSize(24)
        self.shaul_shutter_toggle.setFont(font)
        self.shutter_control_widget.layout().addWidget(self.shaul_shutter_toggle, 0, 1)
        if hasattr(self, 'shutter'):
            self.shaul_shutter_toggle.clicked.connect(self.shutter.shutter_toggle)

    def setup_recipe_control_widget(self):
        """
        Creates recipe control widget, UI elements related to ALD recipe settings,
        establishes signals and slots, as well as connections between UI elements 
        and their associated *LoggedQuantities*
        """
        self.recipe_control_widget = QtWidgets.QGroupBox('Recipe Controls')
        self.recLayout = QtWidgets.QVBoxLayout()
        self.recipe_control_widget.setLayout(self.recLayout)
        self.layout.addWidget(self.recipe_control_widget)
    
        ## Settings Widget
        self.settings_widget = QtWidgets.QWidget()
        self.settings_layout = QtWidgets.QGridLayout()
        self.settings_widget.setLayout(self.settings_layout)
        
        self.cycle_label = QtWidgets.QLabel('N Cycles')
        self.settings_widget.layout().addWidget(self.cycle_label, 0,0)
        self.cycle_field = QtWidgets.QDoubleSpinBox()
        self.settings_widget.layout().addWidget(self.cycle_field, 0,1)
        self.recipe_control_widget.layout().addWidget(self.settings_widget)
        
        self.recipe.settings.cycles.connect_to_widget(self.cycle_field)
    
        self.current_cycle_label = QtWidgets.QLabel('Cycles Completed')
        self.current_cycle_field = QtWidgets.QDoubleSpinBox()
        self.settings_widget.layout().addWidget(self.current_cycle_label, 0, 2)
        self.settings_widget.layout().addWidget(self.current_cycle_field, 0, 3)
        
        self.recipe.settings.cycles_completed.connect_to_widget(self.current_cycle_field)

        self.method_select_label = QtWidgets.QLabel('t3 Method')
        self.method_select_comboBox = QtWidgets.QComboBox()
        self.settings_widget.layout().addWidget(self.method_select_label, 1, 2)
        self.settings_widget.layout().addWidget(self.method_select_comboBox, 1, 3)
        
        self.recipe.settings.t3_method.connect_to_widget(self.method_select_comboBox)

        # Subroutine Table Widget

        self.subroutine_table_widget = QtWidgets.QWidget()
        self.subroutine_layout = QtWidgets.QHBoxLayout()
        self.subroutine_table_widget.setLayout(self.subroutine_layout)
        self.subroutine_label = QtWidgets.QLabel('Subroutine [s]')
        self.subroutine_table_widget.layout().addWidget(self.subroutine_label)
        
        self.subroutine_table = QtWidgets.QTableView()
        self.subroutine_table.setMaximumHeight(65)
        sub_names = ['Cycles', 't'+u'\u2080'+' PV2', 't'+u'\u2081'+' Purge']
        self.subtableModel = ArrayLQ_QTableModel(self.recipe.settings.subroutine, col_names=sub_names)
        self.subroutine_table.setModel(self.subtableModel)
        self.subroutine_table_widget.layout().addWidget(self.subroutine_table)
        self.recipe_control_widget.layout().addWidget(self.subroutine_table_widget)
        
        
        ## Main Table Widget
        self.table_widget = QtWidgets.QWidget()
        self.table_widget_layout = QtWidgets.QHBoxLayout()
        self.table_widget.setLayout(self.table_widget_layout)
#         self.table_widget.setMinimumWidth(827)

        self.pulse_label = QtWidgets.QLabel('Step Durations [s]')
        self.table_widget.layout().addWidget(self.pulse_label)

        self.pulse_table = QtWidgets.QTableView()
        self.pulse_table.setMaximumHeight(65)
        
        names = ['t'+u'\u2080'+' Pre Purge', 't'+u'\u2081'+' (TiCl'+u'\u2084'+' PV)',\
                  't'+u'\u2082'+' Purge', 't'+u'\u2083'+' (N'+u'\u2082'+'/Shutter)', \
                 't'+u'\u2084'+' Purge', 't'+u'\u2085'+' Post Purge', u'\u03a3'+'t'+u'\u1d62']
        self.tableModel = ArrayLQ_QTableModel(self.recipe.settings.time, col_names=names)
        self.pulse_table.setModel(self.tableModel)
        self.table_widget.layout().addWidget(self.pulse_table)
        self.recipe_control_widget.layout().addWidget(self.table_widget)
    
        self.recipe_panel = QtWidgets.QWidget()
        self.recipe_panel_layout = QtWidgets.QGridLayout()
        self.recipe_panel.setLayout(self.recipe_panel_layout)
        self.recipe_panel.setStyleSheet(self.cb_stylesheet)
              
        self.start_button = QtWidgets.QPushButton('Start Recipe')
        self.start_button.clicked.connect(self.recipe.start)
        self.recipe_panel.layout().addWidget(self.start_button, 0, 1)
        
        self.abort_button = QtWidgets.QPushButton('Abort Recipe')
        self.abort_button.clicked.connect(self.recipe.interrupt)
        self.recipe_panel.layout().addWidget(self.abort_button, 0, 2)
        
        
        self.recipe_complete_subpanel = QtWidgets.QWidget()
        self.recipe_complete_subpanel.setLayout(QtWidgets.QHBoxLayout())
        self.recipe_ready_label = QtWidgets.QLabel('Recipe Complete')
        self.recipe_ready_indicator = QtWidgets.QCheckBox()
        self.recipe_complete_subpanel.layout().addWidget(self.recipe_ready_label)
        self.recipe_complete_subpanel.layout().addWidget(self.recipe_ready_indicator)
        self.recipe_panel.layout().addWidget(self.recipe_complete_subpanel, 0, 3)

        self.recipe_control_widget.layout().addWidget(self.recipe_panel)
        
        self.recipe.settings.recipe_completed.connect_to_widget(self.recipe_ready_indicator)



        
    def setup_display_controls(self):
        """
        Creates a dockArea widget containing other parameters to be set by the 
        end user, including the length of plot time history and temperature data 
        export path.
        """
        
        self.display_control_widget = QtWidgets.QGroupBox('Display Control Panel')
        self.display_control_widget.setLayout(QtWidgets.QVBoxLayout())
        
        self.field_panel = QtWidgets.QWidget()
        self.field_panel_layout = QtWidgets.QGridLayout()
        self.field_panel.setLayout(self.field_panel_layout)
        self.display_control_widget.layout().addWidget(self.field_panel)
        
        self.export_button = QtWidgets.QPushButton('Export Temperature Data')
        self.save_field = QtWidgets.QLineEdit('Directory')
#         self.save_field.setMinimumWidth(200)
#         self.save_field.setMaximumWidth(600)

        self.field_panel.layout().addWidget(self.export_button, 1, 0)
        self.field_panel.layout().addWidget(self.save_field, 1, 1)
        
        self.export_button.clicked.connect(self.export_to_disk)
        self.settings.save_path.connect_to_widget(self.save_field)
        
        plot_ui_list = ('display_window','history_length')
        self.field_panel.layout().addWidget(self.settings.New_UI(include=plot_ui_list), 2,0)


    def setup_buffers_constants(self):
        '''Creates constants and storage arrays to be used in this module.'''
        home = os.path.expanduser("~")
        self.path = home+'\\Desktop\\'
        self.full_file_path = self.path+'np_export'
        self.psu_connected = None
        self.HIST_LEN = self.settings.history_length.val
        self.WINDOW = self.settings.display_window.val
        self.RF_CHANS = 3
        self.T_CHANS = 1
        self.history_i = 0
        self.index = 0
        
        self.rf_history = np.zeros((self.RF_CHANS, self.HIST_LEN))
        self.thermal_history = np.zeros((self.T_CHANS, self.HIST_LEN))
        self.time_history = np.zeros((1, self.HIST_LEN), dtype='datetime64[s]')
        self.debug_mode = False

    def plot_routine(self):
        '''This function reads from *LoggedQuantities* and stores them in arrays. 
        These arrays are then plotted by :meth:`update_display`'''
        if self.debug_mode:
            rf_entry = np.random.rand(3,)
            t_entry = np.random.rand(1,)
        else:
            rf_entry = np.array([self.seren.settings['forward_power_readout'], \
                             self.seren.settings['reflected_power'], \
                             self.mks146.settings['MFC0_flow']])
            t_entry = np.array([self.lovebox.settings['pv_temp']])

        time_entry = datetime.datetime.now()
        if self.history_i < self.HIST_LEN-1:
            self.index = self.history_i % self.HIST_LEN
        else:
            self.index = self.HIST_LEN-1
            self.rf_history = np.roll(self.rf_history, -1, axis=1)
            self.thermal_history = np.roll(self.thermal_history, -1, axis=1)
            self.time_history = np.roll(self.time_history, -1, axis=1)
        self.rf_history[:, self.index] = rf_entry
        self.thermal_history[:, self.index] = t_entry
        self.time_history[:, self.index] = time_entry
        self.history_i += 1
        
    def export_to_disk(self):
        """
        Exports numpy data arrays to disk. Writes to 
        :attr:`self.settings.save_path`
        Function connected to and called by 
        :attr:`self.export_button`
        """
        path = self.settings['save_path']
        np.save(path+'_temperature.npy', self.thermal_history)
        np.save(path+'_times.npy', self.time_history)
        
    def update_display(self):
        """
        **IMPORTANT:** *Do not call this function. The core framework already does so.*
        
        Built in ScopeFoundry function is called repeatedly. 
        Its purpose is to update UI plot objects.
        This particular function updates plot objects depicting 
        stage temperature, RF power levels, and the MFC flow rate and setpoint.
        """
        self.WINDOW = self.settings.display_window.val
        self.vLine1.setPos(self.WINDOW)
        self.vLine2.setPos(self.WINDOW)
        
        lovebox_level = self.lovebox.settings['sv_setpoint']
        self.hLine1.setPos(lovebox_level)
        
        flow_level = self.mks146.settings['MFC0_flow']
        self.hLine2.setPos(flow_level)
        
        lower = self.index-self.WINDOW

        for i in range(self.RF_CHANS):
            if self.index >= self.WINDOW:

                self.rf_plot_lines[i].setData(
                    self.rf_history[i, lower:self.index+1])
            else:
                self.rf_plot_lines[i].setData(
                    self.rf_history[i, :self.index+1])
                self.vLine1.setPos(self.index)
                self.vLine2.setPos(self.index)

        for i in range(self.T_CHANS):
            if self.index >= self.WINDOW:
                self.thermal_plot_lines[i].setData(
                    self.thermal_history[i, lower:self.index+1])
                
            else:
                self.thermal_plot_lines[i].setData(
                    self.thermal_history[i, :self.index+1])
                self.vLine1.setPos(self.index)
                self.vLine2.setPos(self.index)

    def conditions_check(self):
        """Checks ALD system conditions. Conditions that are met appear with 
        green LED indicators in the Conditions Widget groupBox."""
        self.pumped_check()
        self.gases_check()
        self.deposition_check()
        self.substrate_check()
        self.vent_check()
    
    def run(self):
        dt = 0.1
        while not self.interrupt_measurement_called:
            self.conditions_check()
            self.plot_routine()
            time.sleep(dt)


    def pumped_check(self):
        '''Checks if ALD system is properly pumped down.'''
        Z = 1e-3
        P = self.vgc.settings['ch3_pressure_scaled']
        self.recipe.settings['pumped'] = (P < Z)
#         if self.recipe.settings['pumped']:
#             self.pre_deposition_button.setEnabled(True)
#             self.pre_deposition_button.clicked.connect(self.recipe.predeposition)
#         else:
#             self.pre_deposition_button.setEnabled(False)

    def gases_check(self):
        '''Checks if MFC flow and system pressure conditions are ideal
        for deposition. 

        Should its conditions be satisfied, its *LoggedQuantity* is updated
        and its respective LED indicator in the Conditions Widget groupBox will appear green.'''
        flow = self.mks146.settings['MFC0_flow']
        condition = (0.7 <= flow)
        self.recipe.settings['gases_ready'] = condition

    def substrate_check(self):
        '''
        Checks if stage is adequately heated.
        
        Should its condition be satisfied, its *LoggedQuantity* is updated 
        and its respective LED indicator in the Conditions Widget groupBox will appear green.
        '''
        T = self.lovebox.settings['sv_setpoint']
        pv = self.lovebox.settings['pv_temp']
        condition = (0.9*T <= pv <= 1.1*T)
        self.recipe.settings['substrate_hot'] = condition

    
    def deposition_check(self):
        """
        Checks if deposition conditions are met.
        
        Conditions include:
         * System pumped
         * Gases ready
         * RF enabled
         * Substrate temperature hot.
         
        Button which initiates deposition is enabled only upon the 
        satisfaction of the above 4 requirements.
        """
        condition1 = self.recipe.settings['pumped']
        condition2 = self.recipe.settings['gases_ready']
        condition3 = self.seren.settings['RF_enable']
        condition4 = self.recipe.settings['substrate_hot']
        if condition1 and condition2 and condition3 and condition4:
            self.deposition_button.setEnabled(True)
        else:
            self.deposition_button.setEnabled(False)

    def vent_check(self):
        """
        Checks whether predeposition and deposition stages have been completed. 
        
        Should its conditions be satisfied, its *LoggedQuantity* is updated 
        and its respective LED indicator in the Conditions Widget groupBox will appear green.
        """
        if self.recipe.dep_complete and self.recipe.predep_complete:
            self.vent_button.setEnabled(True)
        else:
            self.vent_button.setEnabled(False)
        pass