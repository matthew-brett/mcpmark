#!/usr/bin/env python
""" Calculate grades for notebooks.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from grade_oknb import grade_nb_fname
from mcp_utils import (read_config, get_notebooks, loginfn2login)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('component',
                        help='Component name for which to extract')
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--nb-lext', action='append',
                        help='Ordered list of notebook extensions '
                        'to search for (lower case, including . prefix)')
    return parser


def grade_nbs(nb_fnames, cwd):
    grades = {}
    for nb_fname in nb_fnames:
        grades[loginfn2login(nb_fname)] = grade_nb_fname(nb_fname, cwd)
    return grades


def write_grade_report(all_grades, out_path):
    lines = []
    for login, grades in all_grades.items():
        lines += [f'## {login}\n']
        for tn in sorted(grades):
            lines.append(f'{tn}: {grades[tn]}')
        lines.append(f'Total: {sum(grades.values())}\n')
    out_fname = op.join(out_path, f'autograde.md')
    with open(out_fname, 'wt') as fobj:
        fobj.write('\n'.join(lines))


def write_grade_csv(config, all_grades, out_path):
    stid_col = config['student_id_col']
    out_fname = op.join(out_path, f'autograde.csv')
    first_grades = all_grades[list(all_grades)[0]]
    lines = [','.join([stid_col] + list(first_grades) + ['Total'])]
    for login, grades in all_grades.items():
        values = list(grades.values())
        s_values = [str(v) for v in (values + [sum(values)])]
        lines.append(','.join([login] + s_values))
    with open(out_fname, 'wt') as fobj:
        fobj.write('\n'.join(lines))


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    nb_path = op.join(config['base_path'], 'components', args.component)
    lexts = args.nb_lext if args.nb_lext else ['.rmd', '.ipynb']
    nb_fnames = get_notebooks(nb_path, lexts, first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{nb_path}" '
                           f'with extensions {lexts}')
    all_grades = grade_nbs(nb_fnames, nb_path)
    assert len(all_grades) == len(nb_fnames)
    write_grade_report(all_grades, nb_path)
    write_grade_csv(config, all_grades, nb_path)


if __name__ == '__main__':
    main()
