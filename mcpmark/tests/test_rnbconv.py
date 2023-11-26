""" rnbconv tests
"""

from pathlib import Path

DATA_PATH = Path(__file__).parent / 'data'
IN_NB_PATH = DATA_PATH / 'eg_otter.Rmd'

from mcpmark import rnbconv as mcr

import pytest


def test_header(tmp_path):
    contents =  IN_NB_PATH.read_text()
    hdr = mcr.read_header(contents)
    assert hdr['jupyter']['otter']['OK_FORMAT']
    tests = hdr['jupyter']['otter']['tests']
    assert len(tests) == 20
    assert hdr['jupyter']['otter']['OK_FORMAT']
    with pytest.raises(mcr.OtterError):
        mcr.read_header("Some text")


def test_test2testfile(tmp_path):
    test = {
        'name': 'q1a',
        'points': 1,
        'suites': [
          {'cases': [
           {'code': '>>> is_bid_unique or ~is_bid_unique\nTrue',
            'hidden': False,
            'locked': False}],
          'scored': True,
          'setup': '',
          'teardown': '',
          'type': 'doctest'}
        ]
    }
    test_path = mcr.test2testfile(test, tmp_path)
    assert test_path.name == 'q1a.py'
    ws = {}
    exec(test_path.read_text(), ws)
    assert 'test' in ws
