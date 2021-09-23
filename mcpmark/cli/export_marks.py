#!/usr/bin/env python
""" Process marks for upload to Canvas, submission to office.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas as pd

from ..mcputils import get_minimal_df, read_config


def write_exports(config, out_dir):
    login_fn = config['student_id_col']
    ass_fn = config['assignment_name']
    in_fname = config['mark_fname']
    in_df = get_minimal_df(config)
    df = in_df.set_index(login_fn).drop(ass_fn, axis=1)
    mark_df = pd.read_csv(in_fname).set_index(login_fn)
    for out_field in ('Percent', 'Total'):
        final = mark_df.loc[:, [out_field]].copy()
        ok_final = final.rename(columns={out_field: ass_fn})
        ffinal = ok_final.join(df)
        ffinal[login_fn] = ffinal.index
        export = ffinal.loc[:, list(in_df)]
        out_fname = op.join(out_dir, f'interim_marks_{out_field.lower()}.csv')
        export.to_csv(out_fname, index=None)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--out-dir',
                        help='Directory to which to write files')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    out_dir = args.out_dir if args.out_dir else config['base_path']
    write_exports(config, out_dir)


if __name__ == '__main__':
    main()
