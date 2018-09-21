var jupyter_sigplot = require('./index');
var base = require('@jupyter-widgets/base');

module.exports = {
  id: 'jupyter_sigplot',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'jupyter_sigplot',
          version: jupyter_sigplot.version,
          exports: jupyter_sigplot
      });
  },
  autoStart: true
};

