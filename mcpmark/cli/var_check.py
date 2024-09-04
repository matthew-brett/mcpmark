""" Check notebook for marking errors due to overwriting variables

Look for tests that pass in the main body of the notebook, but fail at the end.
"""

import re
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import numpy as np
from nbclient import execute as executenb

import jupytext
from ..mcputils import (get_notebooks, component_path,
                        get_component_config)


def check_passed(nb_path, **kwargs):
    """ Run notebook checking for overwritten variables.

    Look for tests that pass in the main body of the notebook, but fail at the
    end.

    Parameters
    ----------
    nb_path : str or Path
        Filename or Path to notebook.
    \*\*kwargs : dict
        Arguments to pass to `nbclien` `execute` function.
    """
    nb_path = Path(nb_path)
    nb = jupytext.read(nb_path)

    runned = executenb(nb, cwd=nb_path.parent)

    stdouts = []
    for cell in runned['cells']:
        if cell['cell_type'] != 'code':
            continue
        lines = []
        for output in cell['outputs']:
            if output['output_type'] != 'stream':
                continue
            if output['name'] != 'stdout':
                continue
            lines.append(output['text'].rstrip())
        if lines and 'Test summary' in lines:
            stdouts.append(lines)


    percents = []
    messages = []
    # Assume last test result is multi-test.
    for lines in stdouts[:-1]:
        for line in lines:
            if (match := re.match(r'\[o+k\.*] ([0-9.]+)% passed', line)):
                mark = float(match.groups()[0])
                if mark < 100:  # Fails
                    questions = find_questions(lines)
                    assert len(questions) == 1
                    messages.append(questions[0])
                percents.append(mark)
                continue

    last_percents = []
    lines = stdouts[-1]
    for line in lines:
        if (match := re.match(r'\[o+k\.*] ([0-9.]+)% passed', line)):
            last_percents.append(float(match.groups()[0]))
    last_messages = find_questions(lines)
    if len(percents) < len(last_percents):
        return False, ['Fewer tests in notebook than at end']
    if len(percents) > len(last_percents):
        return False, ['More tests in notebook than at end']
    if np.sum(percents) == np.sum(last_percents):
        return True, None
    return False, [
        f'In-notebook fails: {"; ".join(messages)}',
        f'End-notebook fails: {"; ".join(last_messages)}',
    ]


def find_questions(lines):
    questions = []
    for line in lines:
        if (match := re.search(r'^Question (\w+) >', line, flags=re.M)):
            questions.append(match.groups()[0])
    return questions


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
    prefix = '\n    '
    for nb_fname in nb_fnames:
        ok, messages = check_passed(nb_fname,
                                    timeout=args.timeout)
        if ok:
            print(f'{nb_fname} OK')
        else:
            msg_str = f'{prefix}'.join(messages)
            print(f'{nb_fname} mismatch:{prefix}{msg_str}')


if __name__ == '__main__':
    main()
