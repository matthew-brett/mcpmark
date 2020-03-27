#!/usr/bin/env python
""" Copy model answer files to component directory
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import shutil

from mcp_utils import read_config, component_path


def good_path(path):
    froot, ext = op.splitext(path)
    if ext in ('.md', '.ipynb', '.Rmd'):
        return False
    if path.startswith('.'):
        return False
    return True


def cp_with_dir(in_fname, out_fname):
    out_dir = op.dirname(out_fname)
    if not op.isdir(out_dir):
        os.makedirs(out_dir)
    shutil.copy(in_fname, out_fname)


def cp_model(model_path, component_path):
    for root, dirs, files in os.walk(model_path):
        dirs[:] = [d for d in dirs if good_path(d)]
        for fn in files:
            if not good_path(fn):
                continue
            full_path = op.join(root, fn)
            rel_path = op.relpath(full_path, model_path)
            cp_with_dir(full_path, op.join(component_path, rel_path))


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('model_path',
                        help='Path containing model files')
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
    if not args.component in config['components']:
        raise RuntimeError(f'"{args.component}" not in config')
    cp_model(args.model_path, component_path(config, args.component))


if __name__ == '__main__':
    main()
