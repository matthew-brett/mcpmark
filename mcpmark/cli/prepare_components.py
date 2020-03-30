#!/usr/bin/env python
""" Prepare components for marking

* Rewrite component notebooks into their own directories.
* Make Rmd versions of notebooks.
* Create `broken` subdirectory.
* Write empty `broken.csv` marks file.
"""

import os
import os.path as op
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import shutil

import jupytext

from ..mcputils import (read_config, get_minimal_df, get_notebooks,
                       component_path, MCPError)


def get_component_nbs(in_dir, component_tests):
    notebooks = get_notebooks(in_dir, recursive=True)
    component_nbs = {}
    for nb_fname in notebooks:
        nb = jupytext.read(nb_fname)
        for component, component_test in component_tests.items():
            if component_test(nb, nb_fname):
                assert component not in component_nbs
                component_nbs[component] = (nb_fname, nb)
    missing = set(component_tests).difference(component_nbs)
    if missing:
        missing = '\n'.join(sorted(missing))
        raise MCPError(f'Missing notebooks in {in_dir}:\n{missing}')
    return component_nbs


def get_component_tests(config):
    ns = {}
    with open(config['component_script_path'], 'rt') as fobj:
        exec(fobj.read(), ns)
    return ns['COMPONENT_TESTS']


def expected_student_dirs(config):
    df = get_minimal_df(config)
    stid_col = config['student_id_col']
    dir_names = []
    for i_val, row in df.iterrows():
        login_id = row.loc[stid_col]
        if login_id not in config['known_missing']:
            dir_names.append(login_id)
    assert len(set(dir_names)) == len(dir_names)  # Unique check
    return dir_names


def create_dirs(root_path, names, gitignore=False):
    for name in names:
        out_path = op.join(root_path, name)
        if not op.isdir(out_path):
            os.makedirs(out_path)
            if gitignore:
                with open(op.join(out_path, '.gitignore'), 'wt') as fobj:
                    fobj.write('')


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--out-path',
                        help='Path for output directories')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    if args.out_path is None:
        args.out_path = op.dirname(args.config_path)
    config = read_config(args.config_path)
    stid_col = config['student_id_col']
    component_tests = get_component_tests(config)
    component_names = list(component_tests)
    component_base = component_path(config)
    create_dirs(component_base, component_names)
    sub_path = config['submissions_path']
    for login_id in expected_student_dirs(config):
        exp_path = op.join(sub_path, login_id)
        if not op.isdir(exp_path):
            raise RuntimeError(f'{exp_path} expected, but does not exist')
        nbs = get_component_nbs(exp_path, component_tests)
        for component, (nb_fname, nb) in nbs.items():
            component_root = op.join(component_base, component)
            _, ext = op.splitext(nb_fname)
            out_root = op.join(component_root, login_id)
            shutil.copy2(nb_fname, out_root + ext)
            if ext.lower() != '.rmd':  # Write Rmd version if necessary.
                jupytext.write(nb, out_root + '.Rmd', fmt='Rmd')
            create_dirs(component_root,
                        ['broken', 'marking'],
                        gitignore=True)
            broken_fname = op.join(component_root, 'marking', 'broken.csv')
            with open(broken_fname, 'wt') as fobj:
                fobj.write(f'{stid_col},Mark\n')


if __name__ == '__main__':
    main()
