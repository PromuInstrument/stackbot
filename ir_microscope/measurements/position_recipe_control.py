from ScopeFoundry.stored_recipe_control import BaseRecipeControl
from collections import OrderedDict

class PositionRecipeControl(BaseRecipeControl):
    
    
    name = 'position_recipe_control'
        

    def __init__(self, app, name=None):
        
        settings_dict = OrderedDict()
        
        for ax in ['x','y','z']:
            settings_dict[ax] = 'hardware/attocube_xyz_stage/{}_target_position'.format(ax)
        
        
        BaseRecipeControl.__init__(self, app, name=name, settings_dict=settings_dict)
        
        
    def setup_figure(self):
        BaseRecipeControl.setup_figure(self)
        self.ui.current_settings_groupBox.setEnabled(False)
