""" Run grading

Copy and adjust test files into `tests` directory.

Copy `hw02.ok` and other supporting files file to this directory.

Download notebooks from Canvas, unzip into this directory.

Download grades CSV file from Canvas, save in this directory, change filename
in `build_grades....py` file.

Then see do_grading.py
"""

import os
import os.path as op
import sys

from glob import glob

from nbconvert.preprocessors import CellExecutionError

CFD2019 = op.expanduser(op.join('~', 'dev_trees', 'cfd2019'))
CFD_SCRIPTS = op.join(CFD2019, 'scripts')
sys.path.append(CFD_SCRIPTS)

import write_plot_nbs as wpn

OUT_PATH = 'plot_nbs'
if OUT_PATH and not op.isdir(OUT_PATH):
    os.makedirs(OUT_PATH)
EXE_PATH = '.'
START_FNAME = 'start_at.txt'

start_at = None
if op.isfile(START_FNAME):
    with open(START_FNAME, 'rt') as fobj:
        start_at = fobj.read().strip()

# Build plot notebooks
for nb_fname in sorted(glob('*.ipynb')):
    if start_at and nb_fname < start_at:
        continue
    start_at = None
    try:
        wpn.write_plot_nb(nb_fname, OUT_PATH, EXE_PATH)
    except CellExecutionError as e:
        print(f'Error in {nb_fname}')
        with open(START_FNAME, 'wt') as fobj:
            fobj.write(nb_fname)
        raise
