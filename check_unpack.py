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


BAD_GLOBS = ['__pycache__', '__MACOSX', '.*']


def check_unpack(fnames, out_path):
    known = set()
    for fname in fnames:
        out_dir = check_unpack1(fname, out_path, known)
        print(f'Unpacked {fname} to {out_dir}')


def check_unpack1(fname, out_path, known):
    name1, name2, id_no = ct.fname2key(fname)
    assert name2 == ''
    assert name1 not in known
    this_out = op.join(out_path, name1)
    if op.isdir(this_out):
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
    parser.add_argument('zip_submission_path',
                        help='Directory containing zip file submissions')
    parser.add_argument('--out-path',
                        default=op.join(os.getcwd(), 'submissions'),
                        help='Path for output directories')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    zip_glob = op.join(args.zip_submission_path, '*.zip')
    zip_fnames = glob(zip_glob)
    if len(zip_fnames) == 0:
        raise RuntimeError(f'No files with glob "{zip_glob}"')
    if op.isdir(args.out_path) and os.listdir(args.out_path):
        raise RuntimeError(
            f'Out path "{args.out_path}" exists and is not empty')
    check_unpack(zip_fnames, args.out_path)


if __name__ == '__main__':
    main()
