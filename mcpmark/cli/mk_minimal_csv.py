#!/usr/bin/env python
""" Build minimal CSV file given input Canvas export and config.
"""
import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from ..mcputils import read_config, get_minimal_df


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
