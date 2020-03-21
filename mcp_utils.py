""" Utilities for marking components.
"""

import os
import os.path as op

import yaml
import numpy as np

from gradools import canvastools as ct


BAD_NAME_CHARS = '- '


def read_canvas(canvas_fname):
    required = ('ID', 'Student', 'SIS User ID', 'SIS Login ID', 'Section')
    dtypes = {'ID': int, 'SIS User ID': int}
    df = ct.to_minimal_df(canvas_fname, required, dtypes)
    return df.set_index('ID')


def read_config(config_fname):
    with open(config_fname, 'rt') as fobj:
        res = yaml.load(fobj)
    config_path = op.abspath(op.dirname(config_fname))
    for key, value in res.items():
        if not key.endswith('_path'):
            continue
        if not op.isabs(value):
            res[key] = op.join(config_path, value)
    return res


def get_minimal_df(config):
    df = read_canvas(config['canvas_export_path'])
    df[config['assignment_name']] = np.nan
    return df


def full2cv_name(full_name):
    """ Convert full name as in gradebook to Canvas compression """
    lower_parts = [p.lower() for p in full_name.split()]
    cv_name = ''.join([lower_parts[-1]] + lower_parts[:-1])
    for char in BAD_NAME_CHARS:
        cv_name = cv_name.replace(char, '')
    return cv_name


def full2cv_lookup(full_name, config):
    for k, v in config['cv_name_lookup'].items():
        if full_name in v:
            return k
    return full2cv_name(full_name)


def get_notebooks(in_dir, lexts=('.rmd', '.ipynb'), first_only=False):
    """ Return notebooks filenames from directory `in_dir`

    Parameters
    ----------
    in_dir : str
        Directory in which to do not-recursive search for notebooks.
    lexts : sequence, optional
        Filename extensions that identify notebooks, in lower case.  Order of
        extensions is order in which filenames will be returned.
    first_only : {False, True}, optional
        If False, return all notebooks matching `lexts` criterion.  If True,
        return only the first notebook matching the `lexts` criterion.

    Returns
    -------
    nb_fnames : list
        List of notebook filenames.
    """
    nbs = []
    for root, dirs, files in os.walk(in_dir):
        for fn in sorted(files):
            lext = op.splitext(fn)[1].lower()
            for candidate_lext in lexts:
                if lext == candidate_lext:
                    nbs.append(op.join(root, fn))
                    if first_only:
                        continue
    return nbs


def loginfn2login(fname):
    return op.splitext(op.basename(fname))[0]
