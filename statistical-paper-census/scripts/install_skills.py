#!/usr/bin/env python3
"""Install the three sibling skills without overwriting an existing installation."""
import argparse
import shutil
from pathlib import Path

NAMES = ('statistical-paper-census', 'ranked-mathlib-audit', 'statistical-census-html')
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, required=True, help='Agent skill directory')
    args = parser.parse_args()
    destination = args.dest.expanduser()
    conflicts = [name for name in NAMES if (destination / name).exists()]
    if conflicts:
        parser.error('Existing skills would be replaced: ' + ', '.join(conflicts))
    source = Path(__file__).resolve().parents[1] / 'skills'
    destination.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        shutil.copytree(source / name, destination / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print('Installed all three skills.')
if __name__ == '__main__':
    main()
