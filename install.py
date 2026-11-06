"""Install all five skills without replacing existing skills. Python 3.10+."""
import argparse
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, default=Path.home()/'.agents'/'skills')
    parser.add_argument('--check', action='store_true', help='Show plan only')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent/'skills'
    folders = sorted(source.iterdir())
    if len(folders) != 5 or not all((p/'SKILL.md').is_file() for p in folders):
        raise ValueError('Incomplete package: expected five full skill folders')
    dest = args.dest.expanduser().resolve()
    conflicts = [p.name for p in folders if (dest/p.name).exists() or (dest/p.name).is_symlink()]
    if conflicts:
        raise ValueError('Existing skills left unchanged; compare before updating: '+', '.join(conflicts))
    if dest == source or source in dest.parents:
        raise ValueError('Installation destination must be outside the package skills folder')
    print(f'Install destination: {dest}')
    for folder in folders:
        print(folder.name)
    if not args.check:
        dest.mkdir(parents=True, exist_ok=True)
        for folder in folders:
            shutil.copytree(folder, dest/folder.name, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        print('Copied five skills. Open a new Codex chat and verify their actual paths.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
