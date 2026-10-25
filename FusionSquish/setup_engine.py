"""Run with system Python, never with Fusion's embedded Python."""
import json
from pathlib import Path
import subprocess
import sys
import venv


def main():
    if sys.version_info < (3, 12):
        raise RuntimeError('Zainstaluj Python 3.12 lub nowszy (zalecany 3.14) z python.org.')
    root = Path(__file__).resolve().parent
    environment = root / '.engine'
    venv.EnvBuilder(with_pip=True).create(environment)
    executable = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    subprocess.run([str(executable), '-m', 'pip', 'install', '--only-binary=:all:', '-r', str(root/'requirements.txt')], check=True)
    # A real solve catches native-library and API incompatibilities before registration.
    subprocess.run([str(executable), str(root/'engine'/'selftest.py')], check=True)
    (root/'config.json').write_text(json.dumps({'python': executable.relative_to(root).as_posix()}, indent=2), encoding='utf-8')
    print('\nGOTOWE. Dodaj folder FusionSquish w Fusion: Scripts and Add-Ins > Add-Ins > +.\n')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('\nINSTALACJA NIEUKOŃCZONA:', error, file=sys.stderr)
        sys.exit(1)
