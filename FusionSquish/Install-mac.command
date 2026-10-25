#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
python3 setup_engine.py
result=$?
printf '\nNaciśnij Enter, aby zamknąć.\n'
read answer
exit $result
