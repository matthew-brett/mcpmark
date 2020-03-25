#!/usr/bin/env python
""" Extract plots into one long notebook with cells for grading.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import nbformat.v4 as nbf

from mcp_utils import (read_config, get_notebooks, loginfn2login,
                       get_plot_nb, execute_nb_fname)


def extract_plot_nbs(nb_fnames):
    plot_nbs = {}
    for nb_fname in nb_fnames:
        enb = execute_nb_fname(nb_fname)
        plot_nb = get_plot_nb(enb)
        plot_nbs[loginfn2login(nb_fname)] = plot_nb
    return plot_nbs


def write_plot_nb(plot_nbs, plot_qs, out_path):
    nb = nbf.new_notebook()
    score_txt = '\n'.join(['Plot scores:'] +
                          [f'* {pq} : ' for pq in plot_qs])
    for login, plot_nb in plot_nbs.items():
        nb.cells.append(nbf.new_markdown_cell(f'## {login}'))
        nb.cells += plot_nb.cells
        nb.cells.append(nbf.new_markdown_cell(score_txt))
    nb_dir = op.join(out_path, 'generated')
    if not op.isdir(nb_dir):
        os.makedirs(nb_dir)
    with open(op.join(nb_dir, 'plot_nb.ipynb'), 'wt') as fobj:
        fobj.write(nbf.writes(nb))


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('component',
                        help='Component name for which to extract')
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--nb-lext', action='append',
                        help='Ordered list of notebook extensions '
                        'to search for (lower case, including . prefix)')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    plot_qs = config['components'][args.component]['plot_qs']
    nb_path = op.join(config['base_path'], 'components', args.component)
    lexts = args.nb_lext if args.nb_lext else ['.rmd', '.ipynb']
    nb_fnames = get_notebooks(nb_path,
                              recursive=False,
                              lexts=lexts,
                              first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{nb_path}" '
                           f'with extensions {lexts}')
    plot_nbs = extract_plot_nbs(nb_fnames)
    write_plot_nb(plot_nbs, plot_qs, nb_path)


if __name__ == '__main__':
    main()
