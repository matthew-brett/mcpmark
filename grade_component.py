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
                       get_plot_scores, component_path)


def read_grades(fname, stid_col, total_col):
    if not op.isfile(fname):
        return {}
    df = pd.read_csv(fname)
    return dict(zip(df[stid_col], df[total_col]))


def read_plots(config, component):
    splot_qs = set(config['components'][component].get('plot_qs', []))
    cp_path = component_path(config, component)
    plot_fname = op.join(cp_path, 'generated', 'plot_nb.ipynb')
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
    cp_path = component_path(config, component)
    expected_manuals = [op.join(cp_path, f'{q}_report.md') for q in manual_qs]
    actual_manuals = glob(op.join(cp_path, '*_report.md'))
    assert set(expected_manuals) == set(actual_manuals)
    return [read_manual(fn)[1] for fn in expected_manuals]


def read_autos(config, component):
    cp_path = component_path(config, component)
    stid_col = config['student_id_col']
    # Read autos file
    autos = read_grades(op.join(cp_path, 'autograde.csv'),
                        stid_col, 'Total')
    # Add annotation marks
    nb_fnames = get_notebooks(cp_path, first_only=True)
    for login, mark in nbs2markups(nb_fnames).items():
        autos[login] += mark
    return autos


def read_broken(config, component):
    broken_path = op.join(component_path(config, component),
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
        auto_mark = autos.get(student_id, broken.get(student_id))
        grades[student_id] = manual_mark + auto_mark
    return grades


def write_component_csv(config, component, grades):
    out_path = component_path(config, component)
    stid_col = config['student_id_col']
    out_fname = op.join(out_path, f'component.csv')
    with open(out_fname, 'wt') as fobj:
        fobj.write(f'{stid_col},Mark\n')
        for login, grade in grades.items():
            fobj.write(f'{login},{grade}\n')


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
    write_component_csv(config, args.component, grades)


if __name__ == '__main__':
    main()
