#!/usr/bin/env python
"""
Reset totals for TA marks, write pooled.
"""

import os
import os.path as op

import numpy as np
import pandas as pd

spouses_dir = 'spouses_graded'
ta_dirs = [p for p in os.listdir(spouses_dir)
           if op.isdir(op.join(spouses_dir, p))]

# Rewrite totals
logins = {}
for ta in ta_dirs:
    pth = op.join(spouses_dir, ta, f'{ta}.csv')
    df = pd.read_csv(pth)
    df['Total'] = np.array(df.loc[:, 'Depth':'Based']).sum(axis=1)
    df.sort_values('Student').to_csv(pth, index=None)
    logins.update(dict(zip(df['Student'], df['Total'])))

out_fname = op.join(spouses_dir, 'component.csv')
with open(out_fname, 'wt') as fobj:
    fobj.write('SIS Login ID,Mark\n')
    for login in sorted(logins):
        fobj.write(f'{login},{logins[login]}\n')
