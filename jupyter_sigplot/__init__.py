#!/usr/bin/env python
from ._version import version_info, __version__


def _jupyter_nbextension_paths():
    '''
    Exposes the Jupyter Notebook Extension entrypoints
    '''
    return [{
        'section': 'notebook',

        # the path is relative to the `jupyter_sigplot` directory
        'src': 'static',

        # directory in the `nbextension/` namespace
        'dest': 'jupyter_sigplot',

        # _also_ in the `nbextension/` namespace
        'require': 'jupyter_sigplot/extension'
    }]


__all__ = [
    version_info,
    __version__,
    _jupyter_nbextension_paths,
]
