#!/usr/bin/env python
""" Build minimal CSV file given input Canvas export and config.
"""
import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import yaml
import numpy as np

from gradools import canvastools as ct


def read_canvas(canvas_fname):
    required = ('ID', 'Student', 'SIS User ID', 'SIS Login ID', 'Section')
    dtypes = {'ID': int, 'SIS User ID': int}
    df = ct.to_minimal_df(canvas_fname, required, dtypes)
    return df.set_index('ID')


def read_config(config_fname):
    with open(config_fname, 'rt') as fobj:
        res = yaml.load(fobj)
    config_path = op.abspath(op.dirname(config_fname))
    res['canvas_export'] = op.join(config_path, res['canvas_export'])
    return res


def get_minimal_df(config):
    df = read_canvas(config['canvas_export'])
    df[config['assignment_name']] = np.nan
    return df


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--out-path',
                        help='Path for output csv')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    if args.out_path is None:
        args.out_path = op.join(op.dirname(args.config_path), 'assign_df.csv')
    config = read_config(args.config_path)
    print('Writing', args.out_path)
    get_minimal_df(config).to_csv(args.out_path)


if __name__ == '__main__':
    main()
