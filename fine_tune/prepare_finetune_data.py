"""
prepare_finetune_data.py
------------------------
Converts the dataset/ directory into a JSONL file for LoRA fine-tuning.

Each variant becomes one or more training examples depending on --strategies.
The prompt/response format exactly matches evaluate_llm.py so the model
learns to answer the same prompts it will be evaluated on.

Output: fine_tune_data.jsonl  (one JSON object per line, chat format)

Usage:
    python3 prepare_finetune_data.py
    python3 prepare_finetune_data.py --dataset ../dataset/ --output fine_tune_data.jsonl
    python3 prepare_finetune_data.py --strategies generic pattern-aware taxonomy-guided
    python3 prepare_finetune_data.py --split 0.9 --train train.jsonl --val val.jsonl
    python3 prepare_finetune_data.py --stats   # print dataset summary and exit

Format produced (ChatML, compatible with Qwen2.5-Coder-Instruct):
    {"messages": [
        {"role": "user",      "content": "<prompt>"},
        {"role": "assistant", "content": "<fast.c contents>"}
    ]}
"""

import argparse
import json
import os
import random
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Prompt builders — kept in sync with evaluate_llm.py
# ---------------------------------------------------------------------------

TAXONOMY = """
Inefficient Code Pattern Taxonomy:
1. Semantic Redundancy: Loop-invariant computation, recomputable expressions, redundant aggregation
2. Input-Sensitive: Sparse data, distribution skew, early termination, sorted input
3. Control-Flow: Hoistable branches, redundant bounds checks, collapsible loops, generic dispatch
4. Human-Style: Redundant temps, copy-paste duplication, dead code, defensive checks
5. Data Structure: Linear vs hash, repeated allocation, unnecessary copying, AoS vs SoA
6. Algorithmic: Brute force vs DP, repeated sort, naive search, redundant recursion
7. Memory/IO: Allocation in loops, redundant zeroing, heap in hot loop, cache-unfriendly access
"""


def prompt_generic(slow_code: str) -> str:
    return (
        "Optimize the following C code for better performance.\n"
        "Return ONLY the optimized C function. Do not change the function signature.\n"
        "Rename the function to `optimized`.\n\n"
        f"```c\n{slow_code}\n```"
    )


def prompt_pattern_aware(slow_code: str, meta: dict) -> str:
    return (
        "The following C code contains a performance inefficiency classified as:\n"
        f"Category: {meta.get('category', '')}\n"
        f"Pattern: {meta.get('pattern_name', '')}\n\n"
        "Optimize this code to eliminate the inefficiency. "
        "Rename the function to `optimized`.\n"
        "Return ONLY the optimized C function.\n\n"
        f"```c\n{slow_code}\n```"
    )


def prompt_taxonomy_guided(slow_code: str) -> str:
    return (
        f"{TAXONOMY}\n"
        "Analyze the following C code. First identify which inefficiency pattern(s) it contains,\n"
        "then optimize accordingly. Rename the function to `optimized`.\n"
        "Return ONLY the optimized C function.\n\n"
        f"```c\n{slow_code}\n```"
    )


PROMPT_BUILDERS = {
    "generic":          lambda slow, meta: prompt_generic(slow),
    "pattern-aware":    lambda slow, meta: prompt_pattern_aware(slow, meta),
    "taxonomy-guided":  lambda slow, meta: prompt_taxonomy_guided(slow),
}


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def make_response(fast_code: str) -> str:
    """
    The model should output the fast code with the function renamed to `optimized`.
    We do the rename here so the training target matches eval expectations.
    """
    # Rename the first function definition: fast_<anything>( -> optimized(
    renamed = re.sub(
        r'\b((?:static\s+)?[\w\s\*]+?)\b(fast_\w+)\s*\(',
        lambda m: m.group(0).replace(m.group(2), "optimized"),
        fast_code,
        count=1,
    )
    return f"```c\n{renamed.strip()}\n```"


# ---------------------------------------------------------------------------
# Dataset walker
# ---------------------------------------------------------------------------

def load_variant(variant_dir: Path) -> dict | None:
    """Load one variant. Returns None if any required file is missing."""
    slow_path = variant_dir / "slow.c"
    fast_path = variant_dir / "fast.c"
    meta_path = variant_dir / "metadata.json"

    for p in (slow_path, fast_path, meta_path):
        if not p.exists():
            print(f"  [skip] missing {p}", file=sys.stderr)
            return None

    with open(slow_path) as f:
        slow_code = f.read().strip()
    with open(fast_path) as f:
        fast_code = f.read().strip()
    with open(meta_path) as f:
        meta = json.load(f)

    return {"slow": slow_code, "fast": fast_code, "meta": meta,
            "variant_id": meta.get("variant_id", variant_dir.name)}


def iter_variants(dataset_dir: Path):
    """Yield variant dicts for every variant_dir found under dataset_dir."""
    for pattern_dir in sorted(dataset_dir.iterdir()):
        if not pattern_dir.is_dir():
            continue
        for variant_dir in sorted(pattern_dir.iterdir()):
            if not variant_dir.is_dir():
                continue
            v = load_variant(variant_dir)
            if v is not None:
                yield v


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_examples(variant: dict, strategies: list[str]) -> list[dict]:
    examples = []
    slow, fast, meta = variant["slow"], variant["fast"], variant["meta"]
    response = make_response(fast)

    for strategy in strategies:
        builder = PROMPT_BUILDERS[strategy]
        prompt = builder(slow, meta)
        examples.append({
            "messages": [
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": response},
            ],
            # Extra fields stripped before training but useful for debugging
            "_variant_id": variant["variant_id"],
            "_strategy":   strategy,
            "_difficulty": meta.get("difficulty", ""),
            "_pattern_id": meta.get("pattern_id", ""),
        })
    return examples


def print_stats(examples: list[dict], strategies: list[str]) -> None:
    from collections import Counter
    pattern_counts: Counter = Counter()
    difficulty_counts: Counter = Counter()
    strategy_counts: Counter = Counter()
    total_user_chars = 0
    total_asst_chars = 0

    for ex in examples:
        pattern_counts[ex["_pattern_id"]] += 1
        difficulty_counts[ex["_difficulty"]] += 1
        strategy_counts[ex["_strategy"]] += 1
        total_user_chars += len(ex["messages"][0]["content"])
        total_asst_chars += len(ex["messages"][1]["content"])

    print(f"\n{'─'*50}")
    print(f"  Total examples : {len(examples)}")
    print(f"  Strategies     : {strategies}")
    print(f"  Avg user chars : {total_user_chars // len(examples)}")
    print(f"  Avg asst chars : {total_asst_chars // len(examples)}")
    print(f"\n  By pattern:")
    for k, v in sorted(pattern_counts.items()):
        print(f"    {k:<12} {v}")
    print(f"\n  By difficulty:")
    for k, v in sorted(difficulty_counts.items()):
        print(f"    {k:<12} {v}")
    print(f"\n  By strategy:")
    for k, v in sorted(strategy_counts.items()):
        print(f"    {k:<20} {v}")
    print(f"{'─'*50}\n")


def write_jsonl(examples: list[dict], path: str, strip_meta: bool = True) -> None:
    with open(path, "w") as f:
        for ex in examples:
            record = {k: v for k, v in ex.items() if not (strip_meta and k.startswith("_"))}
            f.write(json.dumps(record) + "\n")
    print(f"Wrote {len(examples)} examples → {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert dataset/ into a JSONL fine-tuning file")
    parser.add_argument("--dataset", default="../dataset",
                        help="Path to dataset directory (default: ../dataset/)")
    parser.add_argument("--output", default="fine_tune_data.jsonl",
                        help="Output JSONL path (default: fine_tune_data.jsonl)")
    parser.add_argument("--strategies", nargs="+",
                        choices=list(PROMPT_BUILDERS.keys()),
                        default=["generic", "pattern-aware"],
                        help="Prompt strategies to include (default: generic pattern-aware)")
    parser.add_argument("--split", type=float, default=None,
                        help="If set (e.g. 0.9), split into train/val. "
                             "Requires --train and --val.")
    parser.add_argument("--train", default="train.jsonl",
                        help="Train split output path (used with --split)")
    parser.add_argument("--val", default="val.jsonl",
                        help="Validation split output path (used with --split)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stats", action="store_true",
                        help="Print dataset statistics and exit (no file written)")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset)
    if not dataset_dir.exists():
        print(f"ERROR: dataset directory not found: {dataset_dir}", file=sys.stderr)
        sys.exit(1)

    # Build examples
    all_examples: list[dict] = []
    n_variants = 0
    for variant in iter_variants(dataset_dir):
        n_variants += 1
        all_examples.extend(build_examples(variant, args.strategies))

    if not all_examples:
        print("ERROR: no examples built — check dataset/ structure", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {n_variants} variants → {len(all_examples)} examples "
          f"({len(args.strategies)} strategies × {n_variants} variants)")

    if args.stats:
        print_stats(all_examples, args.strategies)
        return

    # Shuffle before writing/splitting
    random.seed(args.seed)
    random.shuffle(all_examples)

    if args.split is not None:
        cut = int(len(all_examples) * args.split)
        train_ex = all_examples[:cut]
        val_ex   = all_examples[cut:]
        write_jsonl(train_ex, args.train)
        write_jsonl(val_ex,   args.val)
        print(f"Split: {len(train_ex)} train / {len(val_ex)} val")
    else:
        write_jsonl(all_examples, args.output)


if __name__ == "__main__":
    main()
