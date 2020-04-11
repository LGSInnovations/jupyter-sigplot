import { DOMWidgetModel, DOMWidgetView } from '@jupyter-widgets/base';
import { Plot } from 'sigplot';
import { version } from '../package';

export class SigPlotModel extends DOMWidgetModel {
    defaults() {
        return {
            ...super.defaults(),
            _model_name: 'SigPlotModel',
            _view_name: 'SigPlotView',
            _model_module: 'jupyter_sigplot',
            _view_module: 'jupyter_sigplot',
            _model_module_version: version,
            _view_module_version: version,
            command_and_arguments: [],
            progress: 0,
            done: false,
        };
    }

    initialize(attributes, options) {
        super.initialize(attributes, options);

        this.on(
            'change:command_and_arguments',
            this.handle_command_args_change.bind(this)
        );
        this.on('change:progress', this.handle_progress_change.bind(this));
        this.on('change:done', this.handle_done.bind(this));
    }

    handle_command_args_change() {
        const prev_cmd_and_args = this.previous('command_and_arguments');
        const cmd_and_args = this.get('command_and_arguments');
        this._for_each_view((view) => {
            view.handle_command_args_change(prev_cmd_and_args, cmd_and_args);
        });
    }

    handle_progress_change() {
        console.log('Progress change');
    }

    handle_done() {
        console.log('Handle done...');
    }

    /**
     * Wrapper around looping over associated views
     *
     * @param {function} callback
     * @private
     */
    _for_each_view(callback) {
        for (const view_id in this.views) {
            this.views[view_id].then(function (view) {
                callback(view);
            });
        }
    }

    remove() {
        console.log('Removing');
    }
}

export class SigPlotView extends DOMWidgetView {
    render() {
        // Instantiate a new plot and attach to the element provided in `this.el`
        this.plot = new Plot(this.el, this.model.get('plot_options'));

        // Wait for element to be added to the DOM
        const self = this;
        window.setTimeout(function () {
            self.$el.css('width', '100%');
            self.$el.css('height', '350px');
            self.plot.checkresize();
        }, 0);
    }

    /**
     * Handles new `sigplot.Plot` commands as a proxy from server Python
     * to client JS.
     *
     * @param {object} prev_cmd_and_args    The previously sent command/args combo
     * @param {string} prev_cmd_and_args.command    Command from {overlay_*, change_settings}
     * @param {array} prev_cmd_and_args.arguments   Arguments for respective sigplot.Plot functions
     * @param new_cmd_and_args {object}     The new command/arg combo
     * @param {string} new_cmd_and_args.command     Command from {overlay_*, change_settings}
     * @param {array} new_cmd_and_args.arguments    Arguments for respective sigplot.Plot functions
     */
    handle_command_args_change(prev_cmd_and_args, new_cmd_and_args) {
        const { command: new_command, arguments: new_args } = new_cmd_and_args;

        // Check that the commands and arguments are different
        if (prev_cmd_and_args === new_cmd_and_args) {
            return;
        }

        // Since we're sending binary for `overlay_array`,
        // need to convert it to a Float32Array so we can plot it.
        if (new_command === 'overlay_array') {
            new_args[0] = new Float32Array(new_args[0].buffer);
        }

        // Call `new_command` providing `new_args`
        this.plot[new_command].apply(this.plot, new_args);

        // Save a screenshot of the current plot
        const image_data = this.plot._Mx.active_canvas.toDataURL('image/png');
        const img = document.createElement('img');
        img.src = image_data;

        // Replace existing image with new image
        const childImg = this.el.querySelector('img');
        if (childImg) {
            this.el.removeChild(childImg);
        }
        this.el.appendChild(img);
    }

    /**
     * Handles remote resource downloading on the server
     *
     * @param {number} old_progress     The previous progress update
     * @param {number} new_progress     The current progress update
     */
    handle_progress_change(old_progress, new_progress) {
        // Check that this is new progress
        if (old_progress === new_progress) {
            return;
        }

        // If it's new progress, make it known
        // For now, just debug log it to console...
        console.debug(new_progress);
    }

    /**
     * Handles plot closing
     */
    handle_done() {
        console.log('Done!');
    }

    remove() {}
}
