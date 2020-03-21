#!/usr/bin/env python
""" Write grades from manual grading
"""

import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from mcp_utils import get_manual_scores


def parse_write(in_file):
    out_file = op.splitext(in_file)[0] + '.csv'
    with open(in_file, 'rt') as fobj:
        contents = fobj.read()
    scores = get_manual_scores(contents)
    with open(out_file, 'wt') as fobj:
        fobj.write('SIS Login ID,Mark\n')
        for login, score in scores.items():
            fobj.write(f'{login},{score}\n')


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('manual_report', nargs='+',
                        help='Path to manual report .md file(s)')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    for report in args.manual_report:
        parse_write(report)


if __name__ == '__main__':
    main()
