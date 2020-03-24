#!/usr/bin/env python
""" Calculate grades for a component.

A student's grade comes from:

* Either:
    * Grades from autograding PLUS
    * Corrections from #M: notations
* Or:
    * Entry in `broken.csv` PLUS
* Grades from manual answer grading.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from glob import glob

import pandas as pd

from mcp_utils import read_config, read_manual, get_notebooks, nbs2markups


def read_grades(fname, stid_col, total_col):
    if not op.isfile(fname):
        return {}
    df = pd.read_csv(fname)
    return dict(zip(df[stid_col], df[total_col]))


def grade_component(config, component_path):
    stid_col = config['student_id_col']
    auto_marks = read_grades(op.join(component_path, 'autograde.csv'),
                             stid_col, 'Total')
    nb_fnames = get_notebooks(component_path, first_only=True)
    for login, mark in nbs2markups(nb_fnames).items():
        auto_marks[login] += mark
    broken = read_grades(op.join(component_path, 'broken.csv'),
                         stid_col,
                         'Mark')
    manual_globber = op.join(component_path, '*_report.md')
    manuals = [read_manual(fn)[1] for fn in glob(manual_globber)]
    keys0 = sorted(manuals[0])
    assert all([sorted(m) == keys0 for m in manuals[1:]])
    assert len(auto_marks) + len(broken) == len(keys0)
    assert len(set(auto_marks).intersection(broken)) == 0
    grades = {}
    for student_id in keys0:
        manual_mark = sum(m[student_id] for m in manuals)
        auto_mark = auto_marks.get(student_id, broken.get(student_id))
        grades[student_id] = manual_mark + auto_mark
    return grades


def write_component_csv(config, grades, out_path):
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
    component_path = op.join(config['base_path'], 'components', args.component)
    grades = grade_component(config, component_path)
    write_component_csv(config, grades, component_path)


if __name__ == '__main__':
    main()
