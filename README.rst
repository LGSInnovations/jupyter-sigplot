jupyter-sigplot
===============================
|Pip|_ |Prs|_ |Apache2|_

.. |Pip| image:: https://img.shields.io/badge/pypi-v0.1.0-blue.svg
.. _Pip: https://pypi.org/project/jupyter-sigplot/

.. |Prs| image:: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
.. _Prs: .github/CONTRIBUTING.md#pull-requests

.. |Apache2| image:: https://img.shields.io/badge/license-Apache%202.0-orange.svg
.. _Apache2: https://opensource.org/licenses/Apache-2.0

A Custom Jupyter Widget Library for the SigPlot plotting library

.. image:: docs/jupyter_sigplot_example.gif

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
