#!/usr/bin/env bash
# score_pareto_sweep.sh — score every raw Modal CSV in results/pareto/
# into <name>_scored.csv with compile + correctness + speedup + faithfulness.
#
# Idempotent: skips CSVs that already have a scored counterpart.
# Parallel: runs up to $JOBS scorings concurrently (default 4).
#
# Usage:
#   bash scripts/score_pareto_sweep.sh           # default JOBS=4, runs=10
#   JOBS=8 RUNS=3 bash scripts/score_pareto_sweep.sh   # faster, less precise
set -euo pipefail
cd "$(dirname "$0")/.."

JOBS="${JOBS:-4}"
RUNS="${RUNS:-10}"

shopt -s nullglob
raw_csvs=(results/pareto/*.csv)
if [ ${#raw_csvs[@]} -eq 0 ]; then
  echo "No raw CSVs found under results/pareto/" >&2
  exit 1
fi

to_score=()
for raw in "${raw_csvs[@]}"; do
  case "$raw" in
    *_scored.csv) continue ;;
    *.submit.log) continue ;;
    *.errors.csv) continue ;;
  esac
  scored="${raw%.csv}_scored.csv"
  [ -f "$scored" ] && { echo "skip (already scored) $raw"; continue; }
  to_score+=("$raw")
done

echo "Scoring ${#to_score[@]} CSVs with $JOBS parallel workers (runs=$RUNS)..."
echo

active=0
for raw in "${to_score[@]}"; do
  scored="${raw%.csv}_scored.csv"
  log="${raw%.csv}.score.log"
  echo "  start  $(basename "$raw")"
  python3 scripts/score_completions.py "$raw" \
      --output "$scored" --runs "$RUNS" --faithfulness \
      > "$log" 2>&1 &
  active=$((active+1))
  if [ "$active" -ge "$JOBS" ]; then
    wait -n
    active=$((active-1))
  fi
done
wait

echo
echo "All scoring done. Outputs in results/pareto/*_scored.csv"
echo
echo "Next: faithfulness 2x2 report"
echo "  python3 faithfulness/report_2x2.py results/pareto/*_scored.csv --out results/aggregate_2x2/"
