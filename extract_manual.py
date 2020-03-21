#!/usr/bin/env python
""" Extract parts for manual grading into their own .md files.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import jupytext

from mcp_utils import (read_config, get_minimal_df, get_notebooks,
                       loginfn2login)



def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('nb_path',
                        help='Path to notebooks to extract from')
    parser.add_argument('ex_labels', nargs='+',
                        help='Labels for manual exercises')
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--nb-lext', action='append',
                        help='Ordered list of notebook extensions '
                        'to search for (lower case, including . prefix)')
    return parser


def extract_from_nb(nb_fname, labels):
    nb = jupytext.read(nb_fname)
    ex_md_text = {}
    for cell in nb.cells:
        problem_id = cell.get('metadata', {}).get('manual_problem_id')
        if problem_id in labels:
            assert problem_id not in ex_md_text
            ex_md_text[problem_id] = cell['source']
    return ex_md_text


def process_nbs(nb_fnames, ex_labels):
    slabels = set(ex_labels)
    all_answers = {}
    for nb_fname in nb_fnames:
        answers = extract_from_nb(nb_fname, ex_labels)
        missing = slabels.difference(answers)
        if missing:
            print(f'{nb_fname} has no metadata for {missing}')
        all_answers[loginfn2login(nb_fname)] = answers
    return all_answers


def write_answers(all_answers, config):
    print(all_answers)


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    lexts = args.nb_lext if args.nb_lext else ['.rmd', '.ipynb']
    nb_fnames = get_notebooks(args.nb_path, lexts, first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{args.nb_path}" '
                           f'with extensions {lexts}')
    all_answers = process_nbs(nb_fnames, args.ex_labels)
    write_answers(all_answers, config)


if __name__ == '__main__':
    main()
