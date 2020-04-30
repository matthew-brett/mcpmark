""" Tools for grading multiple notebook component exercises.
"""

__version__ = '0.1a1'

from .mcputils import (get_notebooks, get_manual_scores, MCPError,
                       match_plot_scores, read_config, execute_nb_fname)
