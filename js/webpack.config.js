const fs = require('fs-extra');
const path = require('path');
const version = require('./package.json').version;

/**
 * Custom webpack rules are generally the same for all webpack bundles, hence
 * stored in a separate local variable.
 */
const rules = [
  {test: /\.css$/, use: ["style-loader", "css-loader"]},
];

// The static file directory
const staticDir = path.resolve(__dirname, '..', 'jupyter_sigplot', 'static');

// Copy the package.json to static so we can inspect its version.
fs.copySync('./package.json', path.join(staticDir, 'package.json'))

const externals = ['@jupyter-widgets/base'];

module.exports = [
  /**
   * Notebook extension
   *
   * This bundle only contains the part of the JavaScript that is run on
   * load of the notebook. This section generally only performs
   * some configuration for requirejs, and provides the legacy
   * `load_ipython_extension` function which is required for any notebook
   * extension.
   */
  {
    entry: './src/nb_extension.js',
    output: {
      filename: 'nb_extension.js',
      path: staticDir,
      libraryTarget: 'amd'
    }
  },

  /**
   * Bundle for the notebook containing the custom widget views and models
   *
   * This bundle contains the implementation for the custom widget views and
   * custom widget.
   *
   * Note: It must be an 'amd' module.
   */
  {
    entry: './src/nb_index.js',
    output: {
      filename: 'index.js',
      path: staticDir,
      libraryTarget: 'amd'
    },
    devtool: 'source-map',
    module: {
      rules: rules
    },
    externals: externals,
  },

  /**
   * Embeddable jupyter_sigplot bundle
   *
   * This bundle is generally almost identical to the notebook bundle
   * containing the custom widget views and models.
   *
   * The only difference is in the configuration of the webpack public path
   * for the static assets.
   *
   * It will be automatically distributed by unpkg to work with the static
   * widget embedder.
   *
   * The target bundle is always `dist/index.js`, which is the path required
   * by the custom widget embedder.
   */
  {
    entry: './src/index.js',
    output: {
      filename: 'index.js',
      path: path.resolve(__dirname, 'dist'),
      libraryTarget: 'amd',
      publicPath: 'https://unpkg.com/jupyter_sigplot@' + version + '/dist/'
    },
    devtool: 'source-map',
    module: {
      rules: rules
    },
    externals: externals,
  }
];
