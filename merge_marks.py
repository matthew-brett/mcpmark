#!/usr/bin/env python
""" Merge mark files, later files have precedence.
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas as pd


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('csv_file', nargs='+',
                        help='CSV files to merge')
    parser.add_argument('--out-csv', default='merged_final.csv',
                        help='Output file to write')
    return parser


def merge_csvs(fnames, on_col=0):
    dfs = []
    for fname in fnames:
        dfs.append(pd.read_csv(fname))
    merged = dfs[0]
    if isinstance(on_col, int):  # Convert index to column name.
        on_col = list(merged)[on_col]
    for other in dfs[1:]:
        for i, row in other.iterrows():
            row_id = row.loc[on_col]
            # Drop existing matching rows.
            merged = merged[row_id != merged.loc[:, on_col]]
            # Append current row.
            merged = merged.append(row, ignore_index=True)
    return merged.sort_values(on_col)


def main():
    parser = get_parser()
    args = parser.parse_args()
    merged = merge_csvs(args.csv_file)
    merged.to_csv(args.out_csv, index=None)
    print(merged.describe())


if __name__ == '__main__':
    main()
