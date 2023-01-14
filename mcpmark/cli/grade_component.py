#!/usr/bin/env python
""" Calculate grades for a component.

A student's grade comes from:

* Grades from autograding PLUS
* Corrections from #M: notations PLUS
* Grades from plots (if present) PLUS
* Grades from manual answer grading.
"""

import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from glob import glob

import pandas as pd

from ..mcputils import (get_component_config, read_manual, get_notebooks, nbs2markups,
                        get_plot_scores, component_path, MCPError)


def read_grades(fname, stid_col, total_col):
    if not op.isfile(fname):
        return {}
    df = pd.read_csv(fname)
    return dict(zip(df[stid_col], df[total_col]))


def read_plots(config, component):
    splot_qs = set(config['components'][component].get('plot_qs', []))
    cp_path = component_path(config, component)
    plot_fname = op.join(cp_path, 'marking', 'plot_nb.ipynb')
    if not op.isfile(plot_fname):
        assert len(splot_qs) == 0
        return {}
    scores = get_plot_scores(plot_fname)
    sums = {}
    for login, vs in scores.items():
        missing = splot_qs.difference(vs)
        if missing:
            raise MCPError(
                f'Plot scores missing for {login}; {", ".join(missing)}')
        assert splot_qs == set(vs)
        sums[login] = sum(vs.values())
    return sums


def read_manuals(config, component):
    manual_qs = config['components'][component].get('manual_qs', [])
    mark_path = op.join(component_path(config, component), 'marking')
    expected_manuals = [op.join(mark_path, f'{q}_report.md')
                        for q in manual_qs]
    actual_manuals = glob(op.join(mark_path, '*_report.md'))
    missing = set(expected_manuals).difference(actual_manuals)
    if missing:
        smissing = ', '.join(sorted(missing))
        raise MCPError(f'Expected manual grading {smissing}')
    return [read_manual(fn)[1] for fn in expected_manuals]


def read_autos(config, component):
    cp_path = component_path(config, component)
    stid_col = config['student_id_col']
    # Read autos file
    autos = read_grades(op.join(cp_path, 'marking', 'autograde.csv'),
                        stid_col, 'Total')
    # Add annotation marks
    nb_fnames = get_notebooks(cp_path, first_only=True)
    for login, mark in nbs2markups(nb_fnames).items():
        autos[login] += mark
    return autos


def check_parts(autos, plots, manuals):
    # Autos should have the same keys as plots, if present.
    auto_set = set(autos)
    if len(plots):
        plot_set = set(plots)
        if auto_set != plot_set:
            auto_only = auto_set.difference(plot_set)
            plot_only = plot_set.difference(auto_set)
            msg = ('Plot and auto submissions differ - '
                   f'plot only: {plot_only if plot_only else "(none)"}; '
                   f'auto only: {auto_only if auto_only else "(none)"}')
            raise MCPError(msg)
    # Manuals should all have same keys, if present:
    for m in manuals:
        missing = auto_set.difference(m)
        if missing:
            raise MCPError(f'Missing manual score for {", ".join(missing)}')
    return sorted(auto_set)


def grade_component(config, component):
    autos = read_autos(config, component)
    plots = read_plots(config, component)
    manuals = read_manuals(config, component)
    logins = check_parts(autos, plots, manuals)
    grades = {}
    for student_id in logins:
        manual_mark = sum(m[student_id] for m in manuals)
        if student_id not in autos:
            raise MCPError(
                f'{student_id} not in autograded logins: {autos}')
        # check_parts makes sure both exist.
        nb_mark = autos[student_id]
        if plots:
            nb_mark += plots[student_id]
        grades[student_id] = manual_mark + nb_mark
    return grades


def write_component_csv(config, component, grades):
    out_path = component_path(config, component)
    stid_col = config['student_id_col']
    out_fname = op.join(out_path, 'marking', f'component.csv')
    with open(out_fname, 'wt') as fobj:
        fobj.write(f'{stid_col},Mark\n')
        for login, grade in grades.items():
            fobj.write(f'{login},{grade}\n')
    return out_fname


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    return parser


def main():
    args, config = get_component_config(get_parser())
    grades = grade_component(config, args.component)
    out_csv = write_component_csv(config, args.component, grades)
    print(pd.read_csv(out_csv).describe())


if __name__ == '__main__':
    main()
