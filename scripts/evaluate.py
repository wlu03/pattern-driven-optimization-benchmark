"""
LLM Evaluation Framework for Pattern-Driven Code Optimization Benchmark

This script:
1. Extracts each SLOW function from the benchmark
2. Sends it to an LLM with various prompting strategies
3. Compiles the LLM output
4. Runs it against test cases
5. Measures speedup vs. the slow version and the hand-optimized version
6. Records results per pattern category

Usage:
    python3 scripts/evaluate.py --model gpt-4o --strategy generic
    python3 scripts/evaluate.py --model claude-sonnet-4-6 --strategy pattern-aware
    python3 scripts/evaluate.py --model deepseek-v3 --strategy taxonomy-guided
    python3 scripts/evaluate.py --all-models --strategy generic --output results.csv
    python3 scripts/evaluate.py --list-models
    python3 scripts/evaluate.py --dry-run --model gpt-4o --strategy generic
    python3 scripts/evaluate.py --dataset dataset --model gpt-4o --strategy generic
    python3 scripts/evaluate.py --dataset dataset --samples 5 --runs 10

Requires:
    pip install anthropic openai google-generativeai pyyaml
"""

import argparse
import csv
import math
import os
import random
import sys
import time
from dataclasses import asdict
from collections import defaultdict

# Make the repo root importable so ``pdob_core`` resolves when this script
# is run directly (``python3 scripts/evaluate.py ...``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdob_core.evaluator import EvalResult, evaluate_pattern, evaluate_variant  # noqa: E402
from pdob_core.models import load_model_config, make_call_llm_fn  # noqa: E402
from pdob_core.patterns import PATTERNS  # noqa: E402
from pdob_core.prompts import HW_TARGET_DESCRIPTIONS, build_prompt  # noqa: E402


def _write_results(results: list, output_path: str) -> None:
    if not results:
        return
    fieldnames = list(asdict(results[0]).keys())
    write_header = not os.path.exists(output_path)
    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))


def _parse_opt_levels(s: str) -> list:
    levels = [x.strip() for x in s.split(",") if x.strip()]
    valid = {"O0", "O1", "O2", "O3", "Os", "Ofast"}
    for lvl in levels:
        if lvl not in valid:
            raise argparse.ArgumentTypeError(
                f"Unknown opt level '{lvl}'. Expected one of {sorted(valid)}.")
    return levels


def _geometric_mean(xs: list):
    """exp(mean(log(x))) over positive values. Returns None if empty.

    Arithmetic mean is wrong for ratios — geometric mean is the correct
    aggregate for multiplicative quantities like speedup factors.
    """
    positives = [x for x in xs if x is not None and x > 0]
    if not positives:
        return None
    return math.exp(sum(math.log(x) for x in positives) / len(positives))


def _summarize_samples(rows: list, group_label: str) -> None:
    """Print pass@1, pass@k, and geometric-mean speedup over a list of
    EvalResult rows that all share the same (pattern_id, model, strategy)
    grouping (or, for dataset path, the same (variant_id, model, strategy)).
    """
    if not rows:
        return
    k = len(rows)
    successes = [r for r in rows if r.correct and not r.unreliable]
    pass_at_1 = 1.0 if (rows[0].correct and not rows[0].unreliable) else 0.0
    pass_at_k = 1.0 if successes else 0.0
    speedups_slow = [r.speedup_vs_slow for r in successes if r.speedup_vs_slow > 0]
    speedups_ref = [r.speedup_vs_ref for r in successes if r.speedup_vs_ref > 0]
    gm_slow = _geometric_mean(speedups_slow)
    gm_ref = _geometric_mean(speedups_ref)
    gm_slow_s = f"{gm_slow:.2f}x" if gm_slow is not None else "n/a"
    gm_ref_s = f"{gm_ref:.2f}x" if gm_ref is not None else "n/a"
    print(
        f"    summary [{group_label}] k={k}  "
        f"pass@1={pass_at_1:.0%}  pass@{k}={pass_at_k:.0%}  "
        f"geomean(slow→llm)={gm_slow_s}  geomean(ref→llm)={gm_ref_s}"
    )


def _set_sample_temperature(model_cfg: dict, sample_idx: int, total_samples: int,
                            base_temp: float = 0.2,
                            diverse_temp: float = 0.5) -> None:
    """Mutate model_cfg in place to set temperature for this sample.

    Sample 0 always uses base_temp (preserves K=1 behavior).
    Samples 1..K-1 use diverse_temp for diversity.
    """
    if total_samples <= 1:
        model_cfg["temperature"] = base_temp
        return
    model_cfg["temperature"] = base_temp if sample_idx == 0 else diverse_temp


def _run_patterns_path(args, models_cfg, model_ids, opt_levels):
    """Original patterns.py-based flow (Issues 2/3/4/5 apply)."""
    active_patterns = [p for p in PATTERNS if p.test_harness.strip()]
    if args.patterns:
        wanted = {x.strip() for x in args.patterns.split(",")}
        active_patterns = [p for p in active_patterns if p.pattern_id in wanted]
    if not active_patterns:
        print("No patterns match the filter (check --patterns or that test_harness is set).",
              file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        for p in active_patterns:
            prompt = build_prompt(p, args.strategy, args.target)
            print(f"\n{'='*60}")
            print(f"Pattern: {p.pattern_id} — {p.name}")
            print(f"Strategy: {args.strategy}  |  Models: {', '.join(model_ids)}")
            print(f"{'='*60}")
            print(prompt)
        return

    total = len(model_ids) * len(active_patterns) * args.samples
    print(f"Evaluating {len(active_patterns)} patterns × {len(model_ids)} model(s) "
          f"× {args.samples} sample(s) = {total} runs  [strategy={args.strategy}, "
          f"runs={args.runs}, opt_levels={','.join(opt_levels)}, "
          f"noise_floor={args.noise_floor}ms]")
    print(f"Output → {args.output}\n")

    run_idx = 0
    for model_id in model_ids:
        mcfg = models_cfg[model_id]
        retries = mcfg.get("retries", 2)
        for pattern in active_patterns:
            sample_results = []
            for s in range(args.samples):
                _set_sample_temperature(mcfg, s, args.samples)
                try:
                    call_llm_fn = make_call_llm_fn(mcfg, retries=retries)
                except Exception as e:
                    print(f"[SKIP] {model_id}: {e}", file=sys.stderr)
                    break

                run_idx += 1
                tag = f"s{s}" if args.samples > 1 else ""
                print(
                    f"[{run_idx:>3}/{total}] {model_id:<25} "
                    f"{pattern.pattern_id:<6} {tag:<4}",
                    end="", flush=True,
                )
                t0 = time.time()
                try:
                    result = evaluate_pattern(
                        pattern, model_id, args.strategy, call_llm_fn,
                        hw_target=args.target,
                        runs=args.runs,
                        opt_levels=opt_levels,
                        noise_floor_ms=args.noise_floor,
                        sample_idx=s,
                        faithfulness=args.faithfulness,
                        iter_max_rounds=args.iter_rounds,
                        iter_speedup_threshold=args.iter_threshold,
                    )
                    elapsed = time.time() - t0
                    if not result.compiles:
                        status = "COMPILE_ERR"
                    elif not result.correct:
                        status = "WRONG"
                    elif result.unreliable:
                        status = "UNRELIABLE"
                    else:
                        status = "OK"
                    print(f" {status:<12} {elapsed:.1f}s  "
                          f"llm_ms={result.llm_ms:.3f} "
                          f"speedup_vs_slow={result.speedup_vs_slow:.1f}x")
                    sample_results.append(result)
                except Exception as e:
                    elapsed = time.time() - t0
                    print(f" ERROR        {elapsed:.1f}s  {e}", file=sys.stderr)

            if sample_results and args.samples > 1:
                _summarize_samples(sample_results,
                                   f"{model_id}/{pattern.pattern_id}")
            _write_results(sample_results, args.output)

    print(f"\nDone. Results appended to {args.output}")


def _run_dataset_path(args, models_cfg, model_ids, opt_levels):
    """New dataset-driven flow (Issue 1 + 2/3/4/5 also apply here)."""
    from pdob_core.dataset_evaluator import discover_variants

    variants = list(discover_variants(args.dataset))
    if not variants:
        print(f"No variants found under {args.dataset!r}.", file=sys.stderr)
        sys.exit(1)

    # Optional: filter by --patterns (matches by pattern_id).
    if args.patterns:
        wanted = {x.strip() for x in args.patterns.split(",")}
        variants = [v for v in variants if v.pattern_id in wanted]
        if not variants:
            print(f"No variants match --patterns={args.patterns!r}.",
                  file=sys.stderr)
            sys.exit(1)

    # Optional: subsample to N variants per pattern_id for fast iteration.
    if args.variants_per_pattern is not None:
        by_pid = defaultdict(list)
        for v in variants:
            by_pid[v.pattern_id].append(v)
        sampled = []
        rng = random.Random(42)  # deterministic subsample
        for pid, vs in by_pid.items():
            vs_sorted = sorted(vs, key=lambda v: v.variant_id)
            if args.variants_per_pattern >= len(vs_sorted):
                sampled.extend(vs_sorted)
            else:
                sampled.extend(rng.sample(vs_sorted, args.variants_per_pattern))
        variants = sorted(sampled, key=lambda v: (v.pattern_id, v.variant_id))

    pattern_lookup = {p.pattern_id: p for p in PATTERNS}

    if args.dry_run:
        # Print one prompt per pattern_id for visibility (not per variant —
        # that would be 590 prompts).
        seen_pids = set()
        from pdob_core.evaluator import _build_variant_prompt  # private but local OK
        for v in variants:
            if v.pattern_id in seen_pids:
                continue
            seen_pids.add(v.pattern_id)
            prompt = _build_variant_prompt(v, pattern_lookup, args.strategy,
                                           args.target)
            print(f"\n{'='*60}")
            print(f"Pattern: {v.pattern_id}  Variant: {v.variant_id}  "
                  f"({v.pattern_name})")
            print(f"Strategy: {args.strategy}  |  Models: {', '.join(model_ids)}")
            print(f"{'='*60}")
            print(prompt)
        print(f"\n(Dry run: printed {len(seen_pids)} unique pattern_ids; "
              f"actual run would do {len(variants)} variant(s) × "
              f"{len(model_ids)} model(s) × {args.samples} sample(s).)")
        return

    total = len(model_ids) * len(variants) * args.samples
    print(f"Evaluating {len(variants)} variants × {len(model_ids)} model(s) "
          f"× {args.samples} sample(s) = {total} runs  [strategy={args.strategy}, "
          f"runs={args.runs}, opt_levels={','.join(opt_levels)}, "
          f"noise_floor={args.noise_floor}ms]")
    print(f"Output → {args.output}\n")

    run_idx = 0
    for model_id in model_ids:
        mcfg = models_cfg[model_id]
        retries = mcfg.get("retries", 2)
        for variant in variants:
            sample_results = []
            for s in range(args.samples):
                _set_sample_temperature(mcfg, s, args.samples)
                try:
                    call_llm_fn = make_call_llm_fn(mcfg, retries=retries)
                except Exception as e:
                    print(f"[SKIP] {model_id}: {e}", file=sys.stderr)
                    break

                run_idx += 1
                tag = f"s{s}" if args.samples > 1 else ""
                print(
                    f"[{run_idx:>3}/{total}] {model_id:<25} "
                    f"{variant.variant_id:<22} {tag:<4}",
                    end="", flush=True,
                )
                t0 = time.time()
                try:
                    result = evaluate_variant(
                        variant, model_id, args.strategy, call_llm_fn,
                        pattern_lookup=pattern_lookup,
                        hw_target=args.target,
                        runs=args.runs,
                        opt_levels=opt_levels,
                        noise_floor_ms=args.noise_floor,
                        sample_idx=s,
                        faithfulness=args.faithfulness,
                    )
                    elapsed = time.time() - t0
                    if not result.compiles:
                        status = "COMPILE_ERR"
                    elif not result.correct:
                        status = "WRONG"
                    elif result.unreliable:
                        status = "UNRELIABLE"
                    else:
                        status = "OK"
                    print(f" {status:<12} {elapsed:.1f}s  "
                          f"llm_ms={result.llm_ms:.3f} "
                          f"speedup_vs_slow={result.speedup_vs_slow:.1f}x")
                    sample_results.append(result)
                except Exception as e:
                    elapsed = time.time() - t0
                    print(f" ERROR        {elapsed:.1f}s  {e}", file=sys.stderr)

            if sample_results and args.samples > 1:
                _summarize_samples(sample_results,
                                   f"{model_id}/{variant.variant_id}")
            _write_results(sample_results, args.output)

    print(f"\nDone. Results appended to {args.output}")


def main():
    parser = argparse.ArgumentParser(description="LLM Code Optimization Evaluator")
    parser.add_argument("--config", default="models.yaml",
                        help="Path to models.yaml config file")
    parser.add_argument("--model", default=None,
                        help="Model ID to evaluate (from models.yaml)")
    parser.add_argument("--all-models", action="store_true",
                        help="Evaluate all models defined in models.yaml")
    parser.add_argument("--list-models", action="store_true",
                        help="List available models from config and exit")
    parser.add_argument("--strategy", default="generic",
                        choices=["generic", "pattern-aware", "taxonomy-guided",
                                 "diagnosis", "hardware-target"],
                        help="Prompting strategy")
    parser.add_argument("--target", default="generic",
                        choices=list(HW_TARGET_DESCRIPTIONS.keys()),
                        help="Hardware target (for hardware-target strategy)")
    parser.add_argument("--patterns", default=None,
                        help="Comma-separated pattern IDs to evaluate (e.g. SR-1,CF-2). "
                             "Default: all patterns with a test harness.")
    parser.add_argument("--output", default="results.csv",
                        help="Output CSV file (appended to if it already exists)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompts without calling any LLM")
    # ── New flags ──
    parser.add_argument("--dataset", default=None,
                        help="Root directory of variant dataset. When set, "
                             "evaluator iterates dataset/*/*/{slow.c,fast.c,"
                             "test.c} instead of patterns.py.")
    parser.add_argument("--variants-per-pattern", type=int, default=None,
                        help="When --dataset is set, sample N variants per "
                             "pattern_id (deterministic). Default: all variants.")
    parser.add_argument("--samples", type=int, default=1,
                        help="Number of LLM completions per (pattern, model). "
                             "Default 1 (current behavior). >1 raises "
                             "temperature for samples 1..K-1 to encourage "
                             "diversity; pass@k and geometric-mean speedup "
                             "are also reported.")
    parser.add_argument("--runs", type=int, default=10,
                        help="Number of timed runs per binary (median + MAD). "
                             "Default 10. Matched for candidate and reference.")
    parser.add_argument("--noise-floor", type=float, default=0.05,
                        help="Minimum llm_ms (in ms) below which we suspect "
                             "DCE/constant-folding and flag the row as "
                             "unreliable (speedup_vs_* zeroed). Default 0.05.")
    parser.add_argument("--opt-levels", type=_parse_opt_levels, default="O2",
                        help="Comma-separated opt levels for candidate "
                             "(e.g. O0,O2,O3). The FIRST level is the "
                             "primary (drives slow_ms/llm_ms/ref_fast_ms); "
                             "additional levels populate llm_ms_O0/O3 columns.")
    parser.add_argument("--faithfulness", action="store_true",
                        help="Run the 2x2 faithfulness cascade (structural "
                             "check + differential equivalence) for every "
                             "correct candidate. Populates faithfulness_cell "
                             "and friends in the output CSV. Adds ~9 extra "
                             "compile+run cycles per candidate.")
    parser.add_argument("--iter-rounds", type=int, default=1, dest="iter_rounds",
                        help="LLM-as-optimizer iteration cap. When >1 AND the "
                             "initial speedup is below --iter-threshold, the "
                             "model is given its own code + measured speedup "
                             "and asked to try harder, up to N rounds total. "
                             "The best correct candidate wins. Default 1 "
                             "(off — preserves single-shot behavior).")
    parser.add_argument("--iter-threshold", type=float, default=2.0,
                        dest="iter_threshold",
                        help="Stop iterating once measured speedup exceeds "
                             "this threshold (default 2.0x). Set to a large "
                             "value (e.g. 999) to force every iteration to "
                             "run regardless of measured speedup.")
    args = parser.parse_args()

    # opt-levels is custom-parsed; if user passed "O2" we get a list.
    opt_levels = args.opt_levels if isinstance(args.opt_levels, list) else _parse_opt_levels(args.opt_levels)
    if not opt_levels:
        opt_levels = ["O2"]

    if args.samples < 1:
        print("ERROR: --samples must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.runs < 1:
        print("ERROR: --runs must be >= 1", file=sys.stderr)
        sys.exit(1)

    models_cfg = load_model_config(args.config)

    if args.list_models:
        print(f"{'ID':<30} {'Provider':<15} {'Auth / Endpoint':<30} Description")
        print("-" * 100)
        current_provider = None
        for mid, mcfg in models_cfg.items():
            provider = mcfg.get("provider", "")
            if provider != current_provider:
                section = {
                    "anthropic":     "── Anthropic ──",
                    "openai":        "── OpenAI ──",
                    "openai_compat": "── OpenAI-compatible (Together AI / Groq / DeepSeek) ──",
                    "google":        "── Google ──",
                    "ollama":        "── Ollama (local) ──",
                }.get(provider, f"── {provider} ──")
                print(f"\n{section}")
                current_provider = provider

            if provider == "ollama":
                auth_info = mcfg.get("base_url", "http://localhost:11434/v1")
            else:
                key_var = mcfg.get("api_key_env", "")
                key_set = "✓" if os.environ.get(key_var) else "✗ not set"
                auth_info = f"{key_var}={key_set}"

            print(f"  {mid:<28} {provider:<15} {auth_info:<30} {mcfg.get('description','')}")
        return

    if args.all_models:
        model_ids = list(models_cfg.keys())
    elif args.model:
        if args.model not in models_cfg:
            print(f"ERROR: model '{args.model}' not found in {args.config}. "
                  f"Use --list-models to see available models.", file=sys.stderr)
            sys.exit(1)
        model_ids = [args.model]
    else:
        parser.print_help()
        print("\nProvide --model <id> or --all-models (or --list-models to see options).",
              file=sys.stderr)
        sys.exit(1)

    if args.dataset:
        _run_dataset_path(args, models_cfg, model_ids, opt_levels)
    else:
        _run_patterns_path(args, models_cfg, model_ids, opt_levels)


if __name__ == "__main__":
    main()
