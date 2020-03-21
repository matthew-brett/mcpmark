""" Tests for mcp_utils module
"""

import os.path as op
import sys

HERE = op.realpath(op.dirname(__file__))
sys.path.append(op.join(HERE, '..'))

from mcp_utils import get_notebooks

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
