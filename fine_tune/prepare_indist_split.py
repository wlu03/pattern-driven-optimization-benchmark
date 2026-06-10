#!/usr/bin/env python3
"""prepare_indist_split.py — build a CLEAN variant-level in-distribution split.

The existing train/val split was random *by example*, so 255/273 val variants
also appear in train (leaked via other strategies) — useless as an in-distribution
held-out. This holds out whole BASE-pattern variants (all strategies) per pattern,
so the held-out set is a genuine in-distribution test the model never saw. COMP
variants stay entirely in training (they're part of the training distribution but
not the clean per-pattern in-dist probe).

Outputs:
  fine_tune/train_indist.jsonl              — training corpus (held-out variants removed)
  fine_tune/heldout_indist_variants.txt     — variant_ids of the in-distribution held-out

Usage:
  python3 fine_tune/prepare_indist_split.py --dataset dataset --holdout-frac 0.2
"""
import argparse
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepare_finetune_data import iter_variants, build_examples  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset")
    ap.add_argument("--strategies", nargs="+",
                    default=["generic", "pattern-aware", "taxonomy-guided"])
    ap.add_argument("--holdout-frac", type=float, default=0.2)
    ap.add_argument("--train-out", default="fine_tune/train_indist.jsonl")
    ap.add_argument("--heldout-ids", default="fine_tune/heldout_indist_variants.txt")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    # Group BASE-pattern variants by pattern_id; COMP -> all to training.
    by_pat = defaultdict(list)
    comp = []
    for v in iter_variants(Path(args.dataset)):
        pid = v["meta"].get("pattern_id", "?")
        (comp if pid.startswith("COMP") else by_pat[pid]).append(v)

    train_ex, heldout_ids = [], []
    for pid, vs in sorted(by_pat.items()):
        vs = sorted(vs, key=lambda x: x["variant_id"])
        rng.shuffle(vs)
        k = max(1, round(len(vs) * args.holdout_frac))
        for v in vs[:k]:
            heldout_ids.append(v["variant_id"])
        for v in vs[k:]:
            train_ex.extend(build_examples(v, args.strategies))
    for v in comp:  # COMP entirely in training
        train_ex.extend(build_examples(v, args.strategies))

    Path(args.train_out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.train_out, "w") as f:
        for ex in train_ex:
            f.write(json.dumps({"messages": ex["messages"]}) + "\n")
    with open(args.heldout_ids, "w") as f:
        f.write("\n".join(sorted(heldout_ids)) + "\n")

    print(f"base patterns: {len(by_pat)}  COMP variants (all to train): {len(comp)}")
    print(f"in-distribution held-out variants: {len(heldout_ids)}")
    print(f"train examples: {len(train_ex)} -> {args.train_out}")
    print(f"held-out ids -> {args.heldout_ids}")


if __name__ == "__main__":
    main()
