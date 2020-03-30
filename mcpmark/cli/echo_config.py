#!/usr/bin/env python
""" Echo key from config file
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from ..mcputils import read_config


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('key',
                        help='Key for value to echo')
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    print(config[args.key])


if __name__ == '__main__':
    main()
