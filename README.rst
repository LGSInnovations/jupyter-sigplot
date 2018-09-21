jupyter-sigplot
===============================
|Pip|_ |Prs|_

.. |Pip| image:: https://img.shields.io/pypi/v/nine.svg
.. _Pip: https://test.pypi.org/project/jupyter-sigplot/

.. |Prs| image:: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
.. _Prs: .github/CONTRIBUTING.md#pull-requests


A Custom Jupyter Widget Library for the SigPlot plotting library

Installation
------------

To install use ``pip``::

    $ pip install jupyter-sigplot
    $ jupyter nbextension enable --py --sys-prefix jupyter-sigplot


For a development installation (requires ``npm``)::

    $ git clone https://github.com/LGSInnovations/jupyter-sigplot.git
    $ cd jupyter-sigplot
    $ pip install -e .
    $ jupyter nbextension install --py --symlink --sys-prefix jupyter-sigplot
    $ jupyter nbextension enable --py --sys-prefix jupyter-sigplot
