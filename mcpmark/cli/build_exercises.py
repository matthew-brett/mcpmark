""" Build directory of student exercises for upload to JupyterHub etc.
"""

import shutil
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from ..mcputils import (make_submission_handler, get_component_config)

import oktools.cutils as okcu

from .prepare_components import expected_login_ids


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        '--drop-missing', action='store_true',
        help='If set, drop missing rows with missing student identifier')
    parser.add_argument(
        '--out-path', default='built',
        help='Output path for built files (default "built")')
    return parser


def build_ex_paths(in_path, out_path, components):
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    site_dict, _ = okcu.proc_config(in_path)
    for component in components:
        in_comp = in_path / component
        okcu.process_dir(in_comp, site_dict=site_dict)
        okcu.write_ipynb(in_comp, 'exercise')
        okcu.write_dir(in_comp, out_path / component)


def main():
    args, config = get_component_config(
        get_parser(),
        multi_component=True,
        component_default='all')
    assess_name = config['assignment_name']
    files_path = Path(assess_name)
    build_ex_paths(Path('models'), files_path, list(config['components']))
    assess_path = Path(args.out_path)
    handler = make_submission_handler(config)
    for login_id in expected_login_ids(config, args.drop_missing):
        gh_path = handler.login2jh(login_id)
        out_path = assess_path / gh_path / assess_name
        out_path.mkdir(exist_ok=True, parents=True)
        shutil.copytree(files_path, out_path,
                        dirs_exist_ok=True)
        shutil.copy2('README.md', out_path)


if __name__ == '__main__':
    main()
