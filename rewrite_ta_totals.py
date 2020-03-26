#!/usr/bin/env python
"""
Reset totals for TA marks
"""

import os
import os.path as op

import numpy as np
import pandas as pd

spouses_dir = 'spouses_graded'
ta_dirs = os.listdir(spouses_dir)

# Rewrite totals
for ta in ta_dirs:
    pth = op.join(spouses_dir, ta, f'{ta}.csv')
    df = pd.read_csv(pth)
    df['Total'] = np.array(df.loc[:, 'Depth':'Based']).sum(axis=1)
    df.sort_values('Student').to_csv(pth, index=None)
