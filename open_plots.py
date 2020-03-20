""" Script to open notebooks one by one in browser
"""

import os.path as op
from glob import glob
from subprocess import check_call

PLOT_NB_DIR = 'plot_nbs'

nbs = glob(op.join(PLOT_NB_DIR, '*.ipynb'))
port = 8888

for nb in nbs:
    check_call(
        ['open', f'http://localhost:{port}/notebooks/{nb}'])
    res = input('Press return')
    if res:
        break
