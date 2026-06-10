#!/usr/bin/env bash
# score_ft_heldout.sh — score the held-out-only fine-tuned eval CSVs in
# results/pareto_ft_heldout/ (compile + correctness + speedup + faithfulness).
#
# Self-contained + parallel so it can be launched fully detached:
#     caffeinate -i nohup bash scripts/score_ft_heldout.sh > /tmp/ho_master.log 2>&1 & disown
# Writes results/pareto_ft_heldout/<cell>_scored.csv, idempotent (skips done),
# and touches results/pareto_ft_heldout/SCORING_DONE on completion.
set -uo pipefail
cd "$(dirname "$0")/.."

JOBS="${JOBS:-6}"
RUNS="${RUNS:-10}"
PY="${PY:-/opt/homebrew/bin/python3}"

rm -f results/pareto_ft_heldout/SCORING_DONE
n=0
for raw in results/pareto_ft_heldout/*-ft_*.csv; do
  case "$raw" in *_scored.csv) continue ;; esac
  scored="${raw%.csv}_scored.csv"
  [ -f "$scored" ] && { echo "skip (scored) $(basename "$raw")"; continue; }
  b="$(basename "$raw" .csv)"
  strat="${b##*_}"                       # strategy = token after last underscore
  echo "start $(basename "$raw") (strategy=$strat)"
  "$PY" scripts/score_completions.py "$raw" --strategy "$strat" \
      --output "$scored" --runs "$RUNS" --faithfulness \
      > "${raw%.csv}.score.log" 2>&1 &
  n=$((n + 1))
  [ "$((n % JOBS))" -eq 0 ] && wait
done
wait
touch results/pareto_ft_heldout/SCORING_DONE
echo "ALL_HELDOUT_SCORING_DONE ($n cells)"
