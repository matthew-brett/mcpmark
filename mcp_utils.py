""" Utilities for marking components.
"""

import os.path as op

import yaml
import numpy as np

from gradools import canvastools as ct


def read_canvas(canvas_fname):
    required = ('ID', 'Student', 'SIS User ID', 'SIS Login ID', 'Section')
    dtypes = {'ID': int, 'SIS User ID': int}
    df = ct.to_minimal_df(canvas_fname, required, dtypes)
    return df.set_index('ID')


def read_config(config_fname):
    with open(config_fname, 'rt') as fobj:
        res = yaml.load(fobj)
    config_path = op.abspath(op.dirname(config_fname))
    res['canvas_export'] = op.join(config_path, res['canvas_export'])
    return res


def get_minimal_df(config):
    df = read_canvas(config['canvas_export'])
    df[config['assignment_name']] = np.nan
    return df
