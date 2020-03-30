#!/usr/bin/env python
""" Print duplicate files
"""

import sys
from hashlib import sha1
from collections import defaultdict


def shasum(fname):
    with open(fname, 'rb') as fobj:
        return sha1(fobj.read()).hexdigest()


def main():
    duplicates = defaultdict(list)
    for fn in sys.argv[1:]:
        sha = shasum(fn)
        duplicates[sha].append(fn)
    clusters = [(k, v) for k, v in duplicates.items() if len(v) > 1]
    for key, cluster in clusters:
        print(f'Cluster {key[:7]}:')
        print('  ' + '\n  '.join(cluster))


if __name__ == '__main__':
    main()
