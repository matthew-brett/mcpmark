#!/usr/bin/env python
""" Calculate grades for a component.

A student's grade comes from:

* Grades from autograding PLUS
* Corrections from #M: notations PLUS
* Grades from plots (if present) PLUS
* Grades from manual answer grading.
"""

from pathlib import Path
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from collections import Counter

import numpy as np
import pandas as pd

from ..mcputils import (get_component_config, read_manual, get_notebooks, nbs2markups,
                        get_plot_scores, component_path, MCPError)


def add_multi(df, heading):
    if not len(df):
        return df
    df = df.copy()
    cols = [(heading, c) for c in df]
    df.columns = pd.MultiIndex.from_tuples(cols)
    return df


def read_grades(fname, stid_col, total_col):
    if not op.isfile(fname):
        return pd.DataFrame()
    df = pd.read_csv(fname)
    return dict(zip(df[stid_col], df[total_col]))


def read_plots(comp_path, plot_qs):
    splot_qs = set(plot_qs)
    plot_fname = comp_path / 'marking' / 'plot_nb.ipynb'
    if not plot_fname.is_file():
        assert len(splot_qs) == 0
        return pd.DataFrame()
    scores = get_plot_scores(plot_fname)
    for login, vs in scores.items():
        missing = splot_qs.difference(vs)
        if missing:
            raise MCPError(
                f'Plot scores missing for {login}; {", ".join(missing)}')
        assert splot_qs == set(vs)
    return pd.DataFrame(scores).T


def read_manuals(comp_path, manual_qs):
    mark_path = comp_path / 'marking'
    expected_manuals = [mark_path / f'{q}_report.md'
                        for q in manual_qs]
    actual_manuals = mark_path.glob('*_report.md')
    missing = set(expected_manuals).difference(actual_manuals)
    if missing:
        smissing = ', '.join(sorted(missing))
        raise MCPError(f'Expected manual grading {smissing}')
    scores = [read_manual(fn)[1] for fn in expected_manuals]
    out = pd.DataFrame(scores).T
    out.columns = manual_qs
    return out


def read_autos(comp_path, stid_col):
    # Read autos file
    fname = comp_path / 'marking' / 'autograde.csv'
    return (pd.read_csv(fname).set_index(stid_col, drop=True)
            .drop(columns='Total'))


def read_annotations(comp_path):
    # Add annotation marks
    notes = Counter()
    nb_fnames = get_notebooks(comp_path, first_only=True)
    for login, mark in nbs2markups(nb_fnames).items():
        notes[login] += mark
    if not notes:
        return pd.DataFrame()
    return pd.DataFrame(pd.Series(notes, name='annotations'))


def grade_component(config, component):
    comp_path = Path(component_path(config, component))
    stid_col = config['student_id_col']
    autos = add_multi(read_autos(comp_path, stid_col), 'auto')
    annotations = add_multi(read_annotations(comp_path), 'annotation')
    plot_qs = config['components'][component].get('plot_qs', [])
    plots = add_multi(read_plots(comp_path, plot_qs), 'plots')
    manual_qs = config['components'][component].get('manual_qs', [])
    manuals = add_multi(read_manuals(comp_path, manual_qs), 'manual')
    start = autos.copy()
    for df in [plots, manuals]:
        if len(df):
            start = start.join(df, how='outer')
    assert not np.any(np.isnan(start))
    # THere may be no annotations
    start = start.join(annotations, how='left')
    start = start.fillna(0)
    return start


def write_component_csv(config, component, marks):
    marks['Total'] = marks.sum(axis=1)
    marks = marks.reset_index()
    out_path = Path(component_path(config, component))
    out_fname = out_path / 'marking' / 'component.csv'
    marks.to_csv(out_fname, index=None)
    return out_fname


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    return parser


def main():
    args, config = get_component_config(get_parser())
    grades = grade_component(config, args.component)
    out_csv = write_component_csv(config, args.component, grades)
    print(pd.read_csv(out_csv)['Total'].describe())


if __name__ == '__main__':
    main()
