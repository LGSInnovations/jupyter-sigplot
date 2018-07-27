from ._version import version_info, __version__

from .sigplot import *

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyterSigplot',
        'require': 'jupyterSigplot/extension'
    }]
