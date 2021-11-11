""" Tests for mcputils module
"""

import os.path as op
from argparse import ArgumentParser

import yaml

from mcpmark.mcputils import (get_notebooks, get_manual_scores, MCPError,
                              match_plot_scores, read_config,
                              proc_config, get_component_config)

import pytest

DATA_DIR = op.join(op.dirname(__file__), 'data')
EG_CONFIG_FNAME = op.join(DATA_DIR, 'assign_config.yaml')
EG_1C_CONFIG_FNAME = op.join(DATA_DIR, 'one_comp_config.yaml')


def touch(fname):
    with open(fname, 'wt') as fobj:
        fobj.write(' ')


def test_get_notebooks(tmp_path):

    def mp(fn):
        return op.join(tmp_path, fn)

    assert get_notebooks(tmp_path) == []
    touch(mp('foo.ipynb'))
    assert get_notebooks(tmp_path) == [mp('foo.ipynb')]
    touch(mp('foo.Rmd'))
    assert get_notebooks(tmp_path) == [mp('foo.Rmd'), mp('foo.ipynb')]
    assert get_notebooks(tmp_path, first_only=True) == [mp('foo.Rmd')]
    assert get_notebooks(tmp_path, lexts=('.ipynb',)) == [mp('foo.ipynb')]
    assert get_notebooks(tmp_path, lexts=('.rmd',)) == [mp('foo.Rmd')]
    assert (get_notebooks(tmp_path, lexts=('.ipynb', '.rmd')) ==
            [mp('foo.ipynb'), mp('foo.Rmd')])
    assert (get_notebooks(tmp_path, lexts=('.ipynb', '.rmd'), first_only=True)
            == [mp('foo.ipynb')])
    touch(mp('bar.Rmd'))
    assert (get_notebooks(tmp_path) ==
            [mp('bar.Rmd'), mp('foo.Rmd'), mp('foo.ipynb')])
    assert (get_notebooks(tmp_path, first_only=True) ==
            [mp('bar.Rmd'), mp('foo.Rmd')])
    touch(mp('baz.ipynb'))
    assert (get_notebooks(tmp_path) ==
            [mp('bar.Rmd'), mp('foo.Rmd'), mp('baz.ipynb'), mp('foo.ipynb')])
    assert (get_notebooks(tmp_path, first_only=True) ==
            [mp('bar.Rmd'), mp('foo.Rmd'), mp('baz.ipynb')])


def test_get_manual_scores():
    res = get_manual_scores('')
    assert res == {}
    res = get_manual_scores("""

## someone

Some text.

Several lines

    MCPScore : .4

## another_person

More text.

More lines.

 MCPScore   : 1
""")
    assert res == {'someone': 0.4, 'another_person': 1}
    res = get_manual_scores("""

## An_other_person

MCPScore : 0.05

## Who_now3

MCPScore : 1

""")
    # Missing final score.
    assert res == {'An_other_person': 0.05, 'Who_now3': 1.0}
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An_other_person

MCPScore : 0.05

## Who_now3

""")
    # Two scores.
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An_other_person

MCPScore : 0.05

MCPScore : 1

## Who_now3

MCPScore : 1

""")
    # Score prefix has wrong case - missing score.
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An_other_person

MCPscore : 0.05

## Who_now3

MCPScore : 1

""")
    # Name doesn't match
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An_other person

MCPScore : 0.05

## Who_now3

MCPScore : 1

""")


def test_match_plot_scores():
    scores = """Plot scores:
* complaints_pp : 1
* complaints_pc : 1
* complaints_pcp : 0
"""
    assert match_plot_scores(scores) == {
        'complaints_pp': 1,
        'complaints_pc': 1,
        'complaints_pcp': 0}
    scores = """Plot scores:
* complaints_pp : 0.1
* complaints_pcp : 3
"""
    assert match_plot_scores(scores) == {
        'complaints_pp': 0.1,
        'complaints_pcp': 3}


def test_read_config():
    config = read_config(EG_CONFIG_FNAME)
    assert config['assignment_name'] == 'An assignment name'
    assert config['student_id_col'] == 'SIS Login ID'
    # Check home directory gets expanded in paths.
    assert config['input_submission_path'] == op.expanduser(
        '~/Downloads/submissions_second')
    with open(EG_CONFIG_FNAME, 'rt') as fobj:
        raw_config = yaml.load(fobj, Loader=yaml.SafeLoader)
    c2 = proc_config(raw_config, EG_CONFIG_FNAME)
    assert c2['input_submission_path'] == op.expanduser(
        '~/Downloads/submissions_second')
    raw_config['student_id_col'] = 'some other col'
    canvas_csv = op.join('~', 'foo', 'bar.csv')
    raw_config['canvas_export_path'] = canvas_csv
    c3 = proc_config(raw_config, EG_CONFIG_FNAME)
    assert c3['student_id_col'] == 'some other col'
    # Check expansion of other fields.
    assert c3['canvas_export_path'] == op.expanduser(canvas_csv)
    # Check the default student id col.
    del raw_config['student_id_col']
    c4 = proc_config(raw_config, EG_CONFIG_FNAME)
    assert c4['student_id_col'] == 'SIS Login ID'


def test_more_config():
    config = read_config(EG_CONFIG_FNAME)
    pander_config = config['components']['pandering']
    assert pander_config['manual_qs'] == ['basic_sorting_6',
                                          'births_6',
                                          'cfpb_complaints_4']


def test_get_component_config():
    # Single component case.
    argv = ['--config-path', EG_1C_CONFIG_FNAME]
    args, config = get_component_config(ArgumentParser(), argv=argv)
    assert list(config['components']) == ['on_regression']
    assert args.component == 'on_regression'
    # Multiple component case, no component specified
    argv = ['--config-path', EG_CONFIG_FNAME]
    with pytest.raises(RuntimeError):
        args, config = get_component_config(ArgumentParser(), argv=argv)
    # Multiple component, component specified
    argv += ['pandering']
    args, config = get_component_config(ArgumentParser(), argv=argv)
    assert args.component == 'pandering'
    # Multiple component, component misspecified
    argv[-1] = 'not_pandering'
    with pytest.raises(RuntimeError):
        args, config = get_component_config(ArgumentParser(), argv=argv)
    # No component cases.
    for froot in ('no', 'empty', 'blank'):
        config_fname = op.join(DATA_DIR, f'{froot}_comp_config.yaml')
        argv = ['--config-path', config_fname]
        with pytest.raises(RuntimeError):
            args, config = get_component_config(ArgumentParser(), argv=argv)
