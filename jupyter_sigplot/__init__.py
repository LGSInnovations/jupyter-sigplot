from ._version import version_info, __version__
import os.path
import sys
import warnings
from .example import *
from notebook import nbextensions

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter_sigplot',
        'require': 'jupyter_sigplot/extension'
    }]

