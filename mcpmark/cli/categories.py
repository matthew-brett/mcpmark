#!/usr/bin/env python
""" Add or analyze mark categories for freeform notebooks.
"""

from pathlib import Path
import re

from argparse import ArgumentParser, RawDescriptionHelpFormatter

import jupytext
import pandas as pd

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


def get_marks(nb_fnames, categories, login_col):
    marks_d = {}
    for nb_fname in nb_fnames:
        login, marks = marks_from_nb(nb_fname)
        if not set(marks) == set(categories):
            cats = '; '.join(categories)
            raise ValueError(
                f'Could not find marks for exactly {cats} in {nb_fname}')
        marks_d[login] = marks
    df = pd.DataFrame(marks_d).T.astype(float)
    df = df.sort_index()
    df.columns = pd.MultiIndex.from_tuples([('Manual', n) for n in df])
    df.index.name = (login_col, '')
    df[('Total', '')] = df.mean(axis=1)
    return df.reset_index()


def marks_from_nb(nb_fname):
    nb_path = Path(nb_fname)
    assert nb_path.suffix == '.Rmd'
    nb = jupytext.read(nb_fname)
    try:
        return nb_path.stem, marks_from_cell(nb.cells[-1])
    except ValueError as e:
        raise RuntimeError(f'{str(e)}: - check {nb_fname}')


RE_MARK = re.compile("^\* ([A-Z]\w+)\s*:\s*(\d+)$",
                     flags=re.M)


def marks_from_cell(cell):
    assert cell['cell_type'] == 'markdown'
    contents = cell['source']
    lines = [L.strip() for L in contents.splitlines() if L.strip()]
    contents = '\n'.join(lines).strip()
    if not contents.startswith('## Marks'):
        raise ValueError('Contents does not contain "## Marks"')
    return {k.lower(): v for k, v in RE_MARK.findall(contents)}


def get_parser(description):
    parser = ArgumentParser(description=description,
                            formatter_class=RawDescriptionHelpFormatter)
    return parser


class ArgProcessor:

    def __init__(self, description):
        self.args, self.config = get_component_config(get_parser(description))
        self.component_name = self.args.component
        self.component_info = self.config['components'][self.component_name]
        self.nb_path = component_path(self.config, self.component_name)
        self.categories = self.component_info.get('categories')
        if self.categories is None:
            raise RuntimeError(
                f'No categories for component {self.component_name}')
        self.nb_fnames = get_notebooks(self.nb_path, ['.rmd'], first_only=True)
        if len(self.nb_fnames) == 0:
            raise RuntimeError(f'No notebooks found in path "{self.nb_path}" '
                            f'with extension .rmd')


def add_categories():
    argp = ArgProcessor(
        'Add cell with mark category template to end of component notebooks')
    for nb_fname in argp.nb_fnames:
        write_categories(nb_fname, argp.categories)


def ana_categories():
    argp = ArgProcessor(
        'Analyze mark categories at end of component notebooks')
    login_col = argp.config['student_id_col']
    marks = get_marks(argp.nb_fnames, argp.categories, login_col)
    out_fname = Path(argp.nb_path) / 'marking' / 'component.csv'
    marks.to_csv(out_fname, index=None)
