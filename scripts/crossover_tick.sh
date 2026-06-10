#!/usr/bin/env bash
# crossover_tick.sh — idempotently advance the in-dist epoch-sweep crossover.
#
# For each of the 8 epoch variants it, in order of readiness:
#   1. launches the eval on Modal (survivable orchestrator) once the variant's
#      MERGED weights (safetensors, not just config.json) exist on pdob-finetuned;
#   2. once the eval is COMPLETE (all 257 in-dist+OOD rows present — the
#      orchestrator checkpoints incrementally, so partial CSVs must NOT be
#      scored), filters + launches Modal scoring;
#   3. pulls the scored CSV back from pdob-results (only when it too is complete).
# When all 8 scored CSVs are present it runs epoch_crossover.py (pass1+faithful).
#
# Safe to run every few minutes — marker files prevent double-launching, every
# launched job is `--detach` (survives this script + the turn ending), and the
# 257-row completion gate stops premature scoring of a still-generating eval.
set -uo pipefail
cd "$(dirname "$0")/.."
MODAL="${MODAL:-$HOME/.local/bin/modal}"
PY="${PY:-/opt/homebrew/bin/python3}"
M=results/pareto_ft_indist; mkdir -p "$M"
INDIST=fine_tune/heldout_indist_variants.txt
EXPECT=257   # 79 in-dist held-out + 178 OOD (HO-*) rows

VARIANTS="qwen2.5-coder-1.5b-indist-ep1-ft qwen2.5-coder-1.5b-indist-ep3-ft \
qwen2.5-coder-1.5b-indist-ep6-ft qwen2.5-coder-1.5b-indist-ep10-ft \
r1-distill-qwen-7b-indist-ep1-ft r1-distill-qwen-7b-indist-ep3-ft \
r1-distill-qwen-7b-indist-ep6-ft r1-distill-qwen-7b-indist-ep10-ft"

VOL=$("$MODAL" volume ls pdob-results 2>/dev/null | grep -oE "[a-z0-9.-]+_pattern-aware(_scored)?.csv" || true)

cov() {  # count in-dist+OOD rows present in $1 (regardless of empty output)
  "$PY" -c "
import csv,sys
csv.field_size_limit(sys.maxsize)
ind=set(open('$INDIST').read().split())
try: rows=list(csv.DictReader(open('$1',newline='')))
except Exception: print(0); sys.exit()
print(sum(1 for r in rows if r.get('variant_id','') in ind or r.get('pattern_id','').startswith('HO-')))
" 2>/dev/null || echo 0
}

for v in $VARIANTS; do
  raw="results/pareto/${v}_pattern-aware.csv"
  filt="$M/${v}_pattern-aware.csv"
  scored="$M/${v}_pattern-aware_scored.csv"

  # already complete locally?
  if [ -f "$scored" ] && [ "$(cov "$scored")" -ge "$EXPECT" ]; then echo "DONE    $v"; continue; fi

  # scored CSV on the volume? pull + verify it's complete (else discard partial).
  if echo "$VOL" | grep -qx "${v}_pattern-aware_scored.csv"; then
    "$MODAL" volume get --force pdob-results "${v}_pattern-aware_scored.csv" "$scored" >/dev/null 2>&1
    if [ "$(cov "$scored")" -ge "$EXPECT" ]; then echo "PULLED  $v (scored)"; continue
    else rm -f "$scored"; fi
  fi

  # eval coverage (complete = all 257 target rows present)
  c=0; [ -f "$raw" ] && c=$(cov "$raw")
  if [ "${c:-0}" -lt "$EXPECT" ] && echo "$VOL" | grep -qx "${v}_pattern-aware.csv"; then
    "$MODAL" volume get --force pdob-results "${v}_pattern-aware.csv" "$raw" >/dev/null 2>&1
    c=$(cov "$raw")
  fi

  if [ "${c:-0}" -ge "$EXPECT" ]; then
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
      echo "SCORE   $v (launched, eval complete $c/$EXPECT)"
    else
      echo "SCORING $v (in flight)"
    fi
    continue
  fi

  # eval incomplete
  if [ "${c:-0}" -gt 0 ]; then echo "EVALING $v (generating $c/$EXPECT)"; continue; fi

  # no eval at all -> launch it once the merged weights are present
  has_w=$("$MODAL" volume ls pdob-finetuned "$v" 2>/dev/null | grep -cE "safetensors" || true)
  if [ "${has_w:-0}" -gt 0 ]; then
    if [ ! -f "$M/.eval_${v}" ]; then
      "$MODAL" run --detach modal_app/inference.py::evaluate_all_modal \
        --model "$v" --strategy pattern-aware > "$M/.evallog_${v}" 2>&1 & disown
      touch "$M/.eval_${v}"
      echo "EVAL    $v (launched, weights ready)"
    else
      echo "EVALING $v (in flight, no rows yet)"
    fi
  else
    echo "WAIT    $v (not merged)"
  fi
done

ALL=1; for v in $VARIANTS; do [ -f "$M/${v}_pattern-aware_scored.csv" ] || ALL=0; done
if [ "$ALL" -eq 1 ]; then
  echo ""; echo "=== ALL 8 SCORED — epoch crossover ==="
  "$PY" scripts/epoch_crossover.py --metric pass1
  echo ""
  "$PY" scripts/epoch_crossover.py --metric faithful
fi
