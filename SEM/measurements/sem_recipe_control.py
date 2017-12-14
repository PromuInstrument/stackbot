'''
    Manage stored SEM image conditions
    Act as SEM Control panel
    
    Some items 
'''

### on init

# read csv file, populate data structure

# items: name, date, kV, WD, aperture (CL), high_current (CL), beam_current (Auger), stig_xy, app_xy, gun_xy (Auger)
# items with CL or Auger after are only set in the corresponding modes
