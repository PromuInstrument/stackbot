from ScopeFoundry.stored_recipe_control import BaseRecipeControl
from collections import OrderedDict

class MirrorRecipeControl(BaseRecipeControl):
    
    
    name = 'mirror_recipe_control'
    
    def __init__(self, app, name=None):
        
        settings_dict = OrderedDict()
        
        for ax in ['x','y', 'z', 'pitch', 'yaw']:
            settings_dict[ax] = 'hardware/cl_mirror/delta_{}_target_position'.format(ax)
        
        
        BaseRecipeControl.__init__(self, app, name=name, settings_dict=settings_dict)
        
        
    def setup_figure(self):
        BaseRecipeControl.setup_figure(self)
        self.ui.current_settings_groupBox.setEnabled(False)
        
        
    def execute_current_recipe(self):
        
        # position safety checks        
        S = self.settings
        
        if abs(S['recipe_x']) > 500. or abs(S['recipe_y']) > 500.:
            self.log.warn("Failed to execute mirror recipe {}: xy out of safe range".format(S['recipe_name']))
            return 
        
        if abs(S['recipe_pitch']) > 1000. or abs(S['recipe_yaw']) > 1000.:
            self.log.warn("Failed to execute mirror recipe {}: pitch and yaw out of safe range".format(S['recipe_name']))
            return 
        
        if S['recipe_z'] < -150:
            self.log.warn("Failed to execute mirror recipe {}: z out of safe range".format(S['recipe_name']))
            return
        
        BaseRecipeControl.execute_current_recipe(self)
