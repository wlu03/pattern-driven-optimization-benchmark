#!/usr/bin/env bash
# Crash-proof re-score of the three DeepSeek-R1-Distill-Llama-70B cells from the
# decoded (detokenized) completions.
#
# The first scoring pass left these three cells all-zero: the Llama-tokenizer
# 70B came back byte-BPE-encoded ( "ĊOkay,ĠI..."), so extraction found no code.
# The decode is fixed in results/pareto/rescore/*_decoded.csv (1244 rows each,
# ~1130 with a ```c fence); this script re-scores those, overwriting the bogus
# results/pareto/*_scored.csv in place.
#
# Memory safety (this is the part that prevents the OOM that killed the last
# run): every compiled binary runs under compile_and_run's watchdog
# (_run_with_limits), which polls RSS via ps and kills any child exceeding
# PDOB_MEM_CAP_MB. Each score_completions process is internally serial (one
# child binary at a time), and we run at most JOBS of them, so peak concurrent
# child RAM is bounded by JOBS * PDOB_MEM_CAP_MB. Defaults below cap that at
# 3 * 4096 = 12 GB on a 48 GB host (~25%); the host currently has ~42 GB free.
#
# Output is written by score_completions in a single pass at the very end, so a
# crash mid-run leaves the existing file untouched rather than truncating it.
#
# Usage:
#   bash scripts/rescore_ds70b.sh                 # JOBS=3 RUNS=10 (defaults)
#   JOBS=1 bash scripts/rescore_ds70b.sh          # fully serial, lowest RAM
#   PDOB_MEM_CAP_MB=2048 bash scripts/rescore_ds70b.sh   # tighter per-child cap
set -uo pipefail
cd "$(dirname "$0")/.."

MODEL="deepseek-r1-distill-llama-70b"
RUNS="${RUNS:-10}"
JOBS="${JOBS:-3}"                                    # only 3 cells; all at once
export PDOB_MEM_CAP_MB="${PDOB_MEM_CAP_MB:-4096}"    # per-child RSS ceiling (MB)
export PDOB_OUT_CAP_MB="${PDOB_OUT_CAP_MB:-64}"      # per-child stdout ceiling (MB)

PY="${PY:-.venv-analysis/bin/python}"
RDIR="results/pareto/rescore"
ODIR="results/pareto"
STRATS=(generic pattern-aware taxonomy-guided)

echo "Re-scoring $MODEL"
echo "  JOBS=$JOBS  RUNS=$RUNS  per-child cap=${PDOB_MEM_CAP_MB}MB  out cap=${PDOB_OUT_CAP_MB}MB"
echo "  worst-case concurrent child RAM ceiling: $((JOBS * PDOB_MEM_CAP_MB)) MB"
echo

# Back up the bogus 0% scored files once, in case we want to diff later (cheap).
mkdir -p "$RDIR/bogus_backup"
for s in "${STRATS[@]}"; do
  old="$ODIR/${MODEL}_${s}_scored.csv"
  [ -f "$old" ] && cp -n "$old" "$RDIR/bogus_backup/${MODEL}_${s}_scored.bogus.csv"
done

for s in "${STRATS[@]}"; do
  in="$RDIR/${MODEL}_${s}_decoded.csv"
  out="$ODIR/${MODEL}_${s}_scored.csv"
  log="$RDIR/${MODEL}_${s}.rescore.log"
  if [ ! -f "$in" ]; then
    echo "  [skip] missing decoded input: $in"
    continue
  fi
  echo "  [start] $s  ($in -> $out)  log: $log"
  "$PY" scripts/score_completions.py "$in" \
      --output "$out" --runs "$RUNS" --faithfulness \
      > "$log" 2>&1 &
  # Throttle to JOBS concurrent scorers (wait -n is bash 4.3+; macOS ships 3.2).
  while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$JOBS" ]; do sleep 2; done
done
wait

echo
echo "==== re-score complete; per-cell summary ===="
for s in "${STRATS[@]}"; do
  log="$RDIR/${MODEL}_${s}.rescore.log"
  printf "  %-16s " "$s"
  grep -hE "Compilation rate|Correctness rate|Median speedup" "$log" 2>/dev/null | tr '\n' '  '
  echo
done
echo
echo "Now rerank with:  $PY scripts/rank_models.py --sort size --keep-zero"