import os.path as op
from glob import glob

import pandas as pd
import nbformat.v4 as nbf
from nbconvert.preprocessors.execute import executenb

import jupytext

from gradools import canvastools as ct


def plot_marks(plot_nb_fnames):
    end_cell = nbf.new_code_cell('for mark in plot_marks:\n    print(mark)')
    rows = []
    for nb_fname in plot_nb_fnames:
        nb = jupytext.read(nb_fname)
        nb['cells'].append(end_cell)
        print('Executing', nb_fname)
        exe_nb = executenb(nb)
        mark_strs = exe_nb['cells'][-1]['outputs'][0]['text'].split('\n')
        marks = [int(m) for m in mark_strs if m][:3]
        name, _, stid = ct.fname2key(nb_fname)
        rows.append([int(stid), name, sum(marks)])
    df = pd.DataFrame(data=rows, columns=['ID', 'Student', 'Mark'])
    return df.set_index('ID')


pmarks = plot_marks(sorted(glob(op.join('plot_nbs', '*.ipynb'))))
pmarks.to_csv('plot_marks.csv')
