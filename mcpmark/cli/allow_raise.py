#!/usr/bin/env python
""" Write metadata allowing error in error cells
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter

from ..mcputils import (get_notebooks, component_path,
                        get_component_config)
from rnbgrader.allow_raise import write_skipped


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--nb-lext', action='append',
                        help='Ordered list of notebook extensions '
                        'to search for (lower case, including . prefix)')
    parser.add_argument('--no-show-error', action='store_true',
                        help='If set, do not display errors generated '
                        'during notebook execution')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='More verbosity')
    parser.add_argument('-t', '--timeout', type=int, default=120,
                        help='Timeout default')
    return parser


def main():
    args, config = get_component_config(get_parser())
    nb_path = component_path(config, args.component)
    lexts = args.nb_lext if args.nb_lext else ['.rmd', '.ipynb']
    nb_fnames = get_notebooks(nb_path, lexts, first_only=True)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No notebooks found in path "{nb_path}" '
                           f'with extensions {lexts}')
    for nb_fname in nb_fnames:
        if args.verbose:
            print(f'Grading {nb_fname}')
        write_skipped(nb_fname,
                      show_errors=not args.no_show_error,
                      timeout=args.timeout)


if __name__ == '__main__':
    main()
