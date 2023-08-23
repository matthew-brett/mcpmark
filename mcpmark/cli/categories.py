#!/usr/bin/env python
""" Add or analyze mark categories for freeform notebooks.
"""

from pathlib import Path

from argparse import ArgumentParser, RawDescriptionHelpFormatter

from ..mcputils import (get_notebooks, component_path,
                        get_component_config)


def write_categories(nb_fname, categories):
    nb_path = Path(nb_fname)
    contents = nb_path.read_text()
    cats = '\n'.join([f'* {c.capitalize()}: ' for c in categories])
    nb_path.write_text(f"""{contents}

## Marks

{cats}
""")


def get_parser(description):
    parser = ArgumentParser(description=description,
                            formatter_class=RawDescriptionHelpFormatter)
    return parser


def proc_args(description):
    args, config = get_component_config(get_parser(description))
    nb_path = component_path(config, args.component)
    categories = config['components'][args.component].get('categories')
    if categories is None:
        raise RuntimeError(f'No categories for component {args.component}')
    nb_fnames = get_notebooks(nb_path, ['.rmd'], first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{nb_path}" '
                           f'with extension .rmd')
    return nb_fnames, categories


def add_categories():
    nb_fnames, categories = proc_args(
        description='Add cell with mark category template to end of '
        'component notebooks')
    for nb_fname in nb_fnames:
        write_categories(nb_fname, categories)
