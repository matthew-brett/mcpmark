# (Multiple) component marking

Some tools I use when marking homework with with single or multiple Jupyter
notebook components.

The notebooks may have questions for manual marking, and plots for marking.

They assume some Canvas](https://www.instructure.com/canvas) conventions of
naming files, and grade output CSV format.

The tools consist primarily command line utilities, with some supporting code
in a utility library.

## Quickstart

### For single component submission:

```
COMPONENTS_DIR=components
mcp-check-unpack
mcp-prepare-components
mcp-find-duplicates $COMPONENTS_DIR/*/*.Rmd
mcp-cp-models
mcp-extract-manual
rnbg-allow-raise $COMPONENTS_DIR/*/*.Rmd --show-error
mcp-extract-plots
mcp-grade-nbs
# Review `<component>/marking/autograde.md`.
# Rerun after any edits.
mcp-grade-nbs
mcp-grade-component
mcp-scale-combine
```

### For multiple component submission:

```
COMPONENTS_DIR=components
mcp-check-unpack
mcp-prepare-components
mcp-find-duplicates $COMPONENTS_DIR/*/*.Rmd
mcp-cp-models
# For each component
    COMPONENT=my_component
    mcp-allow-raise $COMPONENT
    mcp-grade-nbs $COMPONENT
    # Review `$COMPONENTS_DIR/$COMPONENT/marking/autograde.md`.
    # Rerun after any edits.
    mcp-grade-nbs $COMPONENT
    mcp-extract-manual $COMPONENT
    # Mark manual questions in $COMPONENT/marking/*_report.md files
    mcp-extract-plots $COMPONENT
    # Mark plot questions in $COMPONENT/marking/plot_nb.ipynb file
    mcp-grade-component $COMPONENT
# Finally
mcp-scale-combine
```

## Getting set up

Make a virtual environment / Conda environment for running the marking code, and set yourself up in that environment:

```
python -m virtualenv ~/envs/marking-env
source ~/envs/marking-env/bin/activate
```

or

```
conda create --name marking-env
conda activate marking-env
conda install pip
```

To install locally from the repository, you will need
[flit](https://pypi.org/project/flit):

```
pip install flit
```

Then install MCPMark with its dependencies:

```
cd mcpmark  # Directory containing this README
flit install -s
```

Test all is working as expected with:

```
pip install -r test-requirements.txt
pytest mcpmark
```

## A typical marking run

*   Make sure you have activated the environment above with e.g. `source
    ~/envs/marking-env` or `conda activate marking-env`
* Make a directory for marking, call this `homework1` or similar.
* `cd homework1`
* Download submissions (`.zip` files for multiple notebook submission, `.ipynb`
  files for single notebook submission). Download some directory e.g.
  `submissions` in current directory. There should be one `.zip` file per
  student in the case of multiple notebook submissions, or one `.ipynb` file
  per student in case of single submissions.
* Download Canvas marks CSV file to this (`homework1`) directory.
* Edit `assign_config.yaml` --- see `doc/` for an example.   Use the
  `components` field to name and define components.  Each component corresponds
  to one notebook, so there will be one component for single notebook
  submissions, and multiple component for multiple notebook submissions.
* In what follows below, a "component name" is the name you have given for
  a single notebook assignment in the `assign_config.yaml` file.
* Develop script to identify notebooks by their content - see `doc` for an
  example, and `mcpmark/cli/prepare_components.py` for code using this script.
  This allows Mcpmark to check that a student does have a matching notebook for
  each required component.
* Run `mcp-check-unpack`.  If any errors arise, check and maybe change the
  submission filenames.
* Run `mcp-prepare-components`.  This will check that all the students in the
  relevant student files have got matching notebook submissions for all
  required components.  The error message should tell you what is missing.  If
  you discover that the warning is a false positive, and you were not expecting
  this student to submit (yet), then fill in their ID in the `known_missing`
  list of the `assign_config.yaml` file, to tell Mcpmark not to check their
  submissions.  Then re-run `mcp-prepare-components`, repeating until you get
  no errors.
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
      Consider running this with e.g. `rerun mcp-run-notebooks
      components/pandering` to continuously test notebooks.
    * `mcp-extract-manual <component_name>` (component name optional for single
      component submissions). Edit notebooks where manual component not found.
      Maybe e.g. `rerun mcp-extract-manual pandering`.
    * Mark generated manual file in `<component>/marking/*_report.md`.
    * Check manual scoring with something like `mcp-manual-scores
      components/lymphoma/dunleavy_plausible_report.md`.  Or you can leave
      that until grading the whole component with `mcp-grade-component`.
    * `mcp-extract-plots <component_name>` (component name optional for single
      component submissions).  Edit `marked/plot_nbs.ipynb` to add marks.
    * Run auto-grading with `mcp-grade-nbs <component_name>`
      (`<component_name>`) is optional if a single component.
    * Review `<component>/marking/autograde.md`.
    *   Update any manual fixes with `#M: ` notation to add / subtract marks.
        These are lines in code cells / chunks, of form `#M:
        <score_increment>` -- e.g. `#M: -2.5`.  They reach the final score via
        `mcp-grade-components`.
    * Final run of `mcp-grade-nbs`
    * `mcp-grade-component <component_name>`; (`<component_name>`) is optional
      if a single component.

When done:

* `mcp-scale-combine` to rescale the component marks to their out-of figure
  given in `assign_config.yaml`, and generate the summary `.csv` file.  Do this
  even when there is only one component (in order to do the rescaling).
* `mcp-export-marks` to convert the output of `ncp-rescale-combines` to
  a format for import into Canvas.

## Utilities

* `mcputils` - various utilities for supporting the scripts.
