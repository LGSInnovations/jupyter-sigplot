#!/usr/bin/env python
from __future__ import absolute_import, print_function
import errno
import os

import numpy as np

import ipywidgets as widgets
from traitlets import (
    Unicode,
    Bool,
    Dict,
    List,
)

import requests

from IPython.core.magic import register_line_cell_magic
from IPython.display import (
    display,
    clear_output,
)


class SigPlot(widgets.DOMWidget):
    _view_module_version = Unicode('0.0.1')
    _view_name = Unicode('SigPlotView').tag(sync=True)
    _model_name = Unicode('SigPlotModel').tag(sync=True)
    _view_module = Unicode('jupyter_sigplot').tag(sync=True)
    _model_module = Unicode('jupyter_sigplot').tag(sync=True)
    href_obj = Dict().tag(sync=True)
    array_obj = Dict().tag(sync=True)
    done = Bool(False).tag(sync=True)
    options = Dict().tag(sync=True)
    inputs = []
    arrays = []
    hrefs = []
    oldArrays = List().tag(sync=True)
    oldHrefs = List().tag(sync=True)
    imageOutput = Unicode("img").tag(sync=True)
    dimension = 1

    def __init__(self, *args, **kwargs):
        self.inputs = []
        self.hrefs = []
        self.arrays = []
        self.options = kwargs
        for arg in args:
            if isinstance(arg, str):
                self.overlay_href(arg)
            else:
                self.inputs.append(arg)
        super(SigPlot, self).__init__(**kwargs)

    def change_settings(self, **kwargs):
        self.options.update(kwargs)

    def show_array(self, data, layer_type="1D", subsize=None):
        overrides = {}
        if layer_type == "2D":
            # subsize is *required* if it's 2-D
            if subsize is None and isinstance(data, (list, tuple)):
                raise ValueError("For xraster, a subsize is required")
            elif subsize is not None and isinstance(data, (list, tuple)):
                overrides.update({
                    "subsize": subsize,
                })
        self.array_obj = {
            "data": data,
            "overrides": overrides,
            "layerType": layer_type,
        }
        if self.array_obj not in self.arrays:
            self.arrays.append(self.array_obj)
            self.oldArrays = self.arrays

    @register_line_cell_magic
    def overlay_array(self, data):
        if not isinstance(data, (list, tuple, np.ndarray)):
            raise TypeError(
                "``data`` can only be Union[List, Tuple, np.ndarray]"
            )

        self.inputs.append(data)

    def show_href(self, fpath, layer_type):  # noqa: C901
        """Plot a file or URL with SigPlot

        :param fpath: File-path to bluefile or matfile. Forms accepted:
                      - absolute paths, e.g., /data/foo.tmp
                      - relative paths, e.g., ../foo.tmp
                      - paths with envvars, e.g., $HOME/foo.tmp
                      - paths with tilde, e.g., ~/foo.tmp
                      - local path, e.g., foo.tmp
                      - file in MIDAS aux path, e.g., foo.tmp
                        (actually in /data/midas/`whoami`/foo.tmp)
                      - URL, e.g., http://website.com/foo.tmp
        :type fpath: str

        :param layer_type: either '1D' or '2D'
        :type layer_type: str

        :Example:
        >>> plot = SigPlot()
        >>> display(plot)
        >>> plot.overlay_href('foo.tmp', layer_type='2D')
        """
        # if the file is HTTP/HTTPS, SigPlot.js will handle it
        if not fpath.startswith("http"):
            # expand out environment variables and ~
            fpath = os.path.expanduser(os.path.expandvars(fpath))

            symlink = False
            if not os.path.isabs(fpath):
                # if it's not an absolute path (i.e., is relative),
                # check if it is beyond ${CWD} or if it starts with a `..`
                if fpath.startswith('..'):
                    # need to symlink
                    symlink = True
            else:
                # check if it is within ${CWD}
                if fpath.startswith(os.getcwd() + '/'):
                    # great, it's already in ${CWD}/
                    # so we're done!
                    fpath_without_cwd = fpath.replace(os.getcwd() + '/', '')
                    print("not need to symlink")
                    print(fpath_without_cwd)
                    fpath = fpath_without_cwd
                else:
                    # it's somewhere else, need to symlink
                    print("need to symlink")
                    symlink = True

            # if we need to symlink
            if symlink:
                # make a data directory
                try:
                    os.mkdir('/tmp')
                except OSError:
                    pass

                # file will be symlinked to ${CWD}/data/
                file_in_data_dir = os.path.join(os.getcwd(), 'tmp',
                                                os.path.basename(fpath))

                print(file_in_data_dir)
                print(fpath)

                # if the symlink fails because it already exists,
                # woohoo, just use the existing one
                try:
                    os.symlink(fpath, file_in_data_dir)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        print('Directory not created.')
                    else:
                        raise

                # set ``fpath`` to just the relative path so we can get it via
                # the Jupyter API (i.e., http://${HOST}:${PORT}/files/data/...)
                fpath = os.path.join('data', os.path.basename(fpath))

        self.href_obj = {
            "filename": fpath,
            "layerType": layer_type,
        }
        if self.href_obj not in self.hrefs:
            self.hrefs.append(self.href_obj)
            self.oldHrefs = self.hrefs

    @register_line_cell_magic
    def overlay_href(self, path):
        if path.startswith("http"):
            url = path
            r = requests.get(url)
            filename = path.split('/')[-1]
            with open(filename, 'wb') as f:
                f.write(r.content)
            self.inputs.append(filename)
        else:
            self.inputs.append(path)

    def display_as_png(self):
        print("Hello")

    @register_line_cell_magic  # noqa: C901
    def plot(self, layer_type='1D', subsize=None):
        try:
            display(self)
            for arg in self.inputs:
                if isinstance(arg, (tuple, list, np.ndarray)):
                    data = arg
                    if layer_type == "2D":
                        data = np.asarray(data)
                        if len(data.shape) != 2 and subsize is None:
                            raise ValueError(
                                "For layer_type 2D: data passed in needs"
                                " to be a 2-D array or ``subsize`` "
                                "must be provided"
                            )
                        elif len(data.shape) == 2 and subsize is None:
                            subsize = data.shape[-1]
                            data = data.flatten().tolist()
                        elif len(data.shape) == 2 and subsize is not None:
                            data = data.flatten().tolist()
                        elif len(data.shape) == 1 and subsize is not None:
                            data = arg
                        else:
                            raise ValueError(
                                "For layer_type 2D: data passed in needs"
                                " to be a 2-D array or provide a valid subsize"
                            )
                    else:
                        if isinstance(arg, np.ndarray):
                            data = data.tolist()
                    self.show_array(
                        data, layer_type=layer_type, subsize=subsize)

                else:
                    sub_args = arg.split('|')
                    for sub_arg in sub_args:
                        self.show_href(sub_arg, layer_type)
            self.done = True
        except Exception:
            clear_output()
            raise

    @register_line_cell_magic
    def overlay_file(self, path):
        if not isinstance(path, str):
            raise TypeError(
                "``path`` must be a string or ``Path`` (Python 3) type"
            )
        self.inputs.append(path)
