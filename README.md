# Multiple component marking

Some tools I use when marking homeworks with multiple Jupyter notebook components.

The notebooks may have questions for manual marking, and plots for marking.

They assume some Canvas](https://www.instructure.com/canvas) conventions of naming files, and grade output CSV format.

The tools consist primarily command line utilities, with some supporting code
in a utility library.

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
