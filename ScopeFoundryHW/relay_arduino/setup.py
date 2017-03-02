from setuptools import setup

setup(
    name = 'ScopeFoundryHW.relay_arduino',
    
    version = '0.0.1',
    
    description = 'ScopeFoundry Hardware plug-in: seeed studio Relay Shield and Arduino Uno pair ScopeFoundry interface',
    
    # Author details
    author='Alan Buckley',
    author_email='alanbuckley@lbl.gov',

    # Choose your license
    license='BSD',

    package_dir={'ScopeFoundryHW.relay_arduino': '.'},
    
    packages=['ScopeFoundryHW.relay_arduino',],
    
    #packages=find_packages('.', exclude=['contrib', 'docs', 'tests']),
    #include_package_data=True,  

    install_requires=['ScopeFoundry>=0.0.1'],
    
    package_data={
        '':["*.ui"], # include QT ui files 
        '':["README*", 'LICENSE'], # include License and readme 
        },
    )
