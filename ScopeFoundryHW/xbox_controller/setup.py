from setuptools import setup

setup(
	name = 'ScopeFoundryHW.xbox_controller',

	version = '0.0.1',

	description = 'ScopeFoundry Hardware plug-in: Xbox controller interfacing demonstration',

	#Author details
	author = 'Alan Buckley',
	author_email='alanbuckley@lbl.gov',

	#License details
	license = 'BSD',
	package_dir = {'ScopeFoundryHW.xbox_controller': '.'},
	packages = ['ScopeFoundryHW.xbox_controller',],

	install_requires=['ScopeFoundry>=0.0.1'],

	package_data={
		'':["*.ui"], # include QT user interface files
		'':["README*", 'LICENSE'], # include License and Readme
		},
	)