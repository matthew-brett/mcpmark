#!/usr/bin/env python
""" Unpack submissions into named directories
"""

import os
import os.path as op
import shutil
from zipfile import ZipFile
from fnmatch import fnmatch
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from glob import glob

from gradools import canvastools as ct

from mcp_utils import read_config, get_minimal_df

BAD_GLOBS = ['__pycache__', '__MACOSX', '.*']


def check_unpack(config, fnames, out_path, df, clobber=False):
    known = set()
    for fname in fnames:
        out_dir = check_unpack1(config, fname, out_path, df, clobber, known)
        print(f'Unpacked {fname} to {out_dir}')


def check_unpack1(config, fname, out_path, df, clobber, known):
    name1, name2, id_no = ct.fname2key(fname)
    assert name2 == ''
    st_login = df.loc[int(id_no), config['student_id_col']]
    assert st_login not in known
    this_out = op.join(out_path, st_login)
    if op.isdir(this_out):
        if not clobber:
            raise RuntimeError(f'Directory "{this_out}" exists')
        shutil.rmtree(this_out)
    os.makedirs(this_out)
    with ZipFile(fname, 'r') as zf:
        zf.extractall(path=this_out)
    # Clean extracted files.
    for root, dirs, files in os.walk(this_out):
        ok_dirs = []
        for d in dirs:
            if not (fnmatch(d, g) for g in BAD_GLOBS):
                ok_dirs.append(d)
            else:
                shutil.rmtree(op.join(root, d))
        dirs[:] = ok_dirs
        for fn in files:
            if fn.startswith('.'):
                os.unlink(op.join(root, fn))
    return this_out


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), 'assign_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--clobber', action='store_true',
                        help='If set, delete existing output directories')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = read_config(args.config_path)
    zip_glob = op.join(config['assignment_zip_path'], '*.zip')
    zip_fnames = glob(zip_glob)
    if len(zip_fnames) == 0:
        raise RuntimeError(f'No files with glob "{zip_glob}"')
    out_path = config['submissions_path']
    df = get_minimal_df(config)
    check_unpack(zip_fnames, out_path, df, clobber=args.clobber)


if __name__ == '__main__':
    main()
