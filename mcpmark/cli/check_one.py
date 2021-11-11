#!/usr/bin/env python
""" Move one-component submissions into multi-submission structure.

Usually used via `mcp-check-unpack`.
"""

import os
import os.path as op
import shutil
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from glob import glob

from gradools import canvastools as ct

from ..mcputils import get_minimal_df, get_component_config


def check_rename(config, fnames, out_path, component, df, clobber=False):
    known = set()
    for fname in fnames:
        out_dir = check_rename1(config, fname, out_path, component,
                                df, clobber, known)
        print(f'Checked, renamed {fname} to {out_dir}')


def check_rename1(config, fname, out_path, component, df, clobber, known):
    name1, name2, id_no = ct.fname2key(fname)
    assert name2 == ''
    st_login = df.loc[int(id_no), config['student_id_col']]
    assert st_login not in known
    this_out = op.join(out_path, st_login, component)
    if op.isdir(this_out):
        if not clobber:
            raise RuntimeError(f'Directory "{this_out}" exists')
        shutil.rmtree(this_out)
    os.makedirs(this_out)
    # Copy notebook.
    out_fname = op.join(this_out, op.basename(fname))
    shutil.copy2(fname, out_fname)
    return out_fname


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--clobber', action='store_true',
                        help='If set, delete existing output directories')
    return parser


def main():
    args, config = get_component_config(get_parser())
    nb_glob = op.join(config['input_submission_path'], '*.ipynb')
    nb_fnames = glob(nb_glob)
    if len(nb_fnames) == 0:
        raise RuntimeError(f'No files with glob "{nb_glob}"')
    out_path = config['submissions_path']
    df = get_minimal_df(config)
    check_rename(config, nb_fnames, out_path,
                 args.component,
                 df, clobber=args.clobber)
