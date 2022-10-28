""" Prepare feedback from assignment for upload to JupyterHub
"""

import os
import os.path as op
import shutil
from glob import glob
from functools import partial
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from nbconvert.preprocessors import ExecutePreprocessor

import jupytext

from rmdex.exerciser import make_solution
from ..mcputils import (execute_nb_fname, get_notebooks,
                        get_component_config,
                        component_path as get_component_path)


def clean_dir(start_path,
              bad_dir_func=lambda d : False,
              bad_fname_func=lambda f : False):
    for dirpath, dirnames, filenames in os.walk(start_path):
        for dn in dirnames:
            if bad_dir_func(dn):
                shutil.rmtree(op.join(dirpath, dn))
                dirnames.remove(dn)
        for fn in filenames:
            if bad_fname_func(fn):
                os.unlink(op.join(dirpath, fn))


def run_nb(nb_fname):
    nb_root, ext = op.splitext(nb_fname)
    out_nb_fname = nb_root + '.ipynb'
    nb = execute_nb_fname(nb_fname)
    jupytext.write(nb, out_nb_fname, fmt='ipynb')


def write_solution(nb_path, out_fname):
    in_nb_dir, in_nb_root = op.split(nb_path)
    out_dir = op.dirname(out_fname)
    component_dir, component_name = op.split(in_nb_dir)
    ok_root = component_name + '.ok'
    ok_out = op.join(out_dir, ok_root)
    if op.exists(ok_out):
        return
    ensure_dir(out_dir)
    # Copy ok file, csv files, tests, solution
    shutil.copyfile(op.join(in_nb_dir, ok_root), ok_out)
    shutil.copytree(op.join(in_nb_dir, 'tests'),
                    op.join(out_dir, 'tests'))
    solution_root = component_name + '_solution.ipynb'
    out_solution_fname = op.join(out_dir, solution_root)
    soln_nb = SOLUTION.solution_for_nb(nb_path)
    jupytext.write(soln_nb, out_solution_fname, fmt='ipynb')
    for fname in glob(op.join(in_nb_dir, '*.csv')):
        out_csv_fname = op.join(out_dir, op.basename(fname))
        shutil.copyfile(fname, out_csv_fname)


class Solution:

    def __init__(self, timeout=240):
        self._cache = {}
        self.timeout = timeout

    def solution_for_nb(self, nb_fname):
        dirname = op.dirname(op.realpath(nb_fname))
        if dirname in self._cache:
            return self._cache[dirname]
        comp_dir, component_name = op.split(dirname)
        ex_dir = op.dirname(comp_dir)
        model_dir = op.join(ex_dir,
                            'models',
                            component_name)
        tpl_fname = op.join(model_dir,
                            component_name + '_template.Rmd')
        soln_nb_str = make_solution(tpl_fname)
        soln_nb = jupytext.read(soln_nb_str, fmt='Rmd')
        ep = ExecutePreprocessor(timeout=self.timeout)
        ep.preprocess(soln_nb, {'metadata': {'path': model_dir}})
        self._cache[dirname] = soln_nb
        return soln_nb


SOLUTION = Solution()


def fb_path_maker(root_path, usuffix=''):

    def maker(fname):
        in_nb_dir, in_nb_root = op.split(fname)
        login_id, ext = op.splitext(in_nb_root)
        component_dir, component_name = op.split(in_nb_dir)
        jh_user = login_id + usuffix
        login_id, ext = op.splitext(in_nb_root)
        return op.join(root_path,
                       jh_user,
                       'marking',
                       component_name,
                       component_name + ext)

    return maker


def mod_path_maker(root_path):

    def maker(fname):
        in_nb_dir, in_nb_root = op.split(fname)
        login_id, ext = op.splitext(in_nb_root)
        component_dir, component_name = op.split(in_nb_dir)
        return op.join(root_path, component_name, login_id + ext)

    return maker


def write_component(component_path, pth_maker):
    nbs_written = []
    nbs = get_notebooks(component_path, lexts=('.rmd',))
    for nb_fname in nbs:
        out_nb_fname = pth_maker(nb_fname)
        write_solution(nb_fname, out_nb_fname)
        shutil.copyfile(nb_fname, out_nb_fname)
        run_nb(out_nb_fname)
        nbs_written.append(out_nb_fname)
    return nbs_written


def ensure_dir(dir_path, need_fresh=False, overwrite=False):
    """ Check directory exists, creating / overwiting if necessary

    Parameters
    ----------
    dir_path : str
        Directory name find / create.
    need_fresh : {False, True}, optional
        Whether directory must be newly created / empty (True) or can already
        exist (False).
    overwrite : {False, True}, optional
        If directory exists, and is not fresh, raise error with
        overwrite=False, otherwise create new empty directory.
    """
    if op.isdir(dir_path):
        if not need_fresh:
            return  # Directory present, contents irrelevant.
        if len(os.listdir(dir_path)) == 0:
            return  # Directory empty.
        if not overwrite:
            raise RuntimeError(f'Directory {dir_path} exists and is not '
                               'empty; specify `overwrite` to overwrite')
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)


def write_marking(component_path, out_nb_path):
    out_marking = op.join(out_nb_path, 'marking')
    if op.isdir(out_marking):
        shutil.rmtree(out_marking)
    shutil.copytree(op.join(component_path, 'marking'),
                    out_marking)


def clean_nb_dirs(nb_fnames):
    written_paths = set(op.dirname(fn) for fn in nb_fnames)
    for wp in written_paths:
        clean_dir(wp,
                  lambda d : d in ('__pycache__', '.ipynb_checkpoints'),
                  lambda f : (f == '.ok_storage' or
                              op.splitext(f)[1].lower() == '.rmd'))


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-p', '--out-path',
                        help='Path at which to write nb marking tree')
    parser.add_argument('-t', '--type', default='feedback',
                        help='"feedback" or "moderation"')
    parser.add_argument('--clobber', action='store_true',
                        help='Whether to overwrite "out_path"')
    return parser


def main():
    args, config = get_component_config(get_parser(),
                                        multi_component=True)
    usuffix = config.get('jh_user_suffix', '')
    type2func = {'feedback': partial(fb_path_maker,
                                     usuffix=usuffix),
                 'moderation': mod_path_maker}
    if not args.type in type2func:
        raise RuntimeError('type must be one of ' +
                           ', '.join(type2func))
    root_path = args.type if args.out_path is None else args.out_path
    ensure_dir(root_path, args.clobber, args.clobber)
    pth_maker = type2func[args.type](root_path)
    for component in config['components']:
        component_path = get_component_path(config, component)
        out_nbs = write_component(component_path, pth_maker)
        clean_nb_dirs(out_nbs)
        if args.type == 'moderation' and out_nbs:
            write_marking(component_path, op.dirname(out_nbs[-1]))


if __name__ == '__main__':
    main()
