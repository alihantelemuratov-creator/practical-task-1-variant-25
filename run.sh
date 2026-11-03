#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
case "${1:-repl}" in
  repl) python3 -m src.model_repl ;;
  server) python3 -m src.server ;;
  demo) python3 -m src.demo ;;
  web) python3 -m src.web ;;
  mbt) python3 -m pytest -q tests/test_mbt_rpc.py ;;
  coverage)
    python3 -m coverage erase
    python3 -m coverage run --branch -m pytest -q tests/test_mbt_rpc.py
    python3 -m coverage report -m --include='src/*'
    python3 -m coverage html --include='src/*'
    ;;
  test) python3 -m pytest -q ;;
  *) echo "Usage: run.sh [repl|server|demo|web|mbt|coverage|test]" >&2; exit 2 ;;
esac
