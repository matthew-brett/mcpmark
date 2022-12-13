#!/usr/bin/env python
""" Unpack submissions into named directories
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from glob import glob


from ..mcputils import read_config, make_submission_handler


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--clobber', action='store_true',
                        help='If set, delete existing output directories')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    one_comp = len(config['components']) == 1
    exp_ext = '.ipynb' if one_comp else '.zip'
    fn_glob = op.join(config['input_submission_path'], '*' + exp_ext)
    fnames = glob(fn_glob)
    if len(fnames) == 0:
        raise RuntimeError(f'No files with glob "{fn_glob}"')
    out_path = config['submissions_path']
    sub_handler = make_submission_handler(config)
    df = sub_handler.get_minimal_df()
    if one_comp:
        component = list(config['components'])[0]
        sub_handler.check_rename(fnames, out_path, component, df,
                                 clobber=args.clobber)
    else:
        sub_handler.check_unpack(fnames, out_path, df, clobber=args.clobber)


if __name__ == '__main__':
    main()
