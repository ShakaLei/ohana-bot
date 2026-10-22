#!/bin/bash
# build.sh — totem-web. Derives the page from the untouched 3D source,
# syntax-gates everything, then reports.
set -u
cd "$(dirname "$0")"
python3 -m py_compile serve.py brain.py canned.py tts.py demo_script.py prerender.py ladder.py test_ladder.py || {
  echo 'PYTHON SYNTAX ERROR — not building'; exit 2; }
python3 src/build-page.py || exit $?
ls -la dist/
