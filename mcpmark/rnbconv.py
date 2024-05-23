""" Convert Otter grader format to OKpy format
"""

import re
import io
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import yaml


class OtterError(Exception):
    """ Exceptions for Otter processing """


YAML_BLOCK = re.compile(
    r"""^---\s*$
    (.*?)
    ^---\s*$""",
    flags=re.VERBOSE | re.DOTALL | re.MULTILINE)


def read_header(contents):
    match = YAML_BLOCK.search(contents)
    if match is None:
        raise OtterError("Could not find header")
    yaml_text = match.groups()[0]
    return yaml.load(io.StringIO(yaml_text), Loader=yaml.SafeLoader)


def proc_tests(test_dict):
    out = deepcopy(test_dict)
    # Delete null points, accepting default.
    # https://otter-grader.readthedocs.io/en/latest/test_files/python_format.html
    if 'points' in out and out['points'] is None:
        out.pop('points')
    for suite in out.get('suites', []):
        for case in suite.get('cases', []):
            # Remove not-accepted keyword arg.
            case.pop('points', 0)
    return out


def test2testfile(test_dict, out_path):
    test_path = out_path / (test_dict['name'] + '.py')
    test_path.write_text('test = ' + pformat(proc_tests(test_dict)))
    return test_path


def proc_nb(contents, header):
    contents = strip_header(contents, header)
    return replace_otter(contents)


def strip_header(contents, header):
    if 'otter' in header['jupyter']:
        header = deepcopy(header)
        del header['jupyter']['otter']
    return YAML_BLOCK.sub(
        f"---\n{yaml.dump(header)}---\n",
        contents,
        count=1)


GRADER_RE = re.compile(
    r'''grader\s+=\s*otter\.Notebook\(["'](.*?)\.ipynb["']\)\s*$''',
    flags=re.MULTILINE)


def replace_otter(contents):
    contents = re.sub(
        r'^import otter\s*$',
        'from client.api.notebook import Notebook',
        contents,
        flags=re.MULTILINE)
    contents = GRADER_RE.sub(
        r'''ok = Notebook('\1.ok')''',
        contents)
    contents = re.sub(
        r'''grader\.check\(\s*["'](.*?)["']\s*\)\s*$''',
        r'''_ = ok.grade('\1')''',
        contents,
        flags=re.MULTILINE)
    contents = re.sub(
        r'''grader\.check_all\(\)\s*$''',
        """\
# For your convenience, you can run this cell to run all the tests at once!
import os
_ = [ok.grade(q[:-3]) for q in os.listdir("tests") if q.startswith('q')]""",
        contents,
        flags=re.MULTILINE)
    return contents.replace('Otter', 'OKpy')


def get_ok_contents(contents):
    ok_root = GRADER_RE.search(contents).groups()[0]
    return ok_root, f"""\
{{
  "name": "{ok_root}",
  "src": [
    "{ok_root}.ipynb"
  ],
  "tests": {{
      "tests/q*.py": "ok_test"
  }},
  "protocols": [
      "file_contents",
      "grading",
      "backup"
  ]
}}"""


def convert(nb_path, out_path, tests=True, ok=True):
    contents = nb_path.read_text()
    hdr = read_header(contents)
    out_nb_path = out_path / nb_path.name
    out_nb_path.write_text(proc_nb(contents, hdr))
    if tests:
        if not 'otter' in hdr['jupyter']:
            raise OtterError('No tests to write from {nb_path}')
        write_tests(hdr, out_path)
    if ok:
        write_ok(contents, out_path)


def write_tests(header, out_path):
    tests_path = out_path / 'tests'
    tests_path.mkdir(parents=True, exist_ok=True)
    (tests_path / '__init__.py').write_text('# Init tests')
    for _, test_dict in header['jupyter']['otter']['tests'].items():
        test2testfile(test_dict, tests_path)


def write_ok(contents, out_path):
    ok_root, ok_contents = get_ok_contents(contents)
    (out_path / (ok_root + '.ok')).write_text(ok_contents)


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('notebook_fnames', nargs='+',
                        help='Notebook filenames')
    parser.add_argument('-o', '--out-path',
                        help='Output directory (default is same as input)')
    parser.add_argument('-t', '--tests', action='store_true',
                        help='Write tests')
    parser.add_argument('-k', '--ok', action='store_true',
                        help='Write OK file')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    args.out_path = Path(args.out_path) if args.out_path else None
    for nb_fname in args.notebook_fnames:
        nb_path = Path(nb_fname)
        out_path = nb_path.parent if args.out_path is None else args.out_path
        convert(nb_path, out_path, tests=args.tests, ok=args.ok)


if __name__ == '__main__':
    main()
