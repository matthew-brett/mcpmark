""" Utilities for marking components.
"""

import os
import os.path as op
import re

import yaml
import numpy as np
import pandas as pd

from gradools import canvastools as ct
from rnbgrader.grader import CanvasGrader


BAD_NAME_CHARS = '- '


class MCPError(Exception):
    """ Class for MCP errors """ 


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
    # Directory containing config file.
    res['base_path'] = op.dirname(config_fname)
    # Defaults
    res['student_id_col'] = res.get('student_id_col', "SIS Login ID")
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




def get_notebooks(in_dir,
                  lexts=('.rmd', '.ipynb'),
                  first_only=False,
                  recursive=False):
    """ Return notebooks filenames from directory `in_dir`

    Parameters
    ----------
    in_dir : str
        Directory in which to search for notebooks.
    lexts : sequence, optional
        Filename extensions that identify notebooks, in lower case.  Order of
        extensions is order in which filenames will be returned.
    first_only : {False, True}, optional
        If False, return all notebooks matching `lexts` criterion.  If True,
        return only the first notebook matching the `lexts` criterion.
    recursive : {False, True}, optional
        Whether to do recursive search in `in_dir`.

    Returns
    -------
    nb_fnames : list
        List of notebook filenames.  If `first_only` is False, then return all
        notebooks with the first extension in `lexts`, followed by all
        notebooks with the second extension in `lexts`, etc.  Within extension
        group, the filenames will be sorted.
    """
    nbs = []
    found = set()
    for root, dirs, files in os.walk(in_dir):
        if not recursive:
            dirs[:] = []
        fnames = [op.join(root, fn) for fn in sorted(files)]
        if len(fnames) == 0:
            continue
        froots, exts = list(zip(*[op.splitext(fn) for fn in fnames]))
        fn_lexts = [e.lower() for e in exts]
        for candidate_lext in lexts:
            for (froot, fn_lext, fn) in zip(froots, fn_lexts, fnames):
                if first_only and froot in found:
                    continue
                if fn_lext == candidate_lext:
                    nbs.append(fn)
                    found.add(froot)
    return nbs


def loginfn2login(fname):
    return op.splitext(op.basename(fname))[0]


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


def nbs_to_markups(nb_fnames):
    """ Manual adjustments from notebook text
    """
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


def _check_total(line, name, marks, required_fields, msg_lines):
    missing = set(required_fields).difference(marks)
    if len(missing):
        msg_lines.append("Required field{} {} not present".format(
            's' if len(missing) > 1 else '',
            ', '.join(sorted(missing))))
    actual_total = sum(marks.values())
    if not line.lower().startswith('total'):
        msg_lines.append("Expecting total {} for {}".format(
            actual_total, name))
        return
    total = float(line.split(':')[1])
    if not total == sum(marks.values()):
        msg_lines.append("Expected {} for {}, got {}".format(
            actual_total, name, total))



NAME_RE = re.compile(r'^##\s+(.*)\s*$')
SCORE_RE = re.compile(r'\s*MCPScore\s*:\s*([0-9.]+)\s*$')
QUESTION_RE = re.compile(r'^(.*)_report\.md')


def get_manual_scores(contents):
    """ Parse contents of markdown file from manual marking
    """
    scores = {}
    state = 'before'
    for line in contents.splitlines():
        if state == 'before':
            match = NAME_RE.search(line)
            if match is None:
                # Should be no further scores
                if SCORE_RE.search(line):
                    raise MCPError(f'Multiple scores - see {line}')
                continue
            state = 'find_score'
            name = match.groups()[0]
        elif state == 'find_score':
            match = SCORE_RE.search(line)
            if match is None:
                if NAME_RE.search(line):
                    raise MCPError(f'Missing score for {name}')
                continue
            scores[name] = float(match.groups()[0])
            state = 'before'
    if state == 'find_score':
        raise MCPError(f'Missing score for {name}')
    return scores


def read_manual(fname):
    """ Parse markdown file `fname` from manual marking
    """
    q_name = QUESTION_RE.match(op.basename(fname)).groups()[0]
    with open(fname, 'rt') as fobj:
        contents = fobj.read()
    return q_name, get_manual_scores(contents)
