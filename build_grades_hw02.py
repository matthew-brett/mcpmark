""" Master script for building grades from grading products
"""
import re
from glob import glob
import os.path as op

import numpy as np
import pandas as pd

from rnbgrader.grader import CanvasGrader
from gradools import canvastools as ct


HERE = op.dirname(__file__)


def read_canvas(canvas_fname):
    required = ('ID', 'Student', 'SIS User ID', 'SIS Login ID', 'Section')
    dtypes = {'ID': int, 'SIS User ID': int}
    df = ct.to_minimal_df(canvas_fname, required, dtypes)
    return df.set_index('ID')


# Fill this in from CSV file.
field = 'Homework 2 (203672)'
df = read_canvas(op.join(
    HERE, '2019-12-19T2021_Grades-LM_Intro_to_Programming.csv'))
df[field] = np.nan


"""
# Get grade output with:
python ~/dev_trees/cfd2019/scripts/grade_oknb.py *.Rmd --cwd=$PWD > grade_output.txt
"""


def read_grade_output(grades_fname):
    """ Parse output from grade_oknb.py script
    """
    with open(grades_fname, 'rt') as fobj:
        output = fobj.read()

    parts = re.split('^(\w+_.*\.Rmd)$', output, flags=re.M)
    if parts[0].strip() == '':
        parts.pop(0)

    rows = []
    for i in range(0, len(parts), 2):
        fname = parts[i]
        result = parts[i + 1]
        assert fname.endswith('.Rmd')
        assert len(result)
        total_match = re.search('^Total: (\d+)$', result, flags=re.M)
        if total_match is None:
            print('No total for', fname, '- please check')
            continue
        name, _, stid = ct.fname2key(fname)
        mark = float(total_match.groups()[0])
        rows.append([int(stid), name, mark])
    df = pd.DataFrame(data=rows, columns=['ID', 'Student', 'Mark'])
    return df.set_index('ID')

# Add main marks
main_marks = read_grade_output(op.join(HERE, 'grade_output.txt'))
df.loc[main_marks.index, field] = main_marks['Mark']

# Set marks from manual CSV
manual = pd.read_csv(op.join(HERE, 'manual_marks.csv'))
# Set indices for manual table (which only has names)
manual = manual.merge(df['Student'].reset_index(), on='Student').set_index('ID')
df.loc[manual.index, field] = manual['Mark']

# Add marks from plots
# python write_plot_marks.py
pmarks = pd.read_csv(op.join(HERE, 'plot_marks.csv')).set_index('ID')
df.loc[pmarks.index, field] += pmarks['Mark']

# Adjustments from notebook text
def nbs_to_markups(nb_fnames):
    cg = CanvasGrader()
    rows = []
    for nb_fname in nb_fnames:
        name, _, stid = ct.fname2key(nb_fname)
        markups = cg.mark_markups(nb_fname)
        if len(markups) == 0:
            continue
        rows.append([int(stid), name, sum(markups)])
    df = pd.DataFrame(data=rows, columns=['ID', 'Student', 'Mark'])
    return df.set_index('ID')

markups = nbs_to_markups(glob('*.Rmd'))
df.loc[markups.index, field] += markups['Mark']

print("Missing")
print(df.loc[df[field].isna()])

print("Less than 70")
print(df.loc[df[field] < 70])

df.insert(1, 'ID', df.index)
df.to_csv(op.join(HERE, 'hw02_grades.csv'), index=False)

# Setting missing to 0
df.loc[df[field].isna(), field] = 0
df.to_csv(op.join(HERE, 'hw02_grades_filled.csv'), index=False)
