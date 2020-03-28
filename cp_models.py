#!/usr/bin/env python
""" Copy model answer files from model paths to component paths.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from mcp_utils import read_config, cp_model, component_path


def cp_models(config):
    models_base = op.join(config['base_path'], 'models')
    if not op.isdir(models_base):
        raise RuntimeError('No directory ' + models_base)
    for component in config['components']:
        model_path = op.join(models_base, component)
        cp_model(model_path, component_path(config, component))


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    cp_models(config)


if __name__ == '__main__':
    main()
