#!/usr/bin/env bash
# run_pareto_sweep.sh — submit the full (model × strategy) Modal sweep.
#
# Loops over the Pareto-frontier model shortlist × the 3 prompt strategies
# (generic / pattern-aware / taxonomy-guided), submitting one detached
# Modal job per (model, strategy). Detached means each job continues in
# the cloud even after this script returns — close your laptop, come back
# later, score the resulting CSVs locally with scripts/score_completions.py.
#
# Skips (model, strategy) combos whose output CSV already exists, so the
# script is safe to re-run after a partial failure.
#
# Usage:
#   bash scripts/run_pareto_sweep.sh             # full 10-model x 3-strategy sweep
#   bash scripts/run_pareto_sweep.sh smoke       # 2 cheapest models, 20 variants
#   MODELS="qwen2.5-coder-7b" bash scripts/run_pareto_sweep.sh   # custom subset
#
# Outputs to results/pareto/<model>_<strategy>.csv (raw outputs +
# reasoning_trace where the model emits one). Each Modal job prints its
# URL to its .submit.log for live monitoring at modal.com/apps/<user>/main/.
#
# Cost estimate (verified against modal.com/pricing × 3 strategies):
#   1.5B-2x   on T4         : ~$1.80
#   7B-2x     on A10G       : ~$6.60
#   14B       on L40S       : ~$9.75
#   22B       on L40S       : ~$9.75
#   32B-2x    on A100-80GB  : ~$37.50
#   70B-2x    on H200       : ~$13-26 (qwen2.5-72b + deepseek-r1-distill-llama-70b)
#   ------------------------------------------------------------
#   Total                   : ~$95 + cold-start budget = ~$110-145
set -euo pipefail
cd "$(dirname "$0")/.."

PROFILE="${1:-full}"

case "$PROFILE" in
  smoke)
    MODELS="${MODELS:-qwen2.5-coder-1.5b deepseek-r1-distill-qwen-1.5b}"
    STRATEGIES="${STRATEGIES:-taxonomy-guided}"
    LIMIT="${LIMIT:-20}"
    ;;
  full)
    MODELS="${MODELS:-qwen2.5-coder-1.5b qwen2.5-coder-7b qwen2.5-coder-14b qwen2.5-coder-32b deepseek-r1-distill-qwen-1.5b deepseek-r1-distill-qwen-7b deepseek-r1-distill-qwen-32b codestral-22b qwen2.5-72b deepseek-r1-distill-llama-70b qwq-32b qwen3-32b opencoder-8b deepseek-coder-v2-lite yi-coder-9b}"
    STRATEGIES="${STRATEGIES:-generic pattern-aware taxonomy-guided}"
    LIMIT="${LIMIT:-0}"   # 0 = full dataset
    ;;
  *)
    echo "Usage: $0 [smoke|full]" >&2
    echo "  (or set MODELS / STRATEGIES / LIMIT env vars to override)" >&2
    exit 1
    ;;
esac

mkdir -p results/pareto

submitted=0
skipped=0
for m in $MODELS; do
  for s in $STRATEGIES; do
    suffix=""
    [ "$LIMIT" -gt 0 ] && suffix="_limit${LIMIT}"
    out="results/pareto/${m}_${s}${suffix}.csv"
    if [ -f "$out" ] || [ -f "${out%.csv}_scored.csv" ]; then
      printf "  skip (CSV exists)  %-40s %s\n" "$m" "$s"
      skipped=$((skipped+1))
      continue
    fi
    extra_args=""
    [ "$LIMIT" -gt 0 ] && extra_args="--limit $LIMIT"
    printf "  submit             %-40s %s -> %s\n" "$m" "$s" "$out"
    modal run --detach modal_app/inference.py::evaluate_all \
        --model "$m" --strategy "$s" --output "$out" $extra_args \
        &> "results/pareto/${m}_${s}${suffix}.submit.log" &
    submitted=$((submitted+1))
    # Space out app creation: Modal rate-limits rapid-fire submissions
    # ("App creation failed: rate limit exceeded"). Override with SUBMIT_DELAY=0.
    sleep "${SUBMIT_DELAY:-15}"
  done
done
wait

echo
echo "Sweep submission complete: $submitted submitted, $skipped skipped."
echo
echo "Monitor jobs at: https://modal.com/apps/$(whoami)/main"
echo "Output CSVs will land in results/pareto/ as each job completes."
echo
echo "When CSVs land, score them locally with:"
echo "  bash scripts/score_pareto_sweep.sh"
