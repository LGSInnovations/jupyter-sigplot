#!/usr/bin/env python
import os

import pytest
from mock import patch
import numpy as np
from IPython.testing.globalipapp import get_ipython

ip = get_ipython()

from jupyter_sigplot.sigplot import SigPlot  # noqa: E402
from testutil import EnvironmentVariable  # noqa: E402


def test_empty_object():
    plot = SigPlot()
    assert plot.inputs == []
    assert plot.hrefs == []
    assert plot.arrays == []
    assert plot.options == {}


def test_non_empty_object():
    plot = SigPlot("foo.tmp")
    assert plot.inputs == ["foo.tmp"]
    assert plot.hrefs == []
    assert plot.arrays == []
    assert plot.options == {}


def test_change_settings():
    options = {'noyaxis': True, 'noxaxis': True}
    plot = SigPlot("foo.tmp", options=options)
    assert plot.inputs == ["foo.tmp"]
    assert plot.hrefs == []
    assert plot.arrays == []
    assert plot.options == options

    new_options = {'noyaxis': False, 'xi': True}
    plot.change_settings(**new_options)
    assert plot.inputs == ["foo.tmp"]
    assert plot.hrefs == []
    assert plot.arrays == []
    assert plot.options == {'noyaxis': False, 'noxaxis': True, 'xi': True}


def test_show_1d_array():
    plot = SigPlot()
    assert plot.arrays == []
    assert plot.array_obj == {}

    data = [1, 2, 3]
    layer_type = '1D'
    plot.show_array(data, layer_type=layer_type)

    array_obj = {
        "data": data,
        "overrides": {},
        "layerType": layer_type,
    }
    assert plot.array_obj == array_obj
    assert plot.arrays == [array_obj]


def test_subsize_show_2d_array():
    plot = SigPlot()
    assert plot.arrays == []
    assert plot.array_obj == {}

    data = [[1, 2, 3], [3, 4, 5]]
    layer_type = '2D'
    subsize = len(data[0])
    plot.show_array(data, layer_type=layer_type, subsize=subsize)

    array_obj = {
        "data": data,
        "overrides": {
            "subsize": subsize
        },
        "layerType": layer_type,
    }
    assert plot.array_obj == array_obj
    assert plot.arrays == [array_obj]


def test_no_subsize_show_2d_array():
    plot = SigPlot()
    data = [[1, 2, 3], [3, 4, 5]]
    with pytest.raises(ValueError):
        plot.show_array(data, layer_type='2D', subsize=None)


def test_overlay_array_bad_type():
    plot = SigPlot()
    assert plot.inputs == []

    data = 3
    with pytest.raises(TypeError):
        plot.overlay_array(data)


def test_overlay_array_empty():
    plot = SigPlot()
    assert plot.inputs == []

    data = []
    plot.overlay_array(data)
    assert plot.inputs == [data]


def test_overlay_array_non_empty():
    plot = SigPlot()
    assert plot.inputs == []

    data = [1, 2, 3]
    plot.overlay_array(data)
    assert plot.inputs == [data]


def test_show_href_url():
    plot = SigPlot()
    assert plot.href_obj == {}
    assert plot.hrefs == []

    path = "http://sigplot.lgsinnovations.com/dat/sin.tmp"
    layer_type = "1D"
    plot.show_href(path, layer_type)

    href_obj = {
        "filename": "sin.tmp",
        "layerType": layer_type,
    }
    assert plot.href_obj == href_obj
    assert plot.hrefs == [href_obj]
    assert plot.oldHrefs == [href_obj]

    assert os.path.exists("./sin.tmp")
    os.remove("./sin.tmp")


def test_show_href_file_absolute_already_in_cwd():
    plot = SigPlot()

    assert plot.inputs == []

    path = os.path.join(os.getcwd(), "sin.tmp")
    plot.show_href(path, '1D')

    href_obj = {
        "filename": 'sin.tmp',
        "layerType": '1D',
    }
    assert plot.href_obj == href_obj
    assert plot.hrefs == [href_obj]
    assert plot.oldHrefs == [href_obj]


@patch('os.mkdir')
@patch('os.symlink')
def test_show_href_file_absolute_not_already_there(symlink_mock, mkdir_mock):
    path = "~/foo.tmp"
    plot = SigPlot()

    plot.show_href(path, '1D')
    assert mkdir_mock.call_count == 1
    assert mkdir_mock.call_args[0][0] == '.'

    assert symlink_mock.call_count == 1

    local_path = 'foo.tmp'
    fpath = os.path.expanduser(os.path.expandvars(path))
    assert symlink_mock.call_args[0] == (fpath, local_path)


@patch('os.mkdir')
@patch('os.symlink')
def test_show_href_file_relative(symlink_mock, mkdir_mock):
    path = "../foo.tmp"
    plot = SigPlot()

    plot.show_href(path, '1D')
    assert mkdir_mock.call_count == 1
    assert mkdir_mock.call_args[0][0] == '.'

    assert symlink_mock.call_count == 1

    local_path = 'foo.tmp'
    fpath = os.path.expanduser(os.path.expandvars(path))
    assert symlink_mock.call_args[0] == (fpath, local_path)


def test_overlay_href_non_empty_file():
    plot = SigPlot()
    assert plot.inputs == []

    path = "foo.tmp"
    plot.overlay_href(path)
    assert plot.inputs == [path]


def test_overlay_href_non_empty_http():
    plot = SigPlot()
    assert plot.inputs == []

    path = "http://sigplot.lgsinnovations.com/dat/sin.tmp"
    plot.overlay_href(path)

    assert os.path.exists("./sin.tmp")
    assert plot.inputs == ["sin.tmp"]

    os.remove("./sin.tmp")


@patch('jupyter_sigplot.sigplot.SigPlot._show_href_internal')
def test_plot_one_href(show_href_mock):
    href = "foo.tmp"
    plot = SigPlot(href)
    assert plot.inputs == [href]

    plot.plot()
    assert show_href_mock.call_count == 1
    assert show_href_mock.call_args[0] == ({
        "filename": href,
        "layerType": "1D"},)
    assert show_href_mock.call_args[1] == {}
    assert plot.done


@patch('jupyter_sigplot.sigplot.SigPlot._show_href_internal')
def test_plot_two_href(show_href_mock):
    href1 = "foo.tmp"
    href2 = "sin.tmp"
    href = "|".join((href1, href2))
    plot = SigPlot(href)
    assert plot.inputs == [href1, href2]

    plot.plot()
    assert show_href_mock.call_count == 2
    args1, kwargs1 = show_href_mock.call_args_list[0]
    assert args1 == ({"filename": href1, "layerType": "1D"},)
    assert kwargs1 == {}

    args2, kwargs2 = show_href_mock.call_args_list[1]
    assert args2 == ({"filename": href2, "layerType": "1D"},)
    assert kwargs2 == {}
    assert plot.done


@patch('jupyter_sigplot.sigplot.SigPlot._show_href_internal')
@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_mixed(show_array_mock, show_href_mock):
    href = "foo.tmp"
    arr = [1, 2, 3, 4]

    plot = SigPlot(href, arr)
    assert plot.inputs == [href, arr]

    plot.plot()
    assert show_href_mock.call_count == 1
    assert show_array_mock.call_count == 1

    assert show_href_mock.call_args[0] == ({"filename": href,
                                            "layerType": "1D",
                                            },)

    assert show_array_mock.call_args[0] == (arr, )
    assert show_array_mock.call_args[1] == {
        "layer_type": "1D",
        "subsize": None
    }


@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_1d(show_array_mock):
    arr = np.array([1, 2, 3, 4])

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    plot.plot()
    assert show_array_mock.call_count == 1
    print(show_array_mock.call_args)
    assert show_array_mock.call_args[0] == (arr.tolist(), )
    assert show_array_mock.call_args[1] == {
        "layer_type": "1D",
        "subsize": None
    }


@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_2d_no_subsize(show_array_mock):
    arr = [[1, 2, 3, 4], [5, 6, 7, 8]]

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    plot.plot(layer_type="2D")
    assert show_array_mock.call_count == 1
    assert show_array_mock.call_args[0] == (np.array(arr).flatten().tolist(), )
    assert show_array_mock.call_args[1] == {
        "layer_type": "2D",
        "subsize": len(arr[0])
    }


@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_2d_with_subsize(show_array_mock):
    arr = [[1, 2, 3, 4], [5, 6, 7, 8]]

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    subsize = len(arr[0])
    plot.plot(layer_type="2D", subsize=subsize)
    assert show_array_mock.call_count == 1
    assert show_array_mock.call_args[0] == (np.array(arr).flatten().tolist(), )
    assert show_array_mock.call_args[1] == {
        "layer_type": "2D",
        "subsize": subsize
    }


@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_3d(show_array_mock):
    arr = [[[1], [2], [3], [4]], [[5], [6], [7], [8]]]

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    subsize = len(arr[0])
    with pytest.raises(ValueError):
        plot.plot(layer_type="2D", subsize=subsize)


@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_expected_2d(show_array_mock):
    arr = [1, 2, 3, 4]

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    with pytest.raises(ValueError):
        plot.plot(layer_type="2D")


@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_expected_2d_with_subsize(show_array_mock):
    arr = [1, 2, 3, 4]

    subsize = 2

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    plot.plot(layer_type="2D", subsize=subsize)
    assert show_array_mock.call_count == 1
    assert show_array_mock.call_args[0] == (np.array(arr).flatten().tolist(), )
    assert show_array_mock.call_args[1] == {
        "layer_type": "2D",
        "subsize": subsize
    }


def test_overlay_file_non_empty():
    plot = SigPlot()
    assert plot.inputs == []

    path = "foo.tmp"
    plot.overlay_file(path)
    assert plot.inputs == [path]


def test_overlay_file_bad_type():
    plot = SigPlot()
    assert plot.inputs == []

    path = 3
    with pytest.raises(TypeError):
        plot.overlay_file(path)


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
        unravel_path_mock.assert_called_once_with(fname, resolvers)


def test_instance_level_resolver():
    from jupyter_sigplot.sigplot import SigPlot

    def to_foo(s):
        return 'foo'

    # If a single path resolver makes it all the way through the prepare step,
    # we assume that other tests ensure more complicated cases do, too.

    # Resolver specified in constructor
    p = SigPlot(path_resolvers=[to_foo])
    p.overlay_file('baz')
    assert(p.inputs == ['foo'])

    p = SigPlot('bar', path_resolvers=[to_foo])
    assert(p.path_resolvers == [to_foo])
    assert(p.inputs == ['foo'])

    p = SigPlot('bar|baz', path_resolvers=[to_foo])
    assert(p.inputs == ['foo', 'foo'])

    # Resolver specified after construction
    p = SigPlot()
    p.path_resolvers = [to_foo]
    p.overlay_href('quux')
    assert(p.path_resolvers == [to_foo])
    assert(p.inputs == ['foo'])


def test_class_level_resolver():
    from jupyter_sigplot.sigplot import SigPlot

    def to_foo(s):
        return 'foo'

    SigPlot.path_resolvers = [to_foo]

    # Resolver applied in constructor
    p = SigPlot('bar.tmp')
    assert(p.path_resolvers == [to_foo])
    assert(p.inputs == ['foo'])

    # Resolver applied post constructor
    p = SigPlot()
    p.overlay_href('baz|quux.mat')
    assert(p.inputs == ['foo', 'foo'])


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
    _prepare_href_input('', local_dir)
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
        local_dir)
    prepare_file_input_mock.assert_not_called()

    # file and url
    reset()
    _prepare_href_input('foo.tmp|https://www.example.com/bar.tmp', local_dir)
    prepare_http_input_mock.assert_called_once_with(
        'https://www.example.com/bar.tmp',
        local_dir)
    prepare_file_input_mock.assert_called_once_with('foo.tmp', local_dir, None)

    # order independence
    reset()
    _prepare_href_input('https://www.example.com/bar.tmp|foo.tmp', local_dir)
    prepare_http_input_mock.assert_called_once_with(
        'https://www.example.com/bar.tmp',
        local_dir)
    prepare_file_input_mock.assert_called_once_with('foo.tmp', local_dir, None)

    # multiple of each
    reset()
    _prepare_href_input(
        'https://www.example.com/bar.tmp| foo.tmp|baz.tmp|http://www.example.com/quux.tmp  | xyzzy.prm',  # noqa: E501
        local_dir)
    assert prepare_http_input_mock.call_count == 2
    assert prepare_file_input_mock.call_count == 3
