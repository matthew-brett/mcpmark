#!/usr/bin/env python
"""
Reset totals for Spouses marks, write pooled.
"""

import os.path as op

import numpy as np
import pandas as pd

marking_pth = op.join('components_second', 'spouses', 'marking')
pth = op.join(marking_pth, 'parts.csv')

# Rewrite totals
df = pd.read_csv(pth)
df['Total'] = np.array(df.loc[:, 'Depth':'Based']).sum(axis=1)
df.sort_values('Student').to_csv(pth, index=None)
marks = dict(zip(df['Student'], df['Total']))

out_fname = op.join(marking_pth, 'component.csv')
with open(out_fname, 'wt') as fobj:
    fobj.write('SIS Login ID,Mark\n')
    for login in sorted(marks):
        fobj.write(f'{login},{marks[login]}\n')
