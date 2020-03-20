""" Tests for notebook components
"""

import re

from functools import partial


def find_md_cell(nb, nb_fname, cell_regex=None):
    for cell in nb.cells:
        if cell['cell_type'] != 'markdown' or not 'source' in cell:
            continue
        text = cell['source']
        regex = re.compile(cell_regex, re.I)
        if regex.search(text.lower()):
            return nb_fname


test_lymphoma = partial(find_md_cell, cell_regex=r'#\s*A cure for cancer?')
test_pandering = partial(find_md_cell,
                         cell_regex=r'#\s*Walking the Pandas walk')
test_religion = partial(find_md_cell,
                        cell_regex=r'#\s*Is religion a good thing?')
test_titanic = partial(find_md_cell,
                        cell_regex=r'#\s*Women and children first?')
test_spouses = partial(find_md_cell, cell_regex=r'#\s*Spouses,\s*Baggage')


COMPONENT_TESTS = {
    'lymphoma': test_lymphoma,
    'pandering': test_pandering,
    'religion': test_religion,
    'titanic': test_titanic,
    'spouses': test_spouses,
}
