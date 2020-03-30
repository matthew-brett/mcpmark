#!/usr/bin/env python
""" Extract parts for manual grading into their own .md files.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import jupytext

from ..mcputils import (read_config, get_notebooks, loginfn2login, MCPError,
                       component_path)


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
    errors = []
    for nb_fname in nb_fnames:
        answers = extract_from_nb(nb_fname, ex_labels)
        missing = slabels.difference(answers)
        if missing:
            errors.append(f'{nb_fname} has no metadata for {missing}')
        else:
            all_answers[loginfn2login(nb_fname)] = answers
    if errors:
        raise MCPError('\n'.join(errors))
    return all_answers


def write_answers(all_answers, out_path):
    k0 = list(all_answers)[0]
    for label in all_answers[k0]:
        lines = [f'# Answers for {label}', '']
        for login, a_dict in all_answers.items():
            answer = a_dict[label]
            lines += [f'## {login}', '', f'{answer}', '', 'MCPScore:', '']
        out_fname = op.join(out_path, f'{label}_report.md')
        with open(out_fname, 'wt') as fobj:
            fobj.write('\n'.join(lines))


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    ex_labels = config['components'][args.component]['manual_qs']
    nb_path = component_path(config, args.component)
    lexts = args.nb_lext if args.nb_lext else ['.rmd', '.ipynb']
    nb_fnames = get_notebooks(nb_path,
                              recursive=False,
                              lexts=lexts,
                              first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{nb_path}" '
                           f'with extensions {lexts}')
    all_answers = process_nbs(nb_fnames, ex_labels)
    assert len(all_answers) == len(nb_fnames)
    write_answers(all_answers, op.join(nb_path, 'marking'))


if __name__ == '__main__':
    main()
