var jupyterSigplot = require('./index');
var base = require('@jupyter-widgets/base');

module.exports = {
  id: 'jupyterSigplot',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'jupyterSigplot',
          version: jupyterSigplot.version,
          exports: jupyterSigplot
      });
  },
  autoStart: true
};

