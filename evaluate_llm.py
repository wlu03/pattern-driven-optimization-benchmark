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
    python3 evaluate_llm.py --model gpt-4o --strategy generic
    python3 evaluate_llm.py --model claude-sonnet-4-6 --strategy pattern-aware
    python3 evaluate_llm.py --model deepseek-v3 --strategy taxonomy-guided
    python3 evaluate_llm.py --all-models --strategy generic --output results.csv
    python3 evaluate_llm.py --list-models
    python3 evaluate_llm.py --dry-run --model gpt-4o --strategy generic

Requires:
    pip install anthropic openai google-generativeai pyyaml
"""

import argparse
import csv
import os
import sys
import time
from dataclasses import asdict

from evaluator import EvalResult, evaluate_pattern
from models import load_model_config, make_call_llm_fn
from patterns import PATTERNS
from prompts import HW_TARGET_DESCRIPTIONS, build_prompt


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
    args = parser.parse_args()

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

    total = len(model_ids) * len(active_patterns)
    print(f"Evaluating {len(active_patterns)} patterns × {len(model_ids)} model(s) "
          f"= {total} runs  [strategy={args.strategy}]")
    print(f"Output → {args.output}\n")

    all_results = []
    run_idx = 0
    for model_id in model_ids:
        mcfg = models_cfg[model_id]
        retries = mcfg.get("retries", 2)
        try:
            call_llm_fn = make_call_llm_fn(mcfg, retries=retries)
        except Exception as e:
            print(f"[SKIP] {model_id}: {e}", file=sys.stderr)
            continue

        for pattern in active_patterns:
            run_idx += 1
            print(f"[{run_idx:>3}/{total}] {model_id:<25} {pattern.pattern_id:<6} ",
                  end="", flush=True)
            t0 = time.time()
            try:
                result = evaluate_pattern(pattern, model_id, args.strategy,
                                          call_llm_fn, hw_target=args.target)
                elapsed = time.time() - t0
                status = "OK" if result.compiles and result.correct else \
                         ("COMPILE_ERR" if not result.compiles else "WRONG")
                print(f"{status:<12} {elapsed:.1f}s  llm_ms={result.llm_ms:.1f}")
                all_results.append(result)
            except Exception as e:
                elapsed = time.time() - t0
                print(f"ERROR        {elapsed:.1f}s  {e}", file=sys.stderr)

        _write_results(all_results, args.output)
        all_results = []

    print(f"\nDone. Results appended to {args.output}")


if __name__ == "__main__":
    main()
