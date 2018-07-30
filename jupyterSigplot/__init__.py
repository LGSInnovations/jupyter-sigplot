from ._version import version_info, __version__

from .example import *

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyterSigplot',
        'require': 'jupyterSigplot/extension'
    }]
    display(Javascript("utils.load_extensions('../js.src/sigplot_ext');"))
