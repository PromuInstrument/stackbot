from setuptools import setup

setup(
    name = 'ScopeFoundryHW.random_gen',
    
    version = '0.0.1',
    
    description = 'ScopeFoundry Hardware plug-in: Dummy random number generator',
    
    # Author details
    author='Edward S. Barnard',
    author_email='esbarnard@lbl.gov',

    # Choose your license
    license='BSD',

    package_dir={'ScopeFoundryHW.random_gen': '.'},
    
    packages=['ScopeFoundryHW.random_gen',],
    
    #packages=find_packages('.', exclude=['contrib', 'docs', 'tests']),
    #include_package_data=True,  

    install_requires=['ScopeFoundry>=0.0.1'],
    
    package_data={
        '':["*.ui"], # include QT ui files 
        '':["README*", 'LICENSE'], # include License and readme 
        },
    )
