""" Run grading

First see prepare_grading.py
"""

import os.path as op

from subprocess import check_output

CFD2019 = op.expanduser(op.join('~', 'dev_trees', 'cfd2019'))
CFD_SCRIPTS = op.join(CFD2019, 'scripts')

# Build plot notebooks


