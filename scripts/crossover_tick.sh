#!/usr/bin/env bash
# crossover_tick.sh — idempotently advance the in-dist epoch-sweep crossover.
#
# For each of the 8 epoch variants it, in order of readiness:
#   1. launches the eval on Modal (survivable orchestrator) once the variant's
#      MERGED weights (safetensors, not just config.json) exist on pdob-finetuned;
#   2. pulls the eval CSV from pdob-results, filters to in-dist(79)+OOD(HO-*),
#      and launches Modal scoring once the eval exists;
#   3. pulls the scored CSV back from pdob-results.
# When all 8 scored CSVs are present it runs epoch_crossover.py (pass1+faithful).
#
# Safe to run every few minutes — marker files prevent double-launching, and
# every launched job is `--detach` so it survives this script (and the turn)
# ending. Just re-run to advance.
set -uo pipefail
cd "$(dirname "$0")/.."
MODAL="${MODAL:-$HOME/.local/bin/modal}"
PY="${PY:-/opt/homebrew/bin/python3}"
M=results/pareto_ft_indist; mkdir -p "$M"
INDIST=fine_tune/heldout_indist_variants.txt

VARIANTS="qwen2.5-coder-1.5b-indist-ep1-ft qwen2.5-coder-1.5b-indist-ep3-ft \
qwen2.5-coder-1.5b-indist-ep6-ft qwen2.5-coder-1.5b-indist-ep10-ft \
r1-distill-qwen-7b-indist-ep1-ft r1-distill-qwen-7b-indist-ep3-ft \
r1-distill-qwen-7b-indist-ep6-ft r1-distill-qwen-7b-indist-ep10-ft"

# one listing of what's already on the results volume (eval + scored CSVs)
VOL=$("$MODAL" volume ls pdob-results 2>/dev/null | grep -oE "[a-z0-9.-]+_pattern-aware(_scored)?.csv" || true)

nonempty() {  # rows with non-empty raw_output
  "$PY" -c "import csv,sys;csv.field_size_limit(sys.maxsize);print(sum(1 for r in csv.DictReader(open('$1',newline='')) if (r.get('raw_output') or '').strip()))" 2>/dev/null || echo 0
}

for v in $VARIANTS; do
  raw="results/pareto/${v}_pattern-aware.csv"
  filt="$M/${v}_pattern-aware.csv"
  scored="$M/${v}_pattern-aware_scored.csv"

  # already fully scored locally?
  [ -f "$scored" ] && { echo "DONE    $v"; continue; }

  # scored CSV waiting on the volume? pull it and finish.
  if echo "$VOL" | grep -qx "${v}_pattern-aware_scored.csv"; then
    "$MODAL" volume get --force pdob-results "${v}_pattern-aware_scored.csv" "$scored" >/dev/null 2>&1 \
      && { echo "PULLED  $v (scored)"; continue; }
  fi

  # do we have the eval CSV (local non-empty, or on the volume)?
  rows=0; [ -f "$raw" ] && rows=$(nonempty "$raw")
  if [ "${rows:-0}" -eq 0 ] && echo "$VOL" | grep -qx "${v}_pattern-aware.csv"; then
    "$MODAL" volume get --force pdob-results "${v}_pattern-aware.csv" "$raw" >/dev/null 2>&1
    rows=$(nonempty "$raw")
  fi

  if [ "${rows:-0}" -gt 0 ]; then
    # have eval -> filter + launch scoring once
    if [ ! -f "$M/.score_${v}" ]; then
      "$PY" - "$raw" "$filt" "$INDIST" <<'PYEOF'
import csv, sys
csv.field_size_limit(sys.maxsize)
raw, filt, idf = sys.argv[1], sys.argv[2], sys.argv[3]
indist = set(open(idf).read().split())
rows = list(csv.DictReader(open(raw, newline="")))
keep = [r for r in rows if r.get("variant_id","") in indist or r.get("pattern_id","").startswith("HO-")]
with open(filt, "w", newline="") as wf:
    w = csv.DictWriter(wf, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(keep)
print(f"  filtered -> {len(keep)} rows")
PYEOF
      "$MODAL" run --detach modal_app/score_modal.py --glob-pattern "$filt" \
        > "$M/.scorelog_${v}" 2>&1 & disown
      touch "$M/.score_${v}"
      echo "SCORE   $v (launched, eval rows=$rows)"
    else
      echo "SCORING $v (in flight)"
    fi
    continue
  fi

  # no eval yet -> launch it once the merged weights are present
  has_w=$("$MODAL" volume ls pdob-finetuned "$v" 2>/dev/null | grep -cE "safetensors" || true)
  if [ "${has_w:-0}" -gt 0 ]; then
    if [ ! -f "$M/.eval_${v}" ]; then
      "$MODAL" run --detach modal_app/inference.py::evaluate_all_modal \
        --model "$v" --strategy pattern-aware > "$M/.evallog_${v}" 2>&1 & disown
      touch "$M/.eval_${v}"
      echo "EVAL    $v (launched, weights ready)"
    else
      echo "EVALING $v (in flight)"
    fi
  else
    echo "WAIT    $v (not merged)"
  fi
done

# all scored -> run the crossover
ALL=1; for v in $VARIANTS; do [ -f "$M/${v}_pattern-aware_scored.csv" ] || ALL=0; done
if [ "$ALL" -eq 1 ]; then
  echo ""; echo "=== ALL 8 SCORED — epoch crossover ==="
  "$PY" scripts/epoch_crossover.py --metric pass1
  echo ""
  "$PY" scripts/epoch_crossover.py --metric faithful
fi
