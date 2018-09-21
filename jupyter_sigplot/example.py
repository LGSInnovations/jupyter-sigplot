from __future__ import absolute_import
from ipywidgets import widgets

import os

from traitlets import (
    Unicode,
    Bool,
    Dict,
    List
)
import requests

from IPython.core.magic import register_line_cell_magic
from IPython.display import (
    display,
    clear_output,
    Image
)

@widgets.register
class HelloWorld(widgets.DOMWidget):
    """An example widget."""
    _view_name = Unicode('HelloView').tag(sync=True)
    _model_name = Unicode('HelloModel').tag(sync=True)
    _view_module = Unicode('jupyter_sigplot').tag(sync=True)
    _model_module = Unicode('jupyter_sigplot').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)
    value = Unicode('Hello World!').tag(sync=True)

