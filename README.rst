jupyter-sigplot
===============================
|Pip|_ |Prs|_ |Apache2|_ |Travis|_ |Binder|_

.. |Pip| image:: https://badge.fury.io/py/jupyter-sigplot.svg
.. _Pip: https://badge.fury.io/py/jupyter-sigplot

.. |Prs| image:: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
.. _Prs: .github/CONTRIBUTING.md#pull-requests

.. |Apache2| image:: https://img.shields.io/badge/license-Apache%202.0-orange.svg
.. _Apache2: https://opensource.org/licenses/Apache-2.0

.. |Travis| image:: https://travis-ci.org/LGSInnovations/jupyter-sigplot.svg?branch=master
.. _Travis: https://travis-ci.org/LGSInnovations/jupyter-sigplot

.. |Binder| image:: https://mybinder.org/badge.svg
.. _Binder: https://mybinder.org/v2/gh/LGSInnovations/jupyter-sigplot/master?filepath=example%2FJupyterSigplot.ipynb

A Custom Jupyter Widget Library for the SigPlot plotting library

.. image:: https://github.com/LGSInnovations/jupyter-sigplot/blob/master/docs/jupyter_sigplot_example.gif?raw=true

Installation
------------

To install use ``pip``::

    $ pip install jupyter-sigplot
    $ jupyter nbextension enable --py --sys-prefix jupyter_sigplot


For a development installation (requires ``npm``)::

    $ git clone https://github.com/LGSInnovations/jupyter-sigplot.git
    $ cd jupyter-sigplot
    $ python setup.py install
    $ jupyter nbextension install --py --symlink --sys-prefix jupyter_sigplot
    $ jupyter nbextension enable --py --sys-prefix jupyter_sigplot
