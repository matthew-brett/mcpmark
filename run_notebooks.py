#!/usr/bin/env python
""" Run notebooks in directory, restarting at last failure.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from nbconvert.preprocessors import CellExecutionError

from mcp_utils import get_notebooks, execute_nb_fname

START_FNAME = '.execute_start_at'


def execute_nbs(fnames, start_fname, timeout=240):
    start_at = None
    if op.isfile(start_fname):
        with open(start_fname, 'rt') as fobj:
            start_at = fobj.read().strip()
    for nb_fname in sorted(fnames):
        if start_at and nb_fname < start_at:
            continue
        try:
            execute_nb_fname(nb_fname, timeout, verbose=True)
        except CellExecutionError as e:
            with open(start_fname, 'wt') as fobj:
                fobj.write(nb_fname)
            raise
    os.unlink(start_fname)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('nb_path',
                        help='Path of notebooks to execute')
    parser.add_argument('--nb-lext', action='append',
                        help='Ordered list of notebook extensions '
                        'to search for (lower case, including . prefix)')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    lexts = args.nb_lext if args.nb_lext else ['.rmd', '.ipynb']
    nb_fnames = get_notebooks(args.nb_path, lexts, first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{args.nb_path}" '
                           f'with extensions {lexts}')
    start_fname = op.join(op.dirname(nb_fnames[0]), START_FNAME)
    execute_nbs(nb_fnames, start_fname)


if __name__ == '__main__':
    main()
