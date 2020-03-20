""" Unpack submissions into named directories
"""

import os
import os.path as op
import shutil
from zipfile import ZipFile
import re
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import yaml

import jupytext


BAD_DIRS = ['__pycache__', '__MACOSX']


def check_unpack(fnames, out_path):
    known = set()
    for fname in fnames:
        check_unpack1(fname, out_path, known)


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
            if not (d.startswith('.') or d in BAD_DIRS):
                ok_dirs.append(d)
            else:
                shutil.rmtree(op.join(root, d))
        dirs[:] = ok_dirs
        for fn in files:
            if fn.startswith('.'):
                os.unlink(op.join(root, fn))


def get_notebooks(in_dir):
    nbs = []
    for root, dirs, files in os.walk(in_dir):
        for fn in files:
            if fn.lower().endswith('.ipynb'):
                nbs.append(op.join(root, fn))
    return nbs


def get_spouse_dir(in_dir):
    notebooks = get_notebooks(in_dir)
    for nb_fname in notebooks:
        nb = jupytext.read(nb_fname)
        for cell in nb.cells:
            if cell['cell_type'] != 'markdown' or not 'source' in cell:
                continue
            text = cell['source']
            if re.search(r'#\s*Spouses,\s*Baggage', text.lower(), re.I):
                return op.dirname(nb_fname)


def get_spouse_dirs(allocations, submission_dir):
    ta2dirs = {}
    for ta_name, students in allocations.items():
        spouse_dirs = []
        for student in students:
            st_dir = op.join(submission_dir, student)
            if not op.isdir(st_dir):
                raise RuntimeError(f'Expected directory {st_dir}')
            st_dir = op.join(submission_dir, student)
            spouse_dir = get_spouse_dir(st_dir)
            assert spouse_dir is not None, f'No spouse dir for {student}'
            assert op.split(spouse_dir)[1] == 'spouses', f'Bad {spouse_dir}'
            spouse_dirs.append((student, spouse_dir))
        ta2dirs[ta_name] = spouse_dirs
    return ta2dirs


def build_for_tas(ta2dirs, out_path):
    for ta, spouse_dirs in ta2dirs.items():
        ta_prefix = ta.split('@')[0].lower()
        ta_path = op.join(out_path, ta_prefix)
        if op.isdir(ta_path):
            shutil.rmtree(ta_path)
        os.makedirs(ta_path)
        students = []
        for student, spouse_dir in spouse_dirs:
            st_dir = op.join(ta_path, student)
            shutil.copytree(spouse_dir, st_dir)
            students.append(student)
        mark_spreadsheet = op.join(ta_path, f'{ta_prefix}_marks.csv')
        with open(mark_spreadsheet, 'wt') as fobj:
            fobj.write('Student,Depth,Appropriate,Quality,Based\n')
            for student in students:
                fobj.write(f'{student},,,,\n')
        zip_fname = op.join(out_path, f'{ta_prefix}_spouses')
        shutil.make_archive(zip_fname, 'zip', ta_path)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('submission_dir',
                        help='Directory containing submissions')
    parser.add_argument('ta_allocations',
                        help='TA to name allocations YaML file')
    parser.add_argument('out_path',
                        help='Directory in which to write TA packs')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    with open(args.ta_allocations, 'rt') as fobj: 
         allocations = yaml.load(fobj)
    ta2dirs = get_spouse_dirs(allocations, args.submission_dir)
    build_for_tas(ta2dirs, args.out_path)


if __name__ == '__main__':
    main()
