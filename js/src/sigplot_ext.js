var widgets = require('@jupyter-widgets/base');
var sigplot= require("sigplot")


var SigPlotModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(_.result(this, 'widgets.DOMWidgetModel.prototype.defaults'), {
        _model_name : 'SigPlotModel',
        _view_name : 'SigPlotView',
        _model_module : 'jupyter_sigplot',
        _view_module : 'jupyter_sigplot',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0'
    })
});

var SigPlotView = widgets.DOMWidgetView.extend({

    /**
     * Instantiates the plot, attaches it to the DOM, and sets up change listeners
     * on the kernel-side (i.e., the model)
     */
    defaults: _.extend(_.result(this, 'widgets.DOMWidgetModel.prototype.defaults'), {
        _model_name : 'SigPlotModel',
        _view_name : 'SigPlotView',
        _model_module : 'jupyter_sigplot',
        _view_module : 'jupyter_sigplot',
        _model_module_version : '0.1.0',
        _view_module_version : '0.1.0'
    }),
    render: function() {

        // Instantiate a new plot and attach to the element provided in `this.$el[0]`
        this.plot = new sigplot.Plot(this.$el[0], this.model.get('options'));

        // Wait for element to be added to the DOM
        var self = this;
        window.setTimeout(function() {
          self.$el.css('width', '100%');
          self.$el.css('height', '350px');
          self.plot.checkresize()
        }, 0);
        
        var i;
        for (i =0; i<this.model.get('oldArrays').length; i++){
            this.array_obj = this.model.get('oldArrays')[i];
            this._plot_from_array();
        }
        for (i =0; i<this.model.get('oldHrefs').length; i++){
            this.href_obj=this.model.get('oldHrefs')[i];
            this._plot_from_file();
        }

        this.listenTo(this.model, 'change:options', this._change_options, this);
        this.listenTo(this.model, 'change:array_obj', this._plot_from_array, this);
        this.listenTo(this.model, 'change:href_obj', this._plot_from_file, this);
        this.listenTo(this.model, 'change:done', this._done, this);
    },

    /**
     * Handles change in options (change_settings)
     */
    _change_options: function() {
      var old_options = this.model.previous('options');
      var new_options = this.model.get('options');
      if (old_options === new_options) {
        return;
      } else {
        this.plot.change_settings(new_options);   
      }
    },
    
    /**
     * Handles plotting both 1-D (xplot) and 2-D arrays (xraster)
     */
    _plot_from_array: function() {
      var old_array_obj = this.model.previous('array_obj');
      var array_obj = this.model.get('array_obj');
      this.plotted=true;
      // Check that the arrays are different
      if (old_array_obj === array_obj) {
        return;
      } else {
        this.plot.overlay_array(
          array_obj.data,
          array_obj.overrides,
          {layerType: array_obj.layerType});
      }
    },

    /**
     * Plots a file (either local or via HTTP/HTTPS)
     */
    _plot_from_file: function() {
      var old_href_obj = this.model.previous('href_obj');
      var href_obj = this.model.get('href_obj');
      this.plotted=true;
      // Check that this is a new file
      if (old_href_obj === href_obj) {
        return;
      } else {
        var url = href_obj.filename;
        if (!url.startsWith("http")) {
          // Server-side widget gave us a name like data/foo.tmp;
          // Jupyter will serve this for us at the `files` route
          url = window.location.origin + "/files/" + url;
        }
        this.plot.overlay_href(
          url,
          null,
          {layerType: href_obj.layerType}
        );
      }
    },

    _done: function() {
      if (this.model.get('done')) {
        var plotLocal=this.plot;
        window.setTimeout(function() {
          var img = plotLocal._Mx.active_canvas.toDataURL("image/png");
          var link = document.createElement("a");
          link.href = img;
          link.display = img;
          document.body.appendChild(link);
          document.body.appendChild(link);
          //document.write('<img src="' + img +'"/>');
          document.body.removeChild(link);
        }, 2000);
      }
    }
});


module.exports = {
    SigPlotModel: SigPlotModel,
    SigPlotView: SigPlotView
};
