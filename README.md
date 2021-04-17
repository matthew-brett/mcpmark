# Multiple component marking

Some tools I use when marking homework with multiple Jupyter notebook
components.

The notebooks may have questions for manual marking, and plots for marking.

They assume some Canvas](https://www.instructure.com/canvas) conventions of naming files, and grade output CSV format.

The tools consist primarily command line utilities, with some supporting code
in a utility library.

## A typical marking run

* Download submissions to some directory
* Download Canvas marks CSV  file to some directory, maybe this one.
* Edit `assign_config.yaml` --- see `docs` for an example.
* Develop script to identify notebooks by their content - see `doc` for an
  example, and `mcpmark/cli/prepare_components.py` for code using this script.
* If you have multiple components, each in a zip file, run:
  `mcp-check-unpack`.  If you have one component, with corresponding single
  notebook, run `mcp-check-one <component_name>`, and make sure you have set
  the `assignment_nb_path` in `assign_config.yaml`.
* `mcp-prepare-components`.
* Develop tests for each component in `models` directory.  Check the marks
  with `grade_oknb.py` in textbook `_scripts` directory.
* `mcp-cp-models`
* In what follows, you can generally omit the `<component_name>` argument when
  you only have one component.
* For items below, assume script `rerun` is on the path and has contents
  `while true; do $@; done`
* Per notebook / component:
    * Develop tests in `model/<component_name>/tests` directory.
    * Test tests with `grade_oknb.py`.
    * Copy tests etc into components directory with `mcp-cp-models`
    * e.g. `mcp-find-duplicates components/my_component/*.Rmd` to analyze
      duplicates, write summary into some file, say `report.md`.
    * Check notebook execution with `mcp-run-notebooks <path_to_notebooks>`.
      Consider running this with e.g. `rerun do mcp-run-notebooks
      components/pandering` to continuously test notebooks.
    * Move any irreparable notebooks to `broken` directory, and mark in
      `broken.csv` file.
    * `mcp-extract-manual <component_name>`. Edit notebooks where manual
      component not found.  Maybe e.g. `rerun mcp-extract-manual pandering`.
    * Mark generated manual file in `<component>/marking/*_report.md`.
    * Check manual scoring with something like `mcp-manual-scores
      components/lymphoma/dunleavy_plausible_report.md`.  Or you can leave
      that until grading the whole component with `mcp-grade-component`.
    * `mcp-extract-plots <component_name>` - edited `marked/plot_nbs.ipynb` to
      add marks.
    * Run auto-grading with `mcp-grade-nbs.py <component_name>`.
    * Review `<component>/marking/autograde.md`.
    * Update any manual fixes with `#M: ` notation to add / subtract marks.
      These are lines in code cells / chunks, of form `#M: <score_increment>`
      -- e.g. `#M: -2.5`.  They reach the final score via
      `mcp-grade-components`.
    * Final run of `mcp-grade-nbs`
    * `mcp-grade-component <component_name>`.

When done:

* `mcp-combine-components` to generate the summary `.csv` file.  Do this even
  when there is only one component.
* `mcp-export-marks`

## Utilities

* `mcputils` - various utilities for supporting the scripts.

## Installation, development

Install from pip, usually:

```
pip install mcpmark
```

To install locally from the repository, you will need
[flit](https://pypi.org/project/flit).

```
flit install --user
```

For development I use:

```
flit install --user -s
```

Test with:

```
pip install -r test-requirements.txt
pytest mcpmark
```
