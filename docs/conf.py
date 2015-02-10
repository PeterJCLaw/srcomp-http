import os
import sys


sys.path.insert(0, os.path.abspath('..'))

# Sphinx configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

source_suffix = '.rst'
master_doc = 'index'

project = 'sr.comp.http'
copyright = '2015, Student Robotics'

release = '1.0.0'
version = '1.0.0'

html_theme = 'default'

intersphinx_mapping = {'http://docs.python.org/': None}