"""
evaluate_faithfulness.py
------------------------
Evaluate structural faithfulness of model outputs against ground-truth patterns.

Usage:
    # Single variant
    python3 evaluate_faithfulness.py \
        --pattern SR-1 \
        --slow    ../dataset/SR_1/SR-1_v000/slow.c \
        --output  model_output.c

    # Full dataset sweep (reads model outputs from a JSONL results file)
    python3 evaluate_faithfulness.py \
        --results  results.jsonl \
        --dataset  ../dataset \
        --out-csv  faithfulness_results.csv

    # Single pattern directory
    python3 evaluate_faithfulness.py \
        --pattern-dir ../dataset/SR_1 \
        --output-dir  model_outputs/SR_1/

Results JSONL format (--results):
    {"pattern_id": "SR-1", "variant_id": "SR-1_v000", "model_output": "<code>"}

Requirements:
    pip install pycparser
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# Allow running from faithfulness/ or from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkers import check_faithfulness, CHECKERS, Verdict


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read(path: str | Path) -> str:
    with open(path) as f:
        return f.read()


def _print_result(pattern_id, variant_id, result, verbose=False):
    icon = {"faithful": "✓", "unfaithful": "✗", "partial": "~", "unknown": "?"}.get(result.verdict, "?")
    print(f"  [{icon}] {pattern_id} {variant_id:20s}  score={result.score:.2f}  {result.explanation}")
    if verbose:
        for c in result.checks_passed:
            print(f"        + {c}")
        for c in result.checks_failed:
            print(f"        - {c}")


def _aggregate(results: list[dict]) -> dict:
    total     = len(results)
    faithful  = sum(1 for r in results if r["verdict"] == Verdict.FAITHFUL)
    partial   = sum(1 for r in results if r["verdict"] == Verdict.PARTIAL)
    unfaith   = sum(1 for r in results if r["verdict"] == Verdict.UNFAITHFUL)
    unknown   = sum(1 for r in results if r["verdict"] == Verdict.UNKNOWN)
    avg_score = sum(r["score"] for r in results) / total if total else 0.0
    return {
        "total":      total,
        "faithful":   faithful,
        "partial":    partial,
        "unfaithful": unfaith,
        "unknown":    unknown,
        "avg_score":  round(avg_score, 4),
        "faithful_%": round(100 * faithful / total, 1) if total else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation modes
# ─────────────────────────────────────────────────────────────────────────────

def eval_single(args):
    slow_code    = _read(args.slow)
    model_output = _read(args.output)
    result       = check_faithfulness(args.pattern, slow_code, model_output)
    _print_result(args.pattern, Path(args.output).stem, result, verbose=True)
    return result


def eval_results_jsonl(args):
    dataset_dir = Path(args.dataset)
    rows = []

    with open(args.results) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    print(f"Evaluating {len(entries)} model outputs …\n")
    per_pattern: dict[str, list] = {}

    for entry in entries:
        pattern_id = entry.get("pattern_id") or entry.get("_pattern_id", "")
        variant_id = entry.get("variant_id") or entry.get("_variant_id", "")
        model_output = entry.get("model_output", "")

        # Locate slow.c in dataset
        pat_dir = pattern_id.replace("-", "_")
        slow_path = dataset_dir / pat_dir / variant_id / "slow.c"
        if not slow_path.exists():
            print(f"  [!] slow.c not found for {variant_id}, skipping")
            continue

        slow_code = _read(slow_path)
        result    = check_faithfulness(pattern_id, slow_code, model_output)

        row = {
            "pattern_id": pattern_id,
            "variant_id": variant_id,
            **result.to_dict(),
        }
        rows.append(row)
        per_pattern.setdefault(pattern_id, []).append(row)
        _print_result(pattern_id, variant_id, result, verbose=args.verbose)

    # Per-pattern summary
    print("\n" + "─" * 60)
    print(f"{'Pattern':<10} {'Faithful':>8} {'Partial':>8} {'Unfaith':>8} {'Score':>8}")
    print("─" * 60)
    for pid in sorted(per_pattern):
        agg = _aggregate(per_pattern[pid])
        print(f"{pid:<10} {agg['faithful_%']:>7}%  {agg['partial']:>8}  {agg['unfaithful']:>8}  {agg['avg_score']:>8.3f}")

    overall = _aggregate(rows)
    print("─" * 60)
    print(f"{'OVERALL':<10} {overall['faithful_%']:>7}%  {overall['partial']:>8}  "
          f"{overall['unfaithful']:>8}  {overall['avg_score']:>8.3f}")
    print(f"  Total: {overall['total']}  "
          f"Faithful: {overall['faithful']}  "
          f"Partial: {overall['partial']}  "
          f"Unfaithful: {overall['unfaithful']}  "
          f"Unknown: {overall['unknown']}")

    if args.out_csv:
        with open(args.out_csv, "w", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        print(f"\nResults written to {args.out_csv}")

    return rows


def eval_pattern_dir(args):
    pattern_dir  = Path(args.pattern_dir)
    output_dir   = Path(args.output_dir)
    pattern_id   = pattern_dir.name.replace("_", "-")

    rows = []
    for variant_dir in sorted(pattern_dir.iterdir()):
        if not variant_dir.is_dir():
            continue
        slow_path   = variant_dir / "slow.c"
        output_path = output_dir / variant_dir.name / "output.c"
        if not slow_path.exists() or not output_path.exists():
            continue
        slow_code    = _read(slow_path)
        model_output = _read(output_path)
        result       = check_faithfulness(pattern_id, slow_code, model_output)
        _print_result(pattern_id, variant_dir.name, result, verbose=args.verbose)
        rows.append({"pattern_id": pattern_id, "variant_id": variant_dir.name, **result.to_dict()})

    if rows:
        agg = _aggregate(rows)
        print(f"\n{pattern_id}: {agg['faithful_%']}% faithful, avg score {agg['avg_score']:.3f}")
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate faithfulness of model-generated C code")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show individual check details")

    sub = parser.add_subparsers(dest="mode")

    # Single variant
    s = sub.add_parser("single", help="Evaluate one model output against one slow.c")
    s.add_argument("--pattern", required=True, choices=list(CHECKERS.keys()))
    s.add_argument("--slow",    required=True, help="Path to slow.c")
    s.add_argument("--output",  required=True, help="Path to model output .c file")

    # Results JSONL sweep
    r = sub.add_parser("sweep", help="Evaluate all entries in a results JSONL file")
    r.add_argument("--results",  required=True, help="JSONL file with model outputs")
    r.add_argument("--dataset",  default="../dataset", help="Path to dataset/ directory")
    r.add_argument("--out-csv",  default=None, help="Write results to CSV")

    # Pattern directory
    p = sub.add_parser("pattern", help="Evaluate all variants in one pattern directory")
    p.add_argument("--pattern-dir",  required=True, help="e.g. ../dataset/SR_1")
    p.add_argument("--output-dir",   required=True, help="Directory with model outputs per variant")

    args = parser.parse_args()

    if args.mode == "single":
        eval_single(args)
    elif args.mode == "sweep":
        eval_results_jsonl(args)
    elif args.mode == "pattern":
        eval_pattern_dir(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
