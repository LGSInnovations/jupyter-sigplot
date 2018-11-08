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
        self.data_dir = 'data'
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
        # TODO (sat 2018-11-06): I believe this can trigger extraneous logic
        # in the client; we should first check whether the new array_obj is
        # already in oldArrays, and only assign to self.array_obj if it's not
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
                      - URL, e.g., http://website.com/foo.tmp
        :type fpath: str

        :param layer_type: either '1D' or '2D'
        :type layer_type: str

        :Example:
        >>> plot = SigPlot()
        >>> display(plot)
        >>> plot.overlay_href('foo.tmp', layer_type='2D')
        """
        # TODO (sat 2018-11-07): I moved preparation out to overlay_href,
        # making the docstring into a lie. Need to decide where everything
        # belongs / what promises each function wants to make.

        # TODO (sat 2018-11-06): I believe this can trigger extraneous logic
        # in the client; we should first check whether the new href_obj is
        # already in oldHrefs, and only assign to self.href_obj if it's not
        self.href_obj = {
            "filename": fpath,
            "layerType": layer_type,
        }
        if self.href_obj not in self.hrefs:
            self.hrefs.append(self.href_obj)
            self.oldHrefs = self.hrefs

    @register_line_cell_magic
    def overlay_href(self, paths):
        # TODO (sat 2018-11-08): This does not trigger a plot update
        # like show_href does. Seems like a recipe for confusion.
        for path in paths.split('|'):
            if path.startswith("http"):
                prepared_path = _prepare_http_input(path, self.data_dir)
            else:
                prepared_path = _prepare_file_input(path, self.data_dir)
            self.inputs.append(prepared_path)

    def display_as_png(self):
        print("Hello")

    @register_line_cell_magic  # noqa: C901
    def plot(self, layer_type='1D', subsize=None):
        try:
            display(self)
            for arg in self.inputs:
                if isinstance(arg, (tuple, list, np.ndarray)):
                    # TODO (sat 2018-11-08): I think this needs to move into a
                    # function so we can test it better. At that point, we may
                    # also be able to specify it as the serializer for the
                    # traitlet via the `to_json` keyword argument
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
                    # All href arguments are already separated and prepared
                    # by overlay_href
                    self.show_href(arg, layer_type)
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
        self.overlay_href(path)


def _require_dir(d):
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def _local_name_for_href(url, local_dir):
    """
    Generate a name for the given url under directory <local_dir>

    :return: A path under <local_dir> suitable for storing the contents
             of <url>

    .. note:: Different <url> values may map to the same local path
    """
    # This function has no side effects, unlike its primary caller,
    # _prepare_http_input . The goal is to make testing easier.

    # TODO (sat 2018-11-07): Note that a URL with a query string
    # will result in an odd filename. Better to split the URL
    # more completely, perhaps with urlparse.urlsplit followed by
    # this split on '/'
    basename = url.split('/')[-1]
    local_path = os.path.join(local_dir, basename)
    # TODO (sat 2018-11-07): Either deconflict this path, or
    # decide explicitly that we don't need to
    return local_path


def _prepare_http_input(url, local_dir):
    """
    Given an input specification that starts with 'http', fetch the named
    resource to a file in <local_dir>.

    :return: A local URL that can be served without concern about CORS issues
    """
    _require_dir(local_dir)

    local_fname = _local_name_for_href(url, local_dir)
    r = requests.get(url)
    with open(local_fname, 'wb') as f:
        f.write(r.content)
    # TODO (sat 2018-11-07): Make sure we do the right thing if <local_dir>
    # is an absolute path, doesn't exist, etc.
    #
    # The client side of the widget will automatically look in the data dir
    return local_fname


def _unravel_path(p):
    from os.path import (
        realpath,
        expanduser,
        expandvars,
    )
    return realpath(expanduser(expandvars(p)))


def _local_name_for_file(fpath, local_dir):
    """
    Generate a name for the given a file path under <local_dir>

    :return: tuple (path, is_local) where
             <path> is a path starting at <local_dir> suitable for storing
                    a link to, or the contents of, <fname>
             <is_local> is a bool, true iff <fpath> is already a
                    descendant of <local_dir>

    .. note:: Different <fname> values may map to the same local path

    """
    # TODO (sat 2018-11-07): Consider adding an optional <resolver> callable
    # to transform <fname> into a full path. Could implement the current
    # expanduser+expandvars, but could also implement a domain-specific search
    # path for unadorned filenames, etc.

    fpath = _unravel_path(fpath)
    abs_local_dir = _unravel_path(local_dir)

    # A bit clunky but works okay for now
    if fpath.startswith(abs_local_dir):
        is_local = True
        local_relative_path = fpath[len(abs_local_dir + os.path.sep):]
    else:
        is_local = False
        local_relative_path = os.path.basename(fpath)

    return (os.path.join(local_dir, local_relative_path), is_local)


def _prepare_file_input(orig_fname, local_dir):
    input_path = _unravel_path(orig_fname)

    # TODO (sat 2018-11-07): Handle errors more thoroughly
    # * unable to make local path
    # * symlink already exists, to wrong target
    # * original file does not exist / has bad perms
    _require_dir(local_dir)

    # TODO (sat 2018-11-07): Do the right thing if <local_dir> is absolute
    local_fname, is_local = _local_name_for_file(input_path, local_dir)
    if not is_local:
        try:
            os.symlink(input_path, local_fname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    return local_fname
