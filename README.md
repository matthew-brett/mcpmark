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
  notebook, run `mcp-check-one <component_name>`.
* `mcp-prepare-components`.
* Develop tests for each component in `model` directory.
* `mcp-cp-models`
* Per notebook / component:
    * Develop tests in `model` directory.
    * Copy tests etc into components directory with `mcp-cp-models`
    * `mcp-find-duplicates` to analyze duplicates, write summary into some
      file, say `report.md`.
    * Check notebook execution with `mcp-run-notebooks <path_to_notebooks>`
    * Move any broken notebooks to `broken` directory, and mark in
      `broken.csv` file.
    * `mcp-extract-manual`. Edit notebooks where manual component not found.
    * Mark generated manual file in `<component>/marking/*_report.md`.
    * Check manual scoring with something like `mcp-parse-manual-scores
      components/lymphoma/dunleavy_plausible_report.md`
    * `mcp-grade-nbs.py <component_name>`.
    * Review `<component>/marking/autograde.md`.
    * Update any manual fixes with `#M: ` notation to add / subtract marks.
    * Final run of `mcp-grade-nbs`
    * `mcp-grade-component`.

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
