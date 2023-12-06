#!/usr/bin/env python
""" Export marks for upload to Canvas, submission to office.
"""

from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas as pd

from gradools import canvastools as ct

from ..mcputils import get_minimal_df, read_config


def write_exports(config, out_dir):
    login_fn = config['student_id_col']
    template = ct.to_minimal_df(config['canvas_export_path'])
    ass_col = config['assignment_name']
    out_cols = list(template) + [ass_col]
    in_fname = config['mark_fname']
    in_df = get_minimal_df(config)[[login_fn, ct.CANVAS_ID_COL]]
    df = in_df.merge(template,
                     on=ct.CANVAS_ID_COL,
                     how='left').set_index(login_fn)
    mark_df = pd.read_csv(in_fname).set_index(login_fn)
    for out_field in ('Percent', 'Total'):
        final = mark_df.loc[:, [out_field]].copy()
        ok_final = final.rename(columns={out_field: ass_col})
        ffinal = df.join(ok_final, how='right')
        export = ffinal.loc[:, out_cols]
        out_fname = out_dir / f'interim_marks_{out_field.lower()}.csv'
        export.to_csv(out_fname, index=None)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=Path() / 'assign_config.yaml',
                        help='Path to config file')
    parser.add_argument('--out-dir',
                        help='Directory to which to write files')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    out_dir = args.out_dir if args.out_dir else config['base_path']
    write_exports(config, Path(out_dir))


if __name__ == '__main__':
    main()
