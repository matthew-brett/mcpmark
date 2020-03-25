""" Tests for mcp_utils module
"""

import os.path as op
import sys

HERE = op.realpath(op.dirname(__file__))
sys.path.append(op.join(HERE, '..'))

from mcp_utils import (get_notebooks, get_manual_scores, MCPError,
                       match_plot_scores)

import pytest


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

## another person

More text.

More lines.

 MCPScore   : 1
""")
    assert res == {'someone': 0.4, 'another person': 1}
    res = get_manual_scores("""

## An other person

MCPScore : 0.05

## Who now?

MCPScore : 1

""")
    # Missing final score.
    assert res == {'An other person': 0.05, 'Who now?': 1.0}
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An other person

MCPScore : 0.05

## Who now?

""")
    # Two scores.
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An other person

MCPScore : 0.05

MCPScore : 1

## Who now?

MCPScore : 1

""")
    # Score prefix has wrong case - missing score.
    with pytest.raises(MCPError):
        res = get_manual_scores("""

## An other person

MCPscore : 0.05

## Who now?

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
