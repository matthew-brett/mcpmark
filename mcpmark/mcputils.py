""" Utilities for marking components.
"""

import os
import os.path as op
from pathlib import Path
import re
import shutil
from fnmatch import fnmatch
from functools import partial
from zipfile import ZipFile, BadZipFile

import yaml
import numpy as np
import pandas as pd
import nbformat.v4 as nbf
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors import CellExecutionError
import jupytext

from gradools import canvastools as ct
from rnbgrader.grader import CanvasGrader


BAD_NAME_CHARS = '- '


class MCPError(Exception):
    """ Class for MCP errors """


def read_config(config_fname):
    """ Read, process config file `config_fname`

    Parameters
    ----------
    config_fname : str
        Path for configuration file.

    Returns
    -------
    config : dict
        Configuration.
    """
    with open(config_fname, 'rt') as fobj:
        res = yaml.load(fobj, Loader=yaml.SafeLoader)
    return proc_config(res, config_fname)


def proc_config(config, config_fname):
    config_path = op.abspath(op.dirname(config_fname))
    res = config.copy()
    for key, value in config.items():
        if not key.endswith('_path'):
            continue
        # Allow home directory expansion.
        value = op.expanduser(value)
        if not op.isabs(value):
            value = op.join(config_path, value)
        res[key] = value
    # Directory containing config file.
    res['base_path'] = op.dirname(config_fname)
    return res


class SubmissionHandler:

    BAD_GLOBS = ['__pycache__', '__MACOSX', '.*']

    def __init__(self, config):
        self.config = config

    def get_minimal_df(self):
        df = self.read_student_data()
        df[self.config['assignment_name']] = np.nan
        return df

    def check_rename1(self, fname, out_path, component, df, clobber, known):
        student_id = self.get_student_id(fname, df)
        assert student_id not in known
        this_out = op.join(out_path, student_id, component)
        if op.isdir(this_out):
            if not clobber:
                raise RuntimeError(f'Directory "{this_out}" exists')
            shutil.rmtree(this_out)
        os.makedirs(this_out)
        # Copy notebook.
        out_fname = op.join(this_out, op.basename(fname))
        shutil.copy2(fname, out_fname)
        return out_fname

    def check_rename(self, fnames, out_path, component, df, clobber=False):
        known = set()
        for fname in fnames:
            out_dir = self.check_rename1(fname, out_path, component, df,
                                         clobber, known)
            print(f'Checked, renamed {fname} to {out_dir}')

    def check_unpack(self, fnames, out_path, df, clobber=False):
        known = set()
        for fname in fnames:
            out_dir = self.check_unpack1(fname, out_path, df, clobber, known)
            print(f'Unpacked {fname} to {out_dir}')

    def check_unpack1(self, fname, out_path, df, clobber, known):
        st_login = self.get_student_id(fname, df)
        assert st_login not in known
        this_out = op.join(out_path, st_login)
        if op.isdir(this_out):
            if not clobber:
                raise RuntimeError(f'Unpacking {fname} failed because '
                                   f'directory "{this_out}" exists')
            shutil.rmtree(this_out)
        os.makedirs(this_out)
        try:
            with ZipFile(fname, 'r') as zf:
                zf.extractall(path=this_out)
        except BadZipFile as e:
            raise RuntimeError(f"Could not extract from {fname} with error:\n"
                               f"{e}")
        # Clean extracted files.
        for root, dirs, files in os.walk(this_out):
            ok_dirs = []
            for d in dirs:
                if not any(fnmatch(d, g) for g in self.BAD_GLOBS):
                    ok_dirs.append(d)
                else:
                    shutil.rmtree(op.join(root, d))
            dirs[:] = ok_dirs
            for fn in files:
                if fn.startswith('.'):
                    os.unlink(op.join(root, fn))
        return this_out

    def login2jh(self, login):
        return login

    def login2uuid(self, login):
        return login


class CanvasHandler(SubmissionHandler):

    def get_student_id(self, fname, df=None):
        if self.config.get('anonymous'):
            name = Path(fname).name
            return name.split('_')[2 if name.startswith('LATE_') else 1]
        if isinstance(df, (None, str)):
            df = self.read_student_data(df)
        name1, name2, id_no = ct.fname2key(fname)
        assert name2 == ''
        return df.loc[int(id_no), self.config['student_id_col']]

    def read_student_data(self, fname=None):
        fname = self.config['canvas_export_path'] if fname is None else fname
        required = ('ID', 'Student', 'SIS User ID', 'SIS Login ID', 'Section')
        dtypes = {'ID': int, 'SIS User ID': int}
        df = ct.to_minimal_df(fname, required, dtypes)
        return df.set_index('ID')


def attend_fn2info(fname):
    froot = Path(fname).stem
    match = re.search(r'(.*)\s+\((.+\..+@lis\.ac\.uk)\)',
                        froot)
    if match is None:
        raise ValueError(f'{froot} does not match')
    return match.groups()


class AttendHandler(SubmissionHandler):

    def __init__(self, config):
        super().__init__(config)
        if not 'github_users_path' in config:
            raise ValueError('Need `github_users_path` in config')
        df = pd.read_csv(config['github_users_path'])
        self.gh_users = df.loc[:, ['Email', 'gh_user']]
        self._def_student_data = self.read_student_data()

    def get_student_id(self, fname, df=None):
        if df is None:
            df = self._def_student_data
        elif isinstance(df, str):
            df = self.read_student_data(df)
        name, email = attend_fn2info(fname)
        rows = df[df['Email'] == email]
        assert len(rows) == 1
        return rows.iloc[0][self.config['student_id_col']]

    def read_student_data(self, fname=None):
        fname = self.config['attendance_export_path'] if fname is None else fname
        required = ['StudentId', 'Forename', 'Surname', 'Email',
                    'school_user', 'gh_user']
        df = pd.read_excel(fname)
        dtypes = {'StudentId': int}
        for name, dt in dtypes.items():
            df[name] = df[name].astype(dt)
        df['school_user'] = df['Email'].str.split('@').apply(lambda v : v[0])
        df = df.merge(self.gh_users, on='Email', how='left')
        missing = df['gh_user'].isna()
        if np.any(missing):
            raise ValueError('Missing gh_user for ' +
                             ', '.join(df.loc[missing, 'Email']))
        return df[required].set_index('StudentId')

    def login2jh(self, login):
        return login.lower().replace('-', '-2d')

    def login2uuid(self, login):
        df = self._def_student_data
        login_col = self.config['student_id_col']
        rows = df[df[login_col] == login]
        if len(rows) == 0:
            raise ValueError(f'No rows for login {login}')
        if len(rows) > 1:
            raise ValueError(f'More than one row for login {login}')
        return str(rows.iloc[0].name)


class CsvHandler(SubmissionHandler):

    def get_student_id(self, fname, df=None):
        """ Work out student ID from given filename
        """
        if isinstance(df, (None, str)):
            df = self.read_student_data(df)
        name, email = attend_fn2info(fname)
        rows = df[df['Email'] == email]
        assert len(rows) == 1
        return rows.iloc[0][self.config['student_id_col']]

    def read_student_data(self, fname=None):
        fname = self.config['user_csv_path'] if fname is None else fname
        required = ['Name', 'Email', 'school_user', 'gh_user']
        df = pd.read_csv(fname, comment='#')
        df['school_user'] = df['Email'].str.split('@').apply(lambda v : v[0])
        missing = df['gh_user'].isna()
        if np.any(missing):
            raise ValueError('Missing gh_user for ' +
                             ', '.join(df.loc[missing, 'Email']))
        return df[required].set_index('gh_user', drop=False)

    def login2jh(self, login):
        return login.lower().replace('-', '-2d')


def make_submission_handler(config):
    if 'canvas_export_path' in config:
        return CanvasHandler(config)
    elif 'attendance_export_path' in config:
        return AttendHandler(config)
    elif 'user_csv_path' in config:
        return CsvHandler(config)
    else:
        raise ValueError('No Canvas or Attendance path')


def get_minimal_df(config):
    return make_submission_handler(config).get_minimal_df()


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
        dirs[:] = [d for d in dirs if d != '.ipynb_checkpoints']
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

    parts = re.split(r'^(\w+_.*\.Rmd)$', output, flags=re.M)
    if parts[0].strip() == '':
        parts.pop(0)

    rows = []
    for i in range(0, len(parts), 2):
        fname = parts[i]
        result = parts[i + 1]
        assert fname.endswith('.Rmd')
        assert len(result)
        total_match = re.search(r'^Total: (\d+)$', result, flags=re.M)
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

    Markups are lines beginning "#M: " followed by a floating point number or
    integer.  This functions sums these numbers.  Postive numbers to add marks.
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



NAME_RE = re.compile(r'^##\s+([a-zA-Z0-9_-]+)\s*$')
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


def execute_nb_fname(nb_fname, timeout=240, verbose=True):
    wd = op.dirname(nb_fname)
    storage_path = op.join(wd, '.ok_storage')
    if op.exists(storage_path):
        os.unlink(storage_path)
    nb = jupytext.read(nb_fname)
    ep = ExecutePreprocessor(timeout=timeout)
    if verbose:
        print(f'Executing {nb_fname}')
    try:
        ep.preprocess(nb, {'metadata': {'path': wd}})
    except CellExecutionError as e:
        # ename, evalue became required parameters at some point
        # after nbconvert 5.6.1, is true of 6.0.7.
        args = (e.ename, e.evalue) if hasattr(e, 'ename') else ()
        raise e.__class__(f'{e.traceback}\nError in {nb_fname}', *args)
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


def get_component_config(parser,
                         def_config='assign_config.yaml',
                         argv=None,
                         multi_component=False,
                         component_default='error',
                         component_as_option=False):
    """ Use `parser` to collect config and component name

    Add "component" and "--config-path" arguments to parser, parse arguments.
    By default, return the only component name if none specified.

    Parameters
    ----------
    parser : :class:`ArgumentParser` object
        Command line argument parser.
    def_config : str, optional
        Default filename for configuration file.
    argv : sequence, optional
        Command line arguments.  Default of None uses ``sys.argv``.
    multi_components : {False, True}, optional
        If False, ``component`` argument can be not-specified, or a single
        component, and `args.component` will be a scalar.  If True,
        specify 0 or more ``component`` arguments, and ``args.component`` will
        be a list.
    component_default : {'error', 'all'}, optional
        Applies only if "component" argument not specified, and multiple
        components exist.  In that case, and this set to `error`, then raise a
        ``ValueError``.   If `all`, set components arg to be all components.
    component_as_option : {False, True}, optional
        If True add ``component`` parameter as positional argument, otherwise,
        add as option.

    Returns
    -------
    args : object
        Parsed command line parameters. By default, set `args.component` to the
        only component name if none specified.
    config : dict
        Configuration as read from default or specified `config_path`.
    """
    if not component_default in ('all', 'error'):
        raise ValueError(
            "component_default should be one of 'all', 'error'")
    comp_nargs, comp_msg, comp_suff = (
        ('*', 'one or more components', 's') if multi_component else
        ('?', 'component', ''))
    parser.add_argument(('--' if component_as_option else '') + 'component',
                        nargs=comp_nargs,
                        help='Component name')
    parser.add_argument('--config-path',
                        default=op.join(os.getcwd(), def_config),
                        help='Path to config file')
    args = parser.parse_args(argv)
    config = read_config(args.config_path)
    if ('components' not in config or
        config['components'] is None or
        len(config['components']) == 0):
        raise ValueError('No components in config')
    comp_names = list(config['components'])
    if not args.component:
        comp_err = f'Specify {comp_msg} from: ' + ', '.join(comp_names)
        if not multi_component:
            if len(comp_names) > 1:
                raise ValueError(comp_err)
            args.component = comp_names[0]
        else:  # multi_component case
            if component_default == 'all':
                args.component = comp_names
            elif component_default == 'error':
                raise ValueError(comp_err)
            else:
                raise ValueError('component_default should be "error" or "all"')
    else:
        to_test = set(args.component) if multi_component else {args.component}
        if to_test.difference(comp_names):
            raise ValueError(
                f'Component{comp_suff} "{args.component}" must be in ' +
                ', '.join(comp_names))
    return args, config


def has_md_text(nb, cell_regex, flags=None):
    """ True if notebook `nb` has Markdown text matching `cell_regex`
    """
    flags = re.I if flags is None else flags
    if not hasattr(cell_regex, 'pattern'):
        cell_regex = re.compile(cell_regex, flags=flags)
    for cell in nb.cells:
        if cell['cell_type'] != 'markdown' or not 'source' in cell:
            continue
        if cell_regex.search(cell['source'].lower()):
            return True
    return False


def has_md_text_component(nb, nb_path, cell_regex, flags=None):
    return nb_path if has_md_text(nb, cell_regex) else None


def has_md_checker(cell_regex, flags=None):
    return partial(has_md_text_component, cell_regex=cell_regex)
