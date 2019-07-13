#!/usr/bin/env python
from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

import errno
import os
import sys

import ipywidgets as widgets
import numpy as np
import requests
from IPython.display import display
from traitlets import (
    Unicode,
    Bool,
    Dict,
    Float,
)

from ._version import __version__ as version_string

_py3k = sys.version_info[0] == 3
if _py3k:
    StringType = (str, bytes)
else:
    StringType = (basestring,)


class Plot(widgets.DOMWidget):
    """Name and version information required by widgets"""
    _view_module_version = Unicode(version_string)
    _view_name = Unicode('SigPlotView').tag(sync=True)
    _model_name = Unicode('SigPlotModel').tag(sync=True)
    _view_module = Unicode('jupyter_sigplot').tag(sync=True)
    _model_module = Unicode('jupyter_sigplot').tag(sync=True)

    """The command and arguments that will get sent"""
    command_and_arguments = Dict().tag(sync=True)

    """The plot_options dictionary in the JS
    sigplot.Plot(dom_element, plot_options)"""
    plot_options = Dict().tag(sync=True)

    """Progress information for the client"""
    progress = Float().tag(sync=True)
    done = Bool(False).tag(sync=True)

    """Sequence of callables used by ``_prepare_file_input``
    to resolve relative pathnames"""
    path_resolvers = []

    def __init__(self, *args, **kwargs):
        super(Plot, self).__init__(**kwargs)

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

        # Whatever's left is meant for sigplot.js's ``sigplot.Plot``
        self.plot_options = kwargs

        display(self)

    def __getattr__(self, attr):
        """Enables a "thin-wrapper" around sigplot.Plot (JS)
        methods

        Note: ``__getattr__`` is only called if ``attr`` is not
        an attribute of ``self``

        :param attr: An attribute or method
        :type attr: str

        :return: A function wrapper around ``self.send_command``
        :rtype: function
        :raises AttributeError: if ``attr`` is not an attribute of
                                ``self`` or in ``available_commands``
        """
        if attr in self.available_commands:
            # if it doesn't have the attribute,
            # but ``attr`` exists as sigplot.Plot methods
            # that we've whitelisted in ``self.available_commands``,
            # send that command (``attr``) and the arguments
            # provded to the client to handle (via ``send_command``)
            def wrapper(*args, **kwargs):
                command = attr
                arguments = args
                self.send_command(command, list(arguments), **kwargs)
        else:
            # if ``attr`` is not an attribute of ``self``
            # AND does not exist on the client, throw the standard
            # ``AttributeError``
            raise AttributeError(attr)
        return wrapper

    @property
    def available_commands(self):
        """Available commands from Sigplot.js that Jupyter-SigPlot can call"""
        return [
            'change_settings',
            'overlay_href',
            'overlay_array',
        ]

    def send_command(self, command, arguments, **_):
        """Sends the Notebook client (JS) the SigPlot.js
        command and relevant arguments.

        :param command: Command for the ``sigplot.Plot`` JS
                        object to run
        :type command: str

        :param arguments: The tuple of the positional arguments and
                          keyword arguments for SigPlot to run
        :type arguments: list(Any)

        :Example:
        >>> from jupyter_sigplot.sigplot import Plot
        >>> plt = Plot()
        >>> plt.send_command('overlay_href', ['foo.tmp'])
        """
        # lower the command, just so we're normalized
        command = command.lower()

        # we need to convert the array argument to numpy arrays
        if command == 'overlay_array':
            array = np.array(arguments[0])
            # make sure np.dtype is something sigplot can plot
            if not np.issubdtype(array.dtype, np.number):
                raise TypeError(
                    'Array passed to overlay_array must be numeric type'
                )
            arguments[0] = memoryview(array.astype(np.float32)).tobytes()
            # cause the sync to happen
            self.sync_command_and_arguments({
                "command": command,
                "arguments": arguments,
            })
        elif command == 'overlay_href':
            # we still need to download the hrefs locally
            # to avoid CORS
            href = arguments[0]
            href_list = _prepare_href_input(
                href,
                self.data_dir,
                self.progress,
                self.path_resolvers
            )
            for href in href_list:
                arguments[0] = href

                # cause the sync to happen
                # TODO: Figure out why the list comp works
                #       but passing `arguments` doesn't;
                #       perhaps it's an addressing issue?
                self.sync_command_and_arguments({
                    "command": command,
                    "arguments": [arg for arg in arguments],
                })
        else:
            # cause the sync to happen
            self.sync_command_and_arguments({
                "command": command,
                "arguments": arguments,
            })

    def sync_command_and_arguments(self, command_and_arguments):
        """

        :param command_and_arguments:
        :type command_and_arguments: dict
        :return:
        """
        self.command_and_arguments = command_and_arguments


# End of class SigPlot
###########################################################################


def _require_dir(d):
    """Creates the path ``d`` similar to ``mkdir -p``

    :param d: Path to create
    :type d: Union[str, Path]

    :raises: OSError if an error occurs (aside from
             the path already existing)

    :Examples:
    >>> from jupyter_sigplot.sigplot import _require_dir
    >>> import os
    >>> import shutil
    >>> path = '/tmp/foo/bar/baz/1/2/3'
    >>> _require_dir(path)
    >>> os.path.exists(path)
    True
    >>> shutil.rmtree('/tmp/foo')
    >>> os.path.exists(path)
    False
    """
    if d == '':
        # makedirs fails on ''
        d = '.'

    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def _local_name_for_href(url, local_dir):
    """Generate a name for the given url under directory ``local_dir``

    :param url: URL that we'll be downloading to some local directory
                ``local_dir``
    :type url: str

    :param local_dir: Local directory where URL
    :type local_dir: str

    :return: A path under ``local_dir`` suitable for storing the contents
             of ``url``
    :rtype: str or Path

    .. note:: Different ``url`` values may map to the same local path
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


def _prepare_http_input(url, local_dir, progress=None):
    """Given a URI, fetch the named resource to a file in ``local_dir``,
    to avoid CORS issues.

    :param url: URL that we'll be downloading to some local directory
                ``local_dir``
    :type url: str

    :param local_dir: Local directory to where URL will be downloaded
    :type local_dir: str

    :param progress: Progress traitlet that will sync with the client
    :type progress: Optional[traitlets.Float]

    :return: A filename in the local filesystem, under <local_dir>
    """
    _require_dir(local_dir)

    # get where the ``url`` will be downloaded to under ``local_dir``
    local_fname = _local_name_for_href(url, local_dir)

    # `stream=True` lets us stream over the response
    r = requests.get(url, stream=True)

    # get the total file size
    total_size = int(r.headers.get('content-length', 0))

    # we'll want to iterate over the file by chunks
    block_size = 1024

    # how much we've written locally (kernel-side)
    wrote = 0

    # "stream" the remote asset to ``local_file``
    with open(local_fname, 'wb') as f:
        for data in r.iter_content(block_size):
            # keep track of how much we've written
            f.write(data)
            wrote += len(data)

            # update the ``progress`` traitlet, which
            # we will handle on the client-side in some loading
            # notification (e.g., loading bar via tqdm?, spinny wheel, etc.)
            if progress is not None:
                progress = wrote / total_size

    # TODO: Make sure we do the right thing if ``local_dir`` is an
    #       absolute path, doesn't exist, etc.
    #
    # The client side of the widget will automatically look for a path
    # relative to ``local_dir``
    return local_fname


def _unravel_path(path, resolvers=None):
    """Expand user directories and environment variables in ``path``,
    then run through callables in ``resolvers``. Does NOT call
    ``realpath`` / ``abspath`` unless that happens to be in ``resolvers``.

    :param path: Path to be unraveled
    :type path: str or Path

    :param resolvers: Optional list of functions to be applied to ``path``,
                      e.g., ``os.path.abspath`` or ``os.path.realpath``
    :type resolvers: Optional[List[function]]

    :return: The unraveled path
    :rtype: str

    :Example:
    >>> from jupyter_sigplot.sigplot import _unravel_path
    >>>
    """
    unraveled = os.path.expanduser(os.path.expandvars(path))
    if resolvers:
        for f in resolvers:
            unraveled = f(unraveled)
    return unraveled


def _local_name_for_file(file_path, local_dir):
    """Generate a name for the given file path under ``local_dir``.

    :param file_path: File that will be renamed and placed under ``local_dir``
    :type file_path: str

    :param local_dir: Directory where ``file_path`` will be placed
    :type local_dir: str

    :return: tuple (path, is_local) where
             ``path`` is a path starting at ``local_dir`` suitable for storing
                    a link to, or the contents of, ``file_path``
             ``is_local`` is a bool, true iff ``file_path`` is already a
                    descendant of ``local_dir``
    :rtype: Tuple[str, bool]

    .. note:: Different ``fname`` values may map to the same local path
    .. note:: Expects arguments to already be unraveled.
    """
    if not isinstance(file_path, StringType):
        raise TypeError("fpath must be of type str (%r has type %s)" %
                        (file_path, type(file_path)))

    if not isinstance(local_dir, StringType):
        raise TypeError("local_dir must be of type str (%r has type %s)" %
                        (local_dir, type(local_dir)))

    if not file_path:
        raise ValueError("Path %r is not a valid filename" % file_path)

    abs_file_path = os.path.realpath(file_path)
    abs_local_dir = os.path.realpath(local_dir)

    # A bit clunky but works okay for now
    if abs_file_path.startswith(abs_local_dir):
        is_local = True
        local_relative_path = abs_file_path[len(abs_local_dir + os.path.sep):]
    else:
        is_local = False
        local_relative_path = os.path.basename(abs_file_path)

    return os.path.join(local_dir, local_relative_path), is_local


def _prepare_file_input(orig_file_name, local_dir, resolvers=None):
    """Given an arbitrary filename, determine whether that file is a child of
    ``local_dir``. If not, create a symlink under ``local_dir`` that points
    to the original file, so the Jupyter server can resolve it.

    :param orig_file_name: Some arbitrary file that we want to put under
                           ``local_dir``
    :type orig_file_name: str

    :param local_dir: The directory where we'll either check if
                      ``orig_file_name`` exists under, or where we'll
                      link ``orig_file_name``
    :type local_dir: str

    :param resolvers: sequence of callables to be applied, in order, to
                      ``orig_file_name``. Could be used to normalize case,
                      look up bare paths in system-specific search paths, etc.
                      ``orig_file_name`` will have environment variables and
                      user directories expanded before it is given to the
                      first resolver.
    :type resolvers: Optional[Sequence[function]]

    :return: A filename in the local filesystem, under ``local_dir``
    :rtype: str
    """
    input_path = _unravel_path(orig_file_name, resolvers=resolvers)

    # TODO: Handle errors more thoroughly
    #       * unable to make local path
    #       * symlink already exists, to wrong target
    #       * original file does not exist / has bad perms
    _require_dir(local_dir)

    # TODO (sat 2018-11-07): Do the right thing if ``local_dir`` is absolute
    local_fname, is_local = _local_name_for_file(input_path, local_dir)
    if not is_local:
        try:
            # Note that ``_unravel_path`` keeps relative names like ../foo.tmp
            # will as is, only applying user specifications like ~someone,
            # environment variables, and any explicit resolvers. This is
            # intended to make links as human-comprehensible as possible.
            os.symlink(input_path, local_fname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    return local_fname


def _split_inputs(orig_inputs):
    """Given an input specification containing one or more filesystem paths and
    URIs separated by '|', return a list of individual inputs.

    * Skips blank entries
    * Removes blank space around entries

    :param orig_inputs: One or more filesystem paths and/or
                        URIs separated by '|'
    :type orig_inputs: str

    :return: List of the individual inputs specified in ``orig_inputs``
    :rtype: list(str)

    :Example:
    >>> from sigplot import _split_inputs
    >>> _split_inputs('foo|bar')
    ['foo', 'bar']
    """
    # (sat 2018-11-19): If we want to support direct list inputs, this is the
    # place to handle that.
    return [ii.strip() for ii in orig_inputs.split('|') if ii.strip()]


def _prepare_href_input(orig_inputs, local_dir, progress=None, resolvers=None):
    """Given an input specification containing one or more filesystem paths and
    URIs separated by '|', prepare each one according to its type.

    :param orig_inputs: One or more filesystem paths
                        and/or URIs separated by '|'
    :type orig_inputs: str

    :param local_dir: Directory where the ``orig_inputs`` will end up
    :type local_dir: Optional[str]

    :param progress: Optional progress traitlet to provide
                     feedback to the client
    :type progress: Optional[traitlets.Float]

    :param resolvers: sequence of callables to be applied, in order, to
                      ``orig_file_name``. Could be used to normalize case,
                      look up bare paths in system-specific search paths, etc.
                      ``orig_file_name`` will have environment variables and
                      user directories expanded before it is given to the
                      first resolver.
    :type resolvers: Optional[Sequence[function]]

    :return: A list of filenames in the local filesystem, under ``local_dir``
    :rtype: list(str)
    """
    prepared = []

    for oi in _split_inputs(orig_inputs):
        if oi.startswith("http"):
            pi = _prepare_http_input(oi, local_dir, progress=progress)
        else:
            # TODO: This `resolvers` argument  feels like a bad factoring,
            #       since only one branch uses it; may want to move
            #       _prepare_href_input to a class member or else replace
            #       with a split+dispatch idiom at the point of call.
            pi = _prepare_file_input(oi, local_dir, resolvers)
        prepared.append(pi)
    return prepared
