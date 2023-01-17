""" Test grade_component
"""

from pathlib import Path

import numpy as np
import pandas as pd

from mcpmark.mcputils import component_path, MCPError
from mcpmark.cli import grade_component as gcp

import pytest

TEST_DATA_PATH = Path(__file__).parent / 'data'

COMP_AUTO = TEST_DATA_PATH / 'autograde.csv'


def test_grade_component(tmpdir):
    a_component = {'actual_max': 8, 'scaled_to': 15}
    config = dict(base_path=tmpdir,
                  components={'a_component': a_component},
                  student_id_col='gh_user',
                  components_path='components')
    comp_mark_path = Path(component_path(config, 'a_component')) / 'marking'
    comp_mark_path.mkdir(parents=True)
    auto_path = comp_mark_path / 'autograde.csv'
    auto_path.write_text(COMP_AUTO.read_text())
    auto_df = pd.read_csv(auto_path, index_col=0)
    df = gcp.grade_component(config, 'a_component')
    assert np.all(np.array(df) == np.array(auto_df)[:, :-1])
    df_col_labels = list(df)
    auto_col_labels = list(auto_df.drop(columns='Total'))
    assert df_col_labels == [('auto', L) for L in auto_col_labels]
    assert np.all(df.index == auto_df.index)
    # Presence of broken.csv is OK, if empty.
    broken_path = comp_mark_path / 'broken' / 'broken.csv'
    broken_path.parent.mkdir(parents=True)
    broken_path.write_text('')
    df = gcp.grade_component(config, 'a_component')
    assert np.all(np.array(df) == np.array(auto_df)[:, :-1])
    # Header but no data also OK.
    broken_header = f'{config["student_id_col"]},Mark\n'
    broken_path.write_text(broken_header)
    df = gcp.grade_component(config, 'a_component')
    assert np.all(np.array(df) == np.array(auto_df)[:, :-1])
    # But not OK where there are data.
    broken_path.write_text(broken_header + 'first_user,6\n')
    with pytest.raises(MCPError):
        df = gcp.grade_component(config, 'a_component')
