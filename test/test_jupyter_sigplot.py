#!/usr/bin/env python
import os

import pytest
from mock import patch
import numpy as np
from IPython.testing.globalipapp import get_ipython

ip = get_ipython()

from jupyter_sigplot.sigplot import SigPlot  # noqa: E402


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
        "filename": path,
        "layerType": layer_type,
    }
    assert plot.href_obj == href_obj
    assert plot.hrefs == [href_obj]
    assert plot.oldHrefs == [href_obj]


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
    assert mkdir_mock.call_args[0] == ('data', )

    assert symlink_mock.call_count == 1

    local_path = os.path.join(os.getcwd(), 'data', 'foo.tmp')
    fpath = os.path.expanduser(os.path.expandvars(path))
    assert symlink_mock.call_args[0] == (fpath, local_path)


@patch('os.mkdir')
@patch('os.symlink')
def test_show_href_file_relative(symlink_mock, mkdir_mock):
    path = "../foo.tmp"
    plot = SigPlot()

    plot.show_href(path, '1D')
    assert mkdir_mock.call_count == 1
    assert mkdir_mock.call_args[0] == ('data', )

    assert symlink_mock.call_count == 1

    local_path = os.path.join(os.getcwd(), 'data', 'foo.tmp')
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


@patch('jupyter_sigplot.sigplot.SigPlot.show_href')
def test_plot_one_href(show_href_mock):
    href = "foo.tmp"
    plot = SigPlot(href)
    assert plot.inputs == [href]

    plot.plot()
    assert show_href_mock.call_count == 1
    assert show_href_mock.call_args[0] == (href, "1D")
    assert show_href_mock.call_args[1] == {}
    assert plot.done


@patch('jupyter_sigplot.sigplot.SigPlot.show_href')
def test_plot_two_href(show_href_mock):
    href1 = "foo.tmp"
    href2 = "sin.tmp"
    href = "|".join((href1, href2))
    plot = SigPlot(href)
    assert plot.inputs == [href]

    plot.plot()
    assert show_href_mock.call_count == 2
    args1, kwargs1 = show_href_mock.call_args_list[0]
    assert args1 == (href1, "1D")
    assert kwargs1 == {}

    args2, kwargs2 = show_href_mock.call_args_list[1]
    assert args2 == (href2, "1D")
    assert kwargs2 == {}
    assert plot.done


@patch('jupyter_sigplot.sigplot.SigPlot.show_href')
@patch('jupyter_sigplot.sigplot.SigPlot.show_array')
def test_plot_mixed(show_array_mock, show_href_mock):
    href = "foo.tmp"
    arr = [1, 2, 3, 4]

    plot = SigPlot(href, arr)
    assert plot.inputs == [href, arr]

    plot.plot()
    assert show_href_mock.call_count == 1
    assert show_array_mock.call_count == 1

    assert show_href_mock.call_args[0] == (href, "1D")

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
def test_plot_expected_2d(show_array_mock):
    arr = [1, 2, 3, 4]
    subsize = 2

    plot = SigPlot(arr)
    assert plot.inputs == [arr]

    with pytest.raises(ValueError):
        plot.plot(layer_type="2D")


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
