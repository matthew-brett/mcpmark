""" Master script for building grades from grading products
"""
from glob import glob
import os.path as op

import pandas as pd

from mcp_utils import (read_grade_output, read_config, get_minimal_df,
                       nbs_to_markups)


HERE = op.dirname(__file__)

CONFIG = read_config('assign_config.yaml')
field = CONFIG['assignment_name']
df = get_minimal_df(CONFIG)

"""
# Get grade output with:
python ~/dev_trees/cfd2019/scripts/grade_oknb.py *.Rmd --cwd=$PWD > grade_output.txt
"""

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
