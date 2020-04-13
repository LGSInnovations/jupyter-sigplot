/*global IPython*/

/**
 * Return the cell and output element which can be found *uniquely* in the notebook.
 *
 * Note: This is a bit hacky, but it is done because the "notebook_saving.Notebook"
 * IPython event is triggered only after the cells have been serialised, which for
 * our purposes (turning an active figure into a static one), is too late.
 *
 * Taken from matplotlib's mpl.js
 *
 * @param {string} html_output
 * @returns {(*|number)[]}
 */
export function find_output_cell(html_output) {
    const cells = IPython.notebook.get_cells();
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        if (cell.cell_type === 'code') {
            for (let j = 0; j < cell.output_area.outputs.length; j++) {
                let data = cell.output_area.outputs[j];
                if (data.data) {
                    // IPython >= 3 moved mimebundle to data attribute of output
                    data = data.data;
                }
                console.log(`cell_index=${i}`);
                console.log(data);
                if (data['text/html'] === html_output) {
                    return [cell, data, j];
                }
            }
        }
    }
}
