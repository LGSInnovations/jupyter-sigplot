'use strict';

var widgets = require('@jupyter-widgets/base');
var sigplot = require('sigplot');
var version = require('../package.json').version;


var SigPlotModel = widgets.DOMWidgetModel.extend({
    defaults: _.extend(_.result(this, 'widgets.DOMWidgetModel.prototype.defaults'), {
        _model_name: 'SigPlotModel',
        _view_name: 'SigPlotView',
        _model_module: 'jupyter_sigplot',
        _view_module: 'jupyter_sigplot',
        _model_module_version: version,
        _view_module_version: version
    })
});

var SigPlotView = widgets.DOMWidgetView.extend({

    /**
     * Instantiates the plot, attaches it to the DOM, and sets up change listeners
     * on the kernel-side (i.e., the model)
     */
    defaults: _.extend(_.result(this, 'widgets.DOMWidgetModel.prototype.defaults'), {
        _model_name: 'SigPlotModel',
        _view_name: 'SigPlotView',
        _model_module: 'jupyter_sigplot',
        _view_module: 'jupyter_sigplot',
        _model_module_version: version,
        _view_module_version: version
    }),

    render: function() {

        // Instantiate a new plot and attach to the element provided in `this.$el[0]`
        this.plot = new sigplot.Plot(this.$el[0], this.model.get('plot_options'));

        // Wait for element to be added to the DOM
        var self = this;
        window.setTimeout(function() {
            self.$el.css('width', '100%');
            self.$el.css('height', '350px');
            self.plot.checkresize()
        }, 0);

        this.listenTo(this.model, 'change:command_and_arguments', this.handle_command_args_change, this);
        this.listenTo(this.model, 'change:progress', this.handle_progress_change, this);
        this.listenTo(this.model, 'change:done', this.handle_done, this);
    },

    /**
     * Handles general calls to the 
     */
    handle_command_args_change: function() {
        var old_command_and_arguments = this.model.previous('command_and_arguments');
        var new_command_and_arguments = this.model.get('command_and_arguments');

        // Check that the arrays are different
        if (old_command_and_arguments === new_command_and_arguments) {
            return;
        } else {
            var command = new_command_and_arguments.command;
            var args = new_command_and_arguments.arguments;

            if (command == 'overlay_array') {
                args[0] = new Float32Array(args[0].buffer)
            }

            // call ``command`` providing ``arguments``
            this.plot[command].apply(this.plot, args);
        }
    },

    /**
     * Handles remote resource downloading on the server
     */
    handle_progress_change: function() {
        var old_progress = this.model.previous('progress');
        var new_progress = this.model.get('progress');

        // Check that this is new progress
        if (old_progress === new_progress) {
            return;
        } else {
            // If it's new progress, make it known
            // For now, just debug log it to console...
            console.debug(new_progress);
        }
    },

    /**
     * Handles plot closing (ideally)
     */
    handle_done: function() {
        if (this.model.get('done')) {
            var plotLocal = this.plot;
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