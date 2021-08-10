#!/usr/bin/env sh

pip install --user coverage -U
pip install --user memory_profiler -U

coverage run -m unittest discover || exit 1
coverage xml -i || exit 1

[ -f coverage.xml ] || exit 1
