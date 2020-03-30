#!/usr/bin/env python
""" Calculate grades for a component.

A student's grade comes from:

* Either:
    * Grades from autograding PLUS
    * Corrections from #M: notations
    * Grades from plots (if present)
* Or:
    * Entry in `broken.csv` PLUS
* Grades from manual answer grading.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from glob import glob

import pandas as pd

from mcp_utils import (read_config, read_manual, get_notebooks, nbs2markups,
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
    for k, v in scores.items():
        assert splot_qs == set(v)
        sums[k] = sum(v.values())
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


def read_broken(config, component):
    broken_path = op.join(component_path(config, component),
                          'marking',
                          'broken.csv')
    if not op.isfile(broken_path):
        return {}
    return read_grades(broken_path, config['student_id_col'], 'Mark')


def check_parts(autos, plots, broken, manuals):
    # Autos should have the same keys as plots, if present.
    if len(plots):
        assert set(autos) == set(plots)
    # No student should be in both autos and broken
    if broken:
        assert len(set(autos).intersection(broken)) == 0
    # Union of autos and broken should be all students.
    slogins = set(autos).union(broken)
    # Manuals should all have same keys, if present:
    for m in manuals:
        assert set(m) == slogins
    return sorted(slogins)


def grade_component(config, component):
    autos = read_autos(config, component)
    plots = read_plots(config, component)
    broken = read_broken(config, component)
    manuals = read_manuals(config, component)
    logins = check_parts(autos, plots, broken, manuals)
    grades = {}
    for student_id in logins:
        manual_mark = sum(m[student_id] for m in manuals)
        if student_id in autos:
            # check_parts makes sure both exist.
            nb_mark = autos[student_id]
            if plots:
                nb_mark += plots[student_id]
        else:  # check_parts checks this.
            nb_mark = broken[student_id]
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
    parser.add_argument('component',
                        help='Component name for which to extract')
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    grades = grade_component(config, args.component)
    out_csv = write_component_csv(config, args.component, grades)
    print(pd.read_csv(out_csv).describe())


if __name__ == '__main__':
    main()
