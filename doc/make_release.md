# Making a release

Update the version number in `src/mcpmark/__init__.py`.

```bash
pip install build twine
```

For reassurance:

```bash
git clean -fxd
```

Build the Sdist:

```bash
python -m build --sdist
```

Upload to PyPI:

```bash
twine upload dist/mcpmark*.tar.gz
```

## Documentation

```{python}
make gh-pages
```
