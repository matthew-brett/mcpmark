#!/usr/bin/env python
""" Write grades from manual grading
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from ..mcputils import read_manual, read_config


def parse_write(config, in_file):
    out_file = op.splitext(in_file)[0] + '.csv'
    q_name, scores = read_manual(in_file)
    stid_col = config['student_id_col']
    with open(out_file, 'wt') as fobj:
        fobj.write(f'{stid_col},Mark\n')
        for login, score in scores.items():
            fobj.write(f'{login},{score}\n')


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('manual_report', nargs='+',
                        help='Path to manual report .md file(s)')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    for report in args.manual_report:
        parse_write(config, report)


if __name__ == '__main__':
    main()
