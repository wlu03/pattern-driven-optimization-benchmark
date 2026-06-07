#!/usr/bin/env bash
# Recompute faithfulness for all 45 cells (COMP composition fix + venv repair),
# then rebuild combined/lean CSVs and regenerate the 2x2 + scaling.
# Faithfulness-only: timing/correctness/speedup are preserved, ranking unchanged.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=/opt/homebrew/bin/python3          # has pycparser (structural axis + report_2x2)
VPY=.venv-analysis/bin/python         # has pandas/matplotlib (scaling)

OLD="codestral-22b deepseek-r1-distill-llama-70b deepseek-r1-distill-qwen-1.5b \
deepseek-r1-distill-qwen-32b qwen2.5-72b qwen2.5-coder-1.5b qwen2.5-coder-14b \
qwen2.5-coder-32b qwen2.5-coder-7b"
NEW="deepseek-coder-v2-lite deepseek-r1-distill-qwen-7b opencoder-8b qwen3-32b qwq-32b yi-coder-9b"

echo "=== [1/4] recompute faithfulness: 27 old cells (reuse equivalence, fast) ==="
for m in $OLD; do for s in generic pattern-aware taxonomy-guided; do
  f="results/pareto/${m}_${s}_scored.csv"
  echo "  reuse  ${m}_${s}"
  $PY scripts/rescore_faithfulness.py "$f" --equivalence reuse
done; done

echo "=== [2/4] recompute faithfulness: 18 venv-scored cells (recompute 9-config equiv, slow) ==="
for m in $NEW; do for s in generic pattern-aware taxonomy-guided; do
  f="results/pareto/${m}_${s}_scored.csv"
  echo "  recompute  ${m}_${s}"
  $PY scripts/rescore_faithfulness.py "$f" --equivalence recompute
done; done

echo "=== [3/4] rebuild combined + lean CSVs ==="
$PY - <<'PYEOF'
import csv, sys, glob, os
csv.field_size_limit(sys.maxsize)
files = sorted(glob.glob("results/pareto/*_scored.csv"))
LEAN = ["pattern_id","model","strategy","correct","unreliable","speedup_vs_slow","sample_idx","faithfulness_cell"]
header=None; tot=0
with open("results/pareto_combined_scored.csv.tmp","w",newline="") as wf, \
     open("results/pareto_combined_lean.csv.tmp","w",newline="") as lf:
    w=csv.writer(wf); lw=csv.DictWriter(lf, fieldnames=LEAN, extrasaction="ignore"); lw.writeheader()
    for f in files:
        with open(f,newline="") as rf:
            r=csv.reader(rf); h=next(r)
            if header is None: header=h; w.writerow(h); idx={c:i for i,c in enumerate(h)}
            for row in r:
                w.writerow(row); tot+=1
                lw.writerow({c:row[idx[c]] for c in LEAN if c in idx})
os.replace("results/pareto_combined_scored.csv.tmp","results/pareto_combined_scored.csv")
os.replace("results/pareto_combined_lean.csv.tmp","results/pareto_combined_lean.csv")
print(f"  combined: {tot} rows from {len(files)} cells")
PYEOF

echo "=== [4/4] regenerate 2x2 + scaling ==="
$PY faithfulness/report_2x2.py results/pareto_combined_scored.csv --out results/aggregate_2x2/ \
    > results/aggregate_2x2/report.txt 2>results/aggregate_2x2/report.err
echo "  2x2 report regenerated"
for metric in geomean_speedup pass1 faithful_rate; do
  for strat in generic pattern-aware taxonomy-guided; do
    $VPY scripts/scaling_analysis.py results/pareto_combined_lean.csv \
        --strategy "$strat" --metric "$metric" \
        --out "results/scaling/${metric}_${strat}.pdf" >/dev/null 2>&1
  done
done
echo "  9 scaling plots regenerated"
echo "=== DONE ==="
