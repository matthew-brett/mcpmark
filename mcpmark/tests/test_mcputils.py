""" Tests for mcputils module
"""

import os.path as op

from mcpmark import (get_notebooks, get_manual_scores, MCPError,
                     match_plot_scores)

import pytest

DATA_DIR = op.join(op.dirname(__file__), 'data', 'assign_config.yaml')


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
