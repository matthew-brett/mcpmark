""" Test scale_combine CLI routines
"""

from pathlib import Path

import numpy as np

from mcpmark.mcputils import MCPError
from mcpmark.cli import scale_combine as scb

import pytest

TEST_DATA_PATH = Path(__file__).parent / 'data'


def test_read_component():
    pre_1p0_pth = TEST_DATA_PATH / 'pre_1p0_format.csv'
    with pytest.raises(MCPError):
        scb.read_component_csv(pre_1p0_pth)
    post_1p0_pth = TEST_DATA_PATH / 'post_1p0_format.csv'
    post_1p0_df = scb.read_component_csv(post_1p0_pth)
    assert post_1p0_df.shape == (3, 10)
    assert list(post_1p0_df)[-1] == ('Total', '')
    assert np.all(post_1p0_df.iloc[:, :-1].sum(axis=1) == post_1p0_df.iloc[:, -1])
