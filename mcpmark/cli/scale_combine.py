#!/usr/bin/env python
""" Scale marks to final totals, combine components (if more than one).
"""

from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import pandas as pd

from ..mcputils import read_config, component_path, MCPError


def read_component(name, config):
    return read_component_csv(Path(component_path(config, name)) /
                              'marking' /
                              'component.csv')


def remove_unnamed(seq_of_seq, rep):
    out = []
    for seq in seq_of_seq:
        out.append(tuple([s if not s.startswith('Unnamed: ') else rep
                          for s in seq]))
    return tuple(out)


def read_component_csv(csv_pth):
    if not csv_pth.is_file():
        raise RuntimeError(f'No component csv file at {csv_pth}; '
                            'Do you need to run mcp-grade-component?')
    comp_marks = pd.read_csv(csv_pth, header=[0, 1], index_col=0)
    # Check for old API
    if list(comp_marks)[0][0] == 'Mark' and len(comp_marks.columns) == 1:
        raise MCPError(f'{csv_pth} looks like the old component CSV format; '
                       'use mcpmark < 1.0 to use these files')
    comp_marks.columns = remove_unnamed(comp_marks.columns, '')
    return comp_marks


def process_components(config):
    components = config['components']
    scaled_max = sum([components[c]['scaled_to'] for c in components])
    final = pd.DataFrame()
    for name, info in components.items():
        df = read_component(name, config)
        final[name] = df['Total'] * info['scaled_to'] / info['actual_max']
    total = final.sum(axis=1)
    if config.get('round_final'):
        total = round(total)
    percent = total / scaled_max * 100
    final['Percent'] = (round(percent) if config.get('round_percent')
                        else percent)
    final['Total'] = total
    return final.reset_index().rename(
        columns={'index': config['student_id_col']})


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=Path('assign_config.yaml'),
                        help='Path to config file')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    all_answers = process_components(config)
    out_csv = Path(config['base_path']) / config['mark_fname']
    all_answers.to_csv(out_csv, index=None)
    print(all_answers.describe())


if __name__ == '__main__':
    main()
