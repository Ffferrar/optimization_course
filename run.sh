#!/usr/bin/env bash
set -e

CMD="$1"; shift || true

case "$CMD" in
  solve)
    python3 src/solver.py "$@"
    ;;
  check)
    python3 src/main.py "$@"
    ;;
  vis)
    python3 src/solver.py "$@"
    echo
    echo "Open tsp-visualizer-master/tsp-visualizer-master/index.html and paste the line above into Path"
    ;;
  *)
    echo "Usage:"
    echo "  ./run.sh solve <instance> [--seed 42] [--time-limit-sec 60]"
    echo "  ./run.sh check <files_or_dirs> [--time-limit SEC]"
    echo "  ./run.sh vis <instance> [--seed 42] [--time-limit-sec 60]"
    ;;
esac
