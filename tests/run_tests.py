"""Recette complète, avec isolation des suites et sans dépendance Python externe."""
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    node = shutil.which('node')
    if not node:
        print('Recette impossible : Node.js est requis pour les tests JavaScript.', flush=True)
        return 2
    suites = [
        ('Lanceur de recette', [sys.executable, '-u', 'tests/test_runner.py']),
        ('Cœur Packet Tracer', [sys.executable, '-u', 'tests/test_all.py']),
        ('Ateliers', [sys.executable, '-u', 'tests/test_workshops.py']),
        ('Web Python', [sys.executable, '-m', 'unittest', 'discover', '-s', 'web', '-p', 'test_*.py']),
    ]
    suites.extend((path.name, [node, str(path)])
                  for path in sorted((ROOT / 'web').glob('test_*.js')))
    failures = []
    for name, command in suites:
        print('\nSuite : ' + name, flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT, check=False)
        except OSError as error:
            print(str(error), flush=True)
            failures.append(name)
            continue
        if result.returncode:
            failures.append(name)
    if failures:
        print('\nÉCHEC : ' + ', '.join(failures), flush=True)
        return 1
    print('\nToutes les suites sont vertes. Validation PT réelle toujours nécessaire.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
