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
        'dest': 'jupyterSigplot',
        'require': 'jupyterSigplot/extension'
    }]

def prepare_js():
    pkgdir = os.path.dirname(__file__)
    sigplotdir = os.path.join(pkgdir, 'static')
    nbextensions.install_nbextension(sigplotdir, user=True, overwrite=True, symlink=True)
    display(Javascript("utils.load_extensions('sigplotjs/sigplot_ext');"))

def load_ipython_extension(ipython):
    prepare_js()
    ipython.push("SigPlot")


def unload_ipython_extension(ipython):
    pass
