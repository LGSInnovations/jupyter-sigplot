#!/usr/bin/env python
from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)
import errno
import os
import sys

import numpy as np

import ipywidgets as widgets
from traitlets import (
    Unicode,
    Bool,
    Dict,
    List,
)

import requests

from IPython.display import (
    display,
    clear_output,
)

_py3k = sys.version_info[0] == 3
if _py3k:
    StringType = (str, bytes)
else:
    StringType = (basestring, )


class SigPlot(widgets.DOMWidget):
    _view_module_version = Unicode('0.1.0')
    _view_name = Unicode('SigPlotView').tag(sync=True)
    _model_name = Unicode('SigPlotModel').tag(sync=True)
    _view_module = Unicode('jupyter_sigplot').tag(sync=True)
    _model_module = Unicode('jupyter_sigplot').tag(sync=True)
    href_obj = Dict().tag(sync=True)
    array_obj = Dict().tag(sync=True)
    done = Bool(False).tag(sync=True)
    options = Dict().tag(sync=True)
    oldArrays = List().tag(sync=True)
    oldHrefs = List().tag(sync=True)
    # Sequence of callables used by _prepare_file_input to resolve relative
    # pathnames
    path_resolvers = []

    def __init__(self, *args, **kwargs):
        self.inputs = []
        self.hrefs = []
        self.arrays = []
        # Where to look for data, and where to cache/symlink remote resources
        # that the server or client cannot access directly. Note that changing
        # the kernel's current directory affects data_dir if it is set as a
        # relative path.
        self.data_dir = kwargs.pop('data_dir', '')

        if 'path_resolvers' in kwargs:
            # Don't use pop()+default because we don't want to override class-
            # level values when not specified here, and we do want to allow
            # specifying None to remove any resolvers.
            #
            # Note that instance-level resolvers will override class-level
            # resolvers per Python semantics.
            self.path_resolvers = kwargs.pop('path_resolvers')

        # Whatever's left is meant for the client half of the widget
        self.options = kwargs
        for arg in args:
            if isinstance(arg, StringType):
                self.overlay_href(arg)
            else:
                self.overlay_array(arg)
        super(SigPlot, self).__init__(**kwargs)

    def change_settings(self, **kwargs):
        new_options = {}
        new_options.update(self.options)
        new_options.update(kwargs)
        self.options = new_options

    def show_array(self, data, overrides=None, layer_type=None, subsize=None):
        array_obj = _prepare_array_input(data, overrides, layer_type, subsize)
        self._show_array_internal(array_obj)

    def _show_array_internal(self, array_obj):
        if array_obj in self.arrays:
            return
        else:
            self.array_obj = array_obj
            self.arrays.append(self.array_obj)
            self.oldArrays = self.arrays

    def overlay_array(self, data, overrides=None,
                      layer_type=None, subsize=None):
        array_obj = _prepare_array_input(data, overrides, layer_type, subsize)
        self.inputs.append(array_obj)

    def show_href(self, fpath, layer_type):  # noqa: C901
        """
        Plot a local file or URL with SigPlot. Any resource that
        cannot be reached directly by the Jupyter server will first
        be copied or symlinked into a subdirectory of the Jupyter
        server's working directory.

        :param fpath: File-path to bluefile or matfile. Forms accepted:
                      - Filesystem paths, e.g., /data/foo.tmp, ../foo.tmp
                        Environment variables and ~ are expanded:
                        - $HOME/foo.tmp
                        - ~/foo.tmp
                      - URLs, e.g., http://example.com/foo.tmp
        :type fpath: str

        :param layer_type: either '1D' or '2D'
        :type layer_type: str

        :Example:
        >>> plot = SigPlot()
        >>> display(plot)
        >>> plot.show_href('foo.tmp', layer_type='2D')
        """
        for pi in _prepare_href_input(fpath,
                                      self.data_dir,
                                      self.path_resolvers):
            href_obj = {
                "filename": pi,
                "layerType": layer_type,
            }
            self._show_href_internal(href_obj)

    def _show_href_internal(self, href_obj):  # noqa: C901
        """
        Common internal function to actually trigger a client-side plot.

        :param href_obj: Dictionary describing what to plot. Interpreted
                         by the client. Created by user-facing functions
                         like overlay_href and show_href.
        :type href_obj: dict
        """
        # The change listener on the client will cheerfully re-plot a layer
        # unless we're careful
        if href_obj in self.hrefs:
            return

        self.href_obj = href_obj
        self.hrefs.append(self.href_obj)
        self.oldHrefs = self.hrefs

    def overlay_href(self, paths):
        # TODO (sat 2018-11-08): This does not trigger a plot update like
        # show_href does. Seems like a recipe for confusion. Should probably
        # only add to self.inputs if we're not yet rendered, and otherwise
        # jump right to _show_href_internal; or clear self.inputs after we've
        # consumed it, add to self.inputs here, and trigger self.plot()
        prepared_paths = _prepare_href_input(paths,
                                             self.data_dir,
                                             self.path_resolvers)
        self.inputs.extend(prepared_paths)

    def plot(self, layer_type=None):
        try:
            display(self)
            for arg in self.inputs:
                if isinstance(arg, dict):
                    if 'data' in arg.keys():
                        self._show_array_internal({
                            "data": arg['data'],
                            "overrides": arg['overrides'],
                            "layerType": arg['layerType'],
                            })
                elif isinstance(arg, StringType):
                    if layer_type is None:
                        layer_type = "1D"
                    self._show_href_internal({
                        "filename": arg,
                        # TODO (sat 2018-11-09): I think we should specify
                        # layer type in overlay_*, allowing each resource to
                        # have its own layer type. Need to reason about
                        # multiple 2D layers, though.
                        "layerType": layer_type,
                    })
                else:
                    raise ValueError("Unknown input type")
            self.done = True
        except Exception:
            clear_output()
            raise

    def overlay_file(self, path):
        if not isinstance(path, StringType):
            raise TypeError(
                "``path`` must be a string or ``Path`` (Python 3) type"
            )
        self.overlay_href(path)

# End of class SigPlot
###########################################################################


def _prepare_array_input(data, overrides, layer_type, subsize):
    if not isinstance(data, (list, tuple, np.ndarray)):
        # TODO (ddw/sat 20190419) we need a stronger check.  What if it's an
        # array of strings?  Consider ['foo', sys], which will pass np.array()
        # but not convert to JSON, nor be plottable
        raise TypeError("Data need to be list, tuple, or ndarray")

    data = np.array(data)

    if len(data.shape) > 2:
        raise ValueError(
                'SigPlot only supports 1- and 2-dimensional inputs (got %r)' %
                (data.shape,))

    new_overrides = {}
    if overrides:
        if not isinstance(overrides, dict):
            raise TypeError(
                    'Overrides should be a dictionary (got %r)' %
                    overrides)
        new_overrides.update(overrides)

    if layer_type not in ("1D", "2D"):
        # Guess layer_type from data
        if len(data.shape) == 2:
            layer_type = "2D"
        else:
            layer_type = "1D"

    if layer_type == "2D" and not subsize:
        subsize = data.shape[-1]

    if subsize:
        new_overrides["subsize"] = subsize

    data = data.flatten().tolist()
    array_obj = {
        "data": data,
        "overrides": new_overrides,
        "layerType": layer_type,
    }

    return array_obj


def _require_dir(d):
    if d == '':
        # makedirs fails on ''
        d = '.'

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

    if not isinstance(url, StringType):
        raise TypeError("url must be of type str (%r has type %s)" %
                        (url, type(url)))

    if not isinstance(local_dir, StringType):
        raise TypeError("local_dir must be of type str (%r has type %s)" %
                        (local_dir, type(local_dir)))

    if not url:
        raise ValueError("Path %r is not a valid filename" % url)

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
    Given a URI, fetch the named resource to a file in <local_dir>, to avoid
    CORS issues.

    :return: A filename in the local filesystem, under <local_dir>
    """
    _require_dir(local_dir)

    local_fname = _local_name_for_href(url, local_dir)
    r = requests.get(url)
    with open(local_fname, 'wb') as f:
        f.write(r.content)
    # TODO (sat 2018-11-07): Make sure we do the right thing if <local_dir>
    # is an absolute path, doesn't exist, etc.
    #
    # The client side of the widget will automatically look for a path
    # relative to <local_dir>
    return local_fname


def _unravel_path(path, resolvers=None):
    """
    Expand user directories and environment variables in <path>, then run
    through callables in <resolvers>. Does NOT call realpath / abspath unless
    that happens to be in <resolvers>.
    """
    import os.path as p
    unraveled = p.expanduser(p.expandvars(path))
    if resolvers:
        for f in resolvers:
            unraveled = f(unraveled)
    return unraveled


def _local_name_for_file(fpath, local_dir):
    """
    Generate a name for the given a file path under <local_dir> . Expects
    arguments to already be unraveled.

    :return: tuple (path, is_local) where
             <path> is a path starting at <local_dir> suitable for storing
                    a link to, or the contents of, <fpath>
             <is_local> is a bool, true iff <fpath> is already a
                    descendant of <local_dir>

    .. note:: Different <fname> values may map to the same local path
    """
    import os.path as p

    if not isinstance(fpath, StringType):
        raise TypeError("fpath must be of type str (%r has type %s)" %
                        (fpath, type(fpath)))

    if not isinstance(local_dir, StringType):
        raise TypeError("local_dir must be of type str (%r has type %s)" %
                        (local_dir, type(local_dir)))

    if not fpath:
        raise ValueError("Path %r is not a valid filename" % fpath)

    abs_fpath = p.realpath(fpath)
    abs_local_dir = p.realpath(local_dir)

    # A bit clunky but works okay for now
    if abs_fpath.startswith(abs_local_dir):
        is_local = True
        local_relative_path = abs_fpath[len(abs_local_dir + os.path.sep):]
    else:
        is_local = False
        local_relative_path = os.path.basename(abs_fpath)

    return (os.path.join(local_dir, local_relative_path), is_local)


def _prepare_file_input(orig_fname, local_dir, resolvers=None):
    """
    Given an arbitrary filename, determine whether that file is a child of
    <local_dir>. If not, create a symlink under <local_dir> that points to the
    original file, so the Jupyter server can resolve it.

    :param resolvers: sequence of callables to be applied, in order, to
    <orig_fname>. Could be used to normalize case, look up bare paths in
    system- specific search paths, etc. <orig_fname> will have environment
    variables and user directories expanded before it is given to the first
    resolver.

    :return: A filename in the local filesystem, under <local_dir>
    """
    input_path = _unravel_path(orig_fname, resolvers)

    # TODO (sat 2018-11-07): Handle errors more thoroughly
    # * unable to make local path
    # * symlink already exists, to wrong target
    # * original file does not exist / has bad perms
    _require_dir(local_dir)

    # TODO (sat 2018-11-07): Do the right thing if <local_dir> is absolute
    local_fname, is_local = _local_name_for_file(input_path, local_dir)
    if not is_local:
        try:
            # Note that _unravel_path keeps relative names like ../foo.tmp
            # will as is, only applying user specifications like ~someone,
            # environment variables, and any explicit resolvers. This is
            # intended to make links as human-comprehensible as possible.
            os.symlink(input_path, local_fname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    return local_fname


def _split_inputs(orig_inputs):
    """
    Given an input specification containing one or more filesystem paths and
    URIs separated by '|', return a list of individual inputs.

    * Skips blank entries
    * Removes blank space around entries
    """
    # (sat 2018-11-19): If we want to support direct list inputs, this is the
    # place to handle that.
    inputs = orig_inputs.split('|')
    inputs = [ii.strip() for ii in inputs]
    inputs = [ii for ii in inputs if ii]
    return inputs


def _prepare_href_input(orig_inputs, local_dir, resolvers=None):
    """
    Given an input specification containing one or more filesystem paths and
    URIs separated by '|', prepare each one according to its type.

    :return: A list of filenames in the local filesystem, under <local_dir>
    """
    prepared = []

    for oi in _split_inputs(orig_inputs):
        if oi.startswith("http"):
            pi = _prepare_http_input(oi, local_dir)
        else:
            # TODO (sat 2019-01-08): This `resolvers` argument  feels like a
            # bad factoring, since only one branch uses it; may want to move
            # _prepare_href_input to a class member or else replace with a
            # split+dispatch idiom at the point of call.
            pi = _prepare_file_input(oi, local_dir, resolvers)
        prepared.append(pi)
    return prepared
