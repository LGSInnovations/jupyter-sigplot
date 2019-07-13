#!/usr/bin/env python
import os

import numpy as np
import pytest
from mock import patch
from IPython.testing.globalipapp import get_ipython

ip = get_ipython()

from jupyter_sigplot.sigplot import Plot  # noqa: E402
from testutil import EnvironmentVariable  # noqa: E402


###########################################################################
# Basic tests.  Can we create a plot?
###########################################################################


def test_empty_object():
    plot = Plot()
    # instance variables
    assert plot.data_dir == ''
    assert plot.path_resolvers == []
    # traitlets
    assert plot.command_and_arguments == {}
    assert plot.plot_options == {}
    assert plot.progress == 0.0
    assert not plot.done


def test_non_empty_object():
    data_dir = "/tmp"
    path_resolvers = ["/data"]
    options = {'noyaxis': True, 'noxaxis': True}
    plot = Plot(
        data_dir=data_dir,
        path_resolvers=path_resolvers,
        **options
    )
    # instance variables
    assert plot.data_dir == data_dir
    assert plot.path_resolvers == path_resolvers

    # traitlets
    assert plot.command_and_arguments == {}
    assert plot.plot_options == options
    assert plot.progress == 0.0
    assert not plot.done


def test_available_commands():
    plot = Plot()
    available_commands = [
        'change_settings',
        'overlay_href',
        'overlay_array',
    ]
    assert plot.available_commands == available_commands


###########################################################################
# Command tests
###########################################################################


def test_getattr_change_settings():
    plot = Plot()
    options = {'autol': 1000}
    plot.change_settings(options)
    assert plot.command_and_arguments == {
        'command': 'change_settings',
        'arguments': [options]
    }


def test_UPPERCASE_getattr_change_settings():
    plot = Plot()
    options = {'autol': 1000}
    with pytest.raises(AttributeError):
        plot.CHANGE_SETTINGS(options)


def test_attr_error():
    plot = Plot()
    with pytest.raises(AttributeError):
        plot.foobar('blah')


def test_overlay_array():
    plot = Plot()
    lst = [1, 2, 3]
    plot.overlay_array(lst)
    assert plot.command_and_arguments == {
        'command': 'overlay_array',
        'arguments': [memoryview(np.array(lst, dtype=np.float32)).tobytes()],
    }


def test_overlay_array_bad_type():
    plot = Plot()
    lst = ['foo', 'bar', 'baz']
    with pytest.raises(TypeError):
        plot.overlay_array(lst)


def test_overlay_array_numpy():
    plot = Plot()
    lst = np.array([1, 2, 3])
    plot.overlay_array(lst)
    assert plot.command_and_arguments == {
        'command': 'overlay_array',
        'arguments': [memoryview(lst.astype(np.float32)).tobytes()],
    }


def test_overlay_array_numpy_bad_dtype():
    plot = Plot()
    lst = np.array(['foo', 'bar', 'baz'])
    with pytest.raises(TypeError):
        plot.overlay_array(lst)


@patch('jupyter_sigplot.sigplot.Plot.sync_command_and_arguments')
def test_overlay_href(traitlet_set_mock):
    plot = Plot()
    plot.overlay_href('bar|baz')
    assert traitlet_set_mock.call_count == 2
    for call_args in traitlet_set_mock.call_args_list:
        assert call_args[0][0]['command'] == 'overlay_href'
        assert len(call_args[0][0]['arguments']) == 1
        assert call_args[0][0]['arguments'][0] in ('bar', 'baz')


###########################################################################
# Other tests
###########################################################################


def test_unravel_path_no_resolvers():
    import time
    from jupyter_sigplot.sigplot import _unravel_path

    tilde_full = os.path.expanduser('~')

    # Go all the way through the environment instead of a mock to be sure the
    # whole thing works end to end
    with EnvironmentVariable('TEST_UNRAVEL', str(time.time())) as envvar:
        env_key = envvar.key
        env_val = envvar.new_value

        cases = [
            # input                 # expected output
            ('',                    ''),
            ('.',                   '.'),

            ('~',                   tilde_full),

            ('$%s' % env_key,       env_val),
            ('/$%s' % env_key,      os.path.join('/', env_val)),

            ('~/$%s' % env_key,     os.path.join(tilde_full, env_val)),
        ]

        for (input, expected) in cases:
            actual = _unravel_path(input)
            assert(actual == expected)


@patch('os.path.expanduser')  # noqa: C901
@patch('os.path.expandvars')
def test_unravel_path_resolvers(expandvars_mock, expanduser_mock):
    # This test isolates just the behavior of the `resolvers` argument to
    # _unravel_path. The set of test cases grows rather quickly if you cross
    # resolver equivalence classes with input equivalence classes, so we'll
    # just trust that testing each axis independently is sufficient.
    from jupyter_sigplot.sigplot import _unravel_path

    # Set up scaffolding to record the names of functions, in order, as they
    # are called.
    call_list = []

    def reset():
        call_list[:] = []

    # Note that all functions take a single argument
    def make_recorder(name):
        def f(a):
            call_list.append(name)
            return a
        return f

    def recordit(f):
        r = make_recorder(f.__name__)

        def wrapped(a):
            r(a)
            return f(a)
        wrapped.__name__ = f.__name__
        return wrapped

    expandvars_mock.side_effect = make_recorder('expandvars')
    expanduser_mock.side_effect = make_recorder('expanduser')

    @recordit
    def one(p): return p + '1'

    @recordit
    def two(p): return p + '2'

    @recordit
    def three(p): return p + '3'

    for resolvers, expected in [
            ([],                     ''),
            ([one],                  '1'),
            ([one, two],             '12'),
            ([two, one],             '21'),
            ([one, two, three],      '123'),
            ([three, two, one, one], '3211'),
    ]:
        reset()
        expected_names = ['expandvars', 'expanduser'] + \
                         [f.__name__ for f in resolvers]
        actual = _unravel_path('', resolvers)
        # Ensure that resolvers are called in the right sequence relative to
        # one another and relative to expandvars/expanduser
        assert(call_list == expected_names)
        # Ensure that resolvers are composed (output of rN is input of rN+1)
        assert(actual == expected)

    # Check that we get an error when resolvers arg is not as expected
    for resolvers in [
        3,
        # 0, Equivalent to resolvers=None, i.e., no resolvers
        'a string',
        [3, 0],
        ['a string'],
    ]:
        with pytest.raises(TypeError):
            _unravel_path('foo.tmp', resolvers)


@patch('os.mkdir')
def test_require_dir_good_inputs(mkdir_mock):
    from jupyter_sigplot.sigplot import _require_dir

    inputs = (
        '.',
        'data',
    )

    for d in inputs:
        _require_dir(d)
        args, kwargs = mkdir_mock.call_args
        assert args[0] == d

    assert mkdir_mock.call_count == len(inputs)

    # Special case: '' means '.'
    _require_dir('')
    assert mkdir_mock.call_args[0][0] == '.'


def test_local_name_for_href_good_inputs():
    from jupyter_sigplot.sigplot import _local_name_for_href

    cases = [
        # input                     # expected output
        ('http://www.example.com/foo.tmp',      'foo.tmp'),
        ('http://www.example.com/dat/foo.tmp',  'foo.tmp'),
        ('https://localhost/foo.tmp',           'foo.tmp'),
        ('https://localhost/dat/foo.tmp',       'foo.tmp'),
    ]
    local_dirs = ['.', 'data', 'files/data', '/path/to/data', ]

    for ld in local_dirs:
        for (input, expected) in cases:
            actual = _local_name_for_href(input, ld)
            expected = os.path.join(ld, expected)
            assert(actual == expected)


def test_local_name_for_href_bad_inputs():
    from jupyter_sigplot.sigplot import _local_name_for_href
    cases = [
        # url                         local_dir       exception
        ('http://localhost/foo.tmp',  None,           TypeError),
        (None,                        '.',            TypeError),
        ('',                          '.',            ValueError),
    ]
    for url, local_dir, etype in cases:
        with pytest.raises(etype):
            _local_name_for_href(url, local_dir)

    # TODO (sat 2018-11-19): Decide whether we want _local_name_for_href to
    # validate URLs more strictly; if so, add tests here.


def test_local_name_for_file_local_good_inputs():
    from jupyter_sigplot.sigplot import _local_name_for_file
    cases = [
        # input                     # expected output
        ('foo.tmp',                 'foo.tmp'),
        ('dat/foo.tmp',             'dat/foo.tmp'),
    ]
    local_dirs = ['.', 'data', 'files/data', '/path/to/data', ]

    # None of these should require symlinks
    for ld in local_dirs:
        for (input, expected) in cases:
            # This test could definitely be stronger. The current idea is just
            # to ensure that some basic cases work right.
            input = os.path.join(ld, input)

            actual, is_local = _local_name_for_file(input, ld)
            assert is_local
            expected = os.path.join(ld, expected)
            assert(actual == expected)


def test_local_name_for_file_nonlocal_good_inputs():
    from jupyter_sigplot.sigplot import _local_name_for_file
    cases = [
        # input                     # expected output
        ('/data/foo.tmp',           'foo.tmp'),
        ('../dat/foo.tmp',          'foo.tmp'),
        ('../foo.tmp',              'foo.tmp'),
        ('data/../../foo.tmp',      'foo.tmp'),
    ]
    local_dirs = ['.', 'data', 'files/data', '/path/to/data', ]

    # All these should require symlinks
    for ld in local_dirs:
        for (input, expected) in cases:
            actual, is_local = _local_name_for_file(input, ld)
            assert not is_local
            expected = os.path.join(ld, expected)
            assert(actual == expected)


def test_local_name_for_file_bad_inputs():
    from jupyter_sigplot.sigplot import _local_name_for_file
    cases = [
        # fpath             local_dir       exception
        ('foo.tmp',         None,           TypeError),
        (None,              '.',            TypeError),
        ('',                '.',            ValueError),
    ]
    for fpath, local_dir, etype in cases:
        with pytest.raises(etype):
            _local_name_for_file(fpath, local_dir)


@patch('jupyter_sigplot.sigplot._unravel_path')
def test_prepare_file_input_resolver(unravel_path_mock):
    """
    Ensure that resolvers get passed through from _prepare_file_input to
    _unravel_path
    """
    from jupyter_sigplot.sigplot import _prepare_file_input

    # Needed to avoid a type error internal to _prepare_file_input; value is
    # unimportant, but type matters
    unravel_path_mock.return_value = 'bar.tmp'

    def one(f): pass

    fname = 'foo.tmp'
    for resolvers in [
        [],
        [one],
    ]:
        unravel_path_mock.reset_mock()
        _prepare_file_input(fname, '', resolvers)
        unravel_path_mock.assert_called_once_with(fname, resolvers=resolvers)


def test_instance_level_resolver():
    from jupyter_sigplot.sigplot import Plot

    def to_foo(_):
        return 'foo'

    # If a single path resolver makes it all the way through the prepare step,
    # we assume that other tests ensure more complicated cases do, too.

    # Resolver specified in constructor
    p = Plot(path_resolvers=[to_foo])
    p.overlay_href('baz')
    assert p.path_resolvers == [to_foo]
    assert p.command_and_arguments == {
        'command': 'overlay_href',
        'arguments': ['foo']
    }

    # Resolver specified after construction
    p = Plot()
    p.path_resolvers = [to_foo]
    p.overlay_href('quux')
    assert p.path_resolvers == [to_foo]
    assert p.command_and_arguments == {
        'command': 'overlay_href',
        'arguments': ['foo']
    }


@patch('jupyter_sigplot.sigplot.Plot.sync_command_and_arguments')
def test_class_level_resolver(traitlet_set_mock):
    from jupyter_sigplot.sigplot import Plot

    def to_foo(_):
        return 'foo'

    Plot.path_resolvers = [to_foo]

    # Resolver applied post constructor
    p = Plot()
    p.overlay_href('baz|quux.mat')
    assert traitlet_set_mock.call_count == 2
    for call_args in traitlet_set_mock.call_args_list:
        assert call_args[0][0]['command'] == 'overlay_href'
        assert len(call_args[0][0]['arguments']) == 1
        assert call_args[0][0]['arguments'][0] == 'foo'


def test_split_inputs():
    from jupyter_sigplot.sigplot import _split_inputs
    cases = [
        # input                     # expected output
        ('',                        []),
        ('a',                       ['a']),
        ('a|b',                     ['a', 'b']),

        ('file.tmp',                ['file.tmp']),
        ('file.tmp|http://url/',    ['file.tmp', 'http://url/']),

        ('  a ',                    ['a']),
        ('  a |  b ',               ['a', 'b']),

        ('|',                       []),
        ('||',                      []),
        ('a|',                      ['a']),
        ('|a',                      ['a']),
        ('||a|||',                  ['a']),
        ('||a|||b|',                ['a', 'b']),
        ('  | ||  | ',              []),
    ]
    for (input, expected) in cases:
        actual = _split_inputs(input)
        assert(actual == expected)


@patch('jupyter_sigplot.sigplot._prepare_file_input')
@patch('jupyter_sigplot.sigplot._prepare_http_input')
def test_prepare_href_input(prepare_http_input_mock,
                            prepare_file_input_mock):
    from jupyter_sigplot.sigplot import _prepare_href_input

    # The value is unimportant for this test
    local_dir = None

    def reset():
        for m in (prepare_file_input_mock,
                  prepare_http_input_mock,
                  ):
            m.reset_mock()

    # empty input
    _prepare_href_input('', None, local_dir)
    prepare_http_input_mock.assert_not_called()
    prepare_file_input_mock.assert_not_called()

    # file only
    reset()
    _prepare_href_input('foo.tmp', local_dir)
    prepare_http_input_mock.assert_not_called()
    prepare_file_input_mock.assert_called_once_with('foo.tmp', local_dir, None)

    # url only
    reset()
    _prepare_href_input('https://www.example.com/bar.tmp', local_dir)
    prepare_http_input_mock.assert_called_once_with(
        'https://www.example.com/bar.tmp',
        local_dir,
        progress=None
    )
    prepare_file_input_mock.assert_not_called()

    # file and url
    reset()
    _prepare_href_input('foo.tmp|https://www.example.com/bar.tmp', local_dir)
    prepare_http_input_mock.assert_called_once_with(
        'https://www.example.com/bar.tmp',
        local_dir,
        progress=None
    )
    prepare_file_input_mock.assert_called_once_with('foo.tmp', local_dir, None)

    # order independence
    reset()
    _prepare_href_input('https://www.example.com/bar.tmp|foo.tmp', local_dir)
    prepare_http_input_mock.assert_called_once_with(
        'https://www.example.com/bar.tmp',
        local_dir,
        progress=None
    )
    prepare_file_input_mock.assert_called_once_with('foo.tmp', local_dir, None)

    # multiple of each
    reset()
    _prepare_href_input(
        'https://www.example.com/bar.tmp| foo.tmp|baz.tmp|http://www.example.com/quux.tmp  | xyzzy.prm',  # noqa: E501
        local_dir,
        progress=None
    )
    assert prepare_http_input_mock.call_count == 2
    assert prepare_file_input_mock.call_count == 3
