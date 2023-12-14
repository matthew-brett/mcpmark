""" rnbconv tests
"""

from pathlib import Path
from copy import deepcopy

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


def _read_test(pth):
    ws = {}
    exec(pth.read_text(), ws)
    test = ws.pop('test')
    assert list(ws) == ['__builtins__']
    return test


def test_test2testfile(tmp_path):
    in_test = {
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
    test_path = mcr.test2testfile(in_test, tmp_path)
    assert test_path.name == 'q1a.py'
    out_test = _read_test(test_path)
    # Test not modified.
    assert in_test == out_test


def test_t2f_none(tmp_path):
    # Test null points gets dropped.
    test_name = 'q_3_b'
    in_test = {
        'name': test_name,
        'points': None,
        'suites': [
            {'cases': [
                {'code': '>>> fruit_info["rank1"].dtype\n'
                 "dtype('int64')",
                 'hidden': False,
                 'locked': False},
                {'code': '>>> sorted(fruit_info["rank1"].dropna())\n'
                 '[1, 2, 3, 4]',
                 'hidden': False,
                 'locked': False}
            ],
            'scored': True,
            'setup': '',
            'teardown': '',
            'type': 'doctest'}
        ]}
    test_path = mcr.test2testfile(in_test, tmp_path)
    assert test_path.name == test_name + '.py'
    out_test = _read_test(test_path)
    # null points removed.
    assert 'points' not in out_test
    # Otherwise, as input.
    exp_test = deepcopy(in_test)
    exp_test.pop('points')
    assert exp_test == out_test
