#!/usr/bin/env python
""" Scale marks to final totals, combine components (if more than one).
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas as pd

from ..mcputils import (read_config, component_path)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    return parser


def process_components(config):
    series = {}
    stid_col = config['student_id_col']
    components = config['components']
    scaled_max = sum([components[c]['scaled_to'] for c in components])
    for name, info in components.items():
        csv_pth = op.join(component_path(config, name),
                          'marking',
                          'component.csv')
        if not op.isfile(csv_pth):
            raise RuntimeError(f'No component csv file at {csv_pth}; '
                               'Do you need to run mcp-grade-component?')
        df = pd.read_csv(csv_pth).set_index(stid_col)
        series[name] = df['Mark'] * info['scaled_to'] / info['actual_max']
    final = pd.DataFrame(series)
    total = final.sum(axis=1)
    if config.get('round_final'):
        total = round(total)
    final['Percent'] = total / scaled_max * 100
    final['Total'] = total
    return final


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    all_answers = process_components(config)
    out_csv = op.join(config['base_path'], config['mark_fname'])
    all_answers.to_csv(out_csv)
    print(all_answers.describe())


if __name__ == '__main__':
    main()
