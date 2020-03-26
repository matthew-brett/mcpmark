#!/usr/bin/env python
""" Extract parts for manual grading into their own .md files.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas as pd

from mcp_utils import (read_config, component_path)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    return parser


def process_components(config):
    seriess = {}
    stid_col = config['student_id_col']
    components = config['components']
    max_overall = sum([components[c]['scaled_to'] for c in components])
    for name, info in components.items():
        csv_pth = op.join(component_path(config, name),
                          'marking',
                          'component.csv')
        df = pd.read_csv(csv_pth).set_index(stid_col)
        scf = info['scaled_to'] / info['actual_max']
        series = df['Mark'].astype(float) * scf
        seriess[name] = series
    final = pd.DataFrame(seriess)
    total = final.sum(axis=1)
    final['Percent'] = total / max_overall * 100
    final['Total'] = total
    return final


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    all_answers = process_components(config)
    all_answers.to_csv(op.join(config['base_path'], 'final.csv'))
    print(all_answers.describe())


if __name__ == '__main__':
    main()
