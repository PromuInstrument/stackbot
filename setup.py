from setuptools import setup, find_packages

setup(name='foundry_scope',
      version='x.x.x',
      description='ScopeFoundry',
      # long_description =open('README.md', 'r').read(),
      # Author details
      author='Edward S. Barnard',
      author_email='esbarnard@lbl.gov',
      # Choose your license
      license='BSD',
      url='http://www.scopefoundry.org/',
      # packages=['ScopeFoundry',
      #           'ScopeFoundry.scanning',
      #           'ScopeFoundry.examples',],
      # package_dir={'ScopeFoundry': './ScopeFoundry'},
      packages=find_packages('.', exclude=['contrib', 'docs', 'tests']),
      # include_package_data=True,
      package_data={'': ["*.ui"]},  # include QT ui files},
      )
