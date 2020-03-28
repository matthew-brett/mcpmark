""" Utilities for marking components.
"""

import os
import os.path as op
import re
import shutil

import yaml
import numpy as np
import pandas as pd
import nbformat.v4 as nbf
from nbconvert.preprocessors import ExecutePreprocessor
import jupytext

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


def nbs2markups(nb_fnames):
    """ Manual adjustments from notebook text
    """
    cg = CanvasGrader()
    markup_marks = {}
    for nb_fname in nb_fnames:
        login = loginfn2login(nb_fname)
        markups = cg.mark_markups(nb_fname)
        if len(markups) == 0:
            continue
        markup_marks[login] = sum(markups)
    return markup_marks


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



NAME_RE = re.compile(r'^##\s+([a-zA-Z0-9_]+)\s*$')
SCORE_RE = re.compile(r'\s*MCPScore\s*:\s*([0-9.]+)\s*$')
QUESTION_RE = re.compile(r'^(.*)_report\.md')


def get_manual_scores(contents, fname=None):
    """ Parse contents of markdown file from manual marking
    """
    scores = {}
    state = 'before'
    fname_label = '<unknown>' if fname is None else fname
    for line in contents.splitlines():
        if state == 'before':
            match = NAME_RE.search(line)
            if match is None:
                # Should be no further scores
                if SCORE_RE.search(line):
                    raise MCPError(
                        f'Multiple scores - see {line} in {fname_label}')
                continue
            state = 'find_score'
            name = match.groups()[0]
        elif state == 'find_score':
            match = SCORE_RE.search(line)
            if match is None:
                if NAME_RE.search(line):
                    raise MCPError(
                        f'Missing score at line {line} '
                        f'for {name} in {fname_label}')
                continue
            scores[name] = float(match.groups()[0])
            state = 'before'
    if state == 'find_score':
        raise MCPError(f'Missing score for {name} in {fname_label}')
    return scores


def read_manual(fname):
    """ Parse markdown file `fname` from manual marking
    """
    q_name = QUESTION_RE.match(op.basename(fname)).groups()[0]
    with open(fname, 'rt') as fobj:
        contents = fobj.read()
    return q_name, get_manual_scores(contents, fname)


def get_plot_nb(nb):
    """ Notebook with cells containing plots from `nb`

    Parameters
    ----------
    nb : dict
        Notebook.

    Returns
    -------
    plot_nb : dict
        Stripped notebook containing only plot outputs.
    """
    plot_nb = nbf.new_notebook()
    for cell in nb.cells:
        if not cell['cell_type'] == 'code':
            continue
        new_outputs = []
        for output in cell['outputs']:
            if output['output_type'] != 'display_data':
                continue
            if not 'data' in output:
                continue
            od = output['data']
            if not 'image/png' in od:
                continue
            no = nbf.new_output('display_data', od)
            new_outputs.append(no)
        if new_outputs:
            nc = nbf.new_code_cell()
            nc['outputs'] = new_outputs
            plot_nb.cells.append(nc)
    return plot_nb


PLOT_LINE = re.compile(r'^\*\s([0-9a-zA-Z_-]+)\s*:\s*([0-9.]+)')


def match_plot_scores(text):
    lines = [L.strip() for L in text.splitlines() if L.strip()]
    if not lines[0] == 'Plot scores:' or len(lines) < 2:
        return
    scores = {}
    for line in lines[1:]:
        m = PLOT_LINE.search(line)
        if not m:
            break
        key, value = m.groups()
        scores[key] = float(value)
    return scores


def get_plot_scores(nb_fname):
    """ Parse contents of notebook for plot scores.
    """
    nb = jupytext.read(nb_fname)
    scores = {}
    state = 'before'
    for cell in nb.cells:
        if not cell['cell_type'] == 'markdown':
            continue
        text = cell['source']
        if state == 'before':
            match = NAME_RE.search(text)
            if match is None:
                continue
            state = 'find_scores'
            name = match.groups()[0]
        elif state == 'find_scores':
            st_scores = match_plot_scores(text)
            if st_scores is None:
                continue
            scores[name] = st_scores
            state = 'before'
    if state == 'find_scores':
        raise MCPError(f'Missing scores for {name} in {nb_fname}')
    return scores


def execute_nb_fname(nb_fname):
    wd = op.dirname(nb_fname)
    storage_path = op.join(wd, '.ok_storage')
    if op.exists(storage_path):
        os.unlink(storage_path)
    nb = jupytext.read(nb_fname)
    ep = ExecutePreprocessor()
    ep.preprocess(nb, {'metadata': {'path': wd}})
    return nb


def component_path(config, component=None):
    pth = op.join(config['base_path'], config['components_path'])
    if component is not None:
        pth = op.join(pth, component)
    return pth


def dirs2logins(config):
    df = get_minimal_df(config)
    stid_col = config['student_id_col']
    d2L = {}
    for i_val, row in df.iterrows():
        cv_name = full2cv_lookup(row['Student'], config).capitalize()
        if cv_name not in config['known_missing']:
            d2L[cv_name] = row[stid_col]
    return d2L


def good_path(path):
    froot, ext = op.splitext(path)
    if ext in ('.md', '.ipynb', '.Rmd'):
        return False
    if path.startswith('.'):
        return False
    return True


def cp_with_dir(in_fname, out_fname):
    out_dir = op.dirname(out_fname)
    if not op.isdir(out_dir):
        os.makedirs(out_dir)
    shutil.copy(in_fname, out_fname)


def cp_model(model_path, component_path):
    for root, dirs, files in os.walk(model_path):
        dirs[:] = [d for d in dirs if good_path(d)]
        for fn in files:
            if not good_path(fn):
                continue
            full_path = op.join(root, fn)
            rel_path = op.relpath(full_path, model_path)
            cp_with_dir(full_path, op.join(component_path, rel_path))
