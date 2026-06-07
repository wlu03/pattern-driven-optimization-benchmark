"""score_completions.py
----------------------
Score pre-computed LLM completions (e.g., from Modal inference) without
re-invoking the model. Reads a CSV with columns
``variant_id, raw_output`` and produces the full EvalResult CSV that
faithfulness/report_2x2.py and scripts/transfer_analysis.py consume.

This decouples expensive GPU inference (run on Modal) from cheap
compile+run scoring (run on the laptop), so you can iterate on scoring
methodology without paying for new inference passes.

Usage:
    python3 scripts/score_completions.py \
        results/qwen25_coder_7b_taxonomy_raw.csv \
        --dataset dataset \
        --strategy taxonomy-guided \
        --model qwen2.5-coder-7b \
        --output results/qwen25_coder_7b_taxonomy_scored.csv

Input CSV columns (minimum): variant_id, raw_output
Optional columns passed through if present: model, strategy, hw_target,
pattern_id, category.
"""
import argparse
import csv
import os
import sys
from dataclasses import asdict

# Repo root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdob_core.dataset_evaluator import discover_variants  # noqa: E402
from pdob_core.evaluator import evaluate_variant  # noqa: E402
from pdob_core.patterns import PATTERNS  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────
# Byte-level-BPE auto-decode guard
#
# Byte-level BPE tokenizers (Llama, DeepSeek-R1-Distill-Llama, GPT-2, RoBERTa,
# ...) can't carry raw control/whitespace bytes inside token strings, so they
# map every byte to a printable stand-in: space (0x20) -> "Ġ", newline (0x0A)
# -> "Ċ", and so on. The final detokenizer step reverses that mapping. When it
# is skipped upstream (a Modal/vLLM detokenizer glitch hit the Llama-tokenizer
# 70B), raw_output arrives stuck in this intermediate form ("ĊOkay,ĠsoĠI...")
# and code extraction finds nothing -> the whole cell silently scores 0%.
#
# This guard detects that form and reverses it at load time, so a recurrence
# self-heals instead of needing a manual re-decode + re-score. The byte<->char
# table below is the standard byte-level-BPE alphabet (stdlib only — no
# tokenizer/transformers dependency, which this script must avoid).
# ──────────────────────────────────────────────────────────────────────────
def _byte_level_bpe_char_to_byte() -> dict:
    """Map each printable byte-level-BPE stand-in character back to its byte."""
    printable = (list(range(ord("!"), ord("~") + 1)) +
                 list(range(ord("¡"), ord("¬") + 1)) +
                 list(range(ord("®"), ord("ÿ") + 1)))
    chars = printable[:]
    n = 0
    for b in range(256):
        if b not in printable:
            printable.append(b)
            chars.append(256 + n)
            n += 1
    return {chr(c): b for b, c in zip(printable, chars)}


_BLBPE_CHAR_TO_BYTE = _byte_level_bpe_char_to_byte()


def _looks_byte_level_bpe(s: str) -> bool:
    """True iff ``s`` is byte-level-BPE-encoded rather than plain text.

    Encoded text maps every space to "Ġ" and every newline to "Ċ", so it
    carries those markers and contains NO literal space. Any real completion
    (C code + English reasoning) always has literal spaces, so this never
    false-positives on clean output.
    """
    return bool(s) and (("Ġ" in s) or ("Ċ" in s)) and (" " not in s)


def maybe_decode_byte_level_bpe(s: str) -> str:
    """Reverse byte-level-BPE encoding if present; otherwise return ``s`` as-is.

    Idempotent: plain text is returned unchanged.
    """
    if not _looks_byte_level_bpe(s):
        return s
    out = bytearray()
    for ch in s:
        b = _BLBPE_CHAR_TO_BYTE.get(ch)
        if b is None:
            out.extend(ch.encode("utf-8"))   # pass any unmapped char through
        else:
            out.append(b)
    return out.decode("utf-8", errors="replace")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input_csv",
                   help="Raw completions CSV from Modal (must have variant_id "
                        "and raw_output columns)")
    p.add_argument("--dataset", default="dataset",
                   help="Dataset root (default: dataset)")
    p.add_argument("--strategy", default="taxonomy-guided")
    p.add_argument("--model", default="unknown",
                   help="Model name (overridden by CSV column if present)")
    p.add_argument("--hw-target", default="generic")
    p.add_argument("--runs", type=int, default=10,
                   help="Timing runs per measurement (default 10)")
    p.add_argument("--max-retries", type=int, default=1,
                   help="Compile-retry attempts (default 1 since the raw "
                        "completion is already final)")
    p.add_argument("--output", default=None,
                   help="Output CSV path (default: <input>_scored.csv)")
    p.add_argument("--faithfulness", action="store_true",
                   help="Also run the 2x2 faithfulness cascade per variant")
    args = p.parse_args()

    # Guard: the 2x2 faithfulness cascade's structural axis is AST-based and
    # needs pycparser. Without it, check_faithfulness silently returns UNKNOWN
    # for every row -> faithfulness_expected_shape is False everywhere and the
    # cell collapses to FAITHFUL_ALTERNATIVE/FAILED (never FAITHFUL/
    # STRUCTURAL_ONLY). That degradation is invisible in the output, so a whole
    # sweep can be scored with dead faithfulness. Fail loudly instead — there is
    # nothing to self-heal. (Run under an interpreter that has pycparser, e.g.
    # base python3, not a venv missing it.)
    if args.faithfulness:
        try:
            import pycparser  # noqa: F401
        except ImportError:
            raise SystemExit(
                "--faithfulness requires pycparser (the structural checkers are "
                "AST-based); it is not importable under this interpreter "
                f"({sys.executable}). Without it every row would score as "
                "structurally unfaithful. Install it (`pip install pycparser`) "
                "or run with an interpreter that has it.")

    out_path = args.output or args.input_csv.replace(".csv", "_scored.csv")
    if out_path == args.input_csv:
        out_path = args.input_csv + ".scored.csv"

    # Load raw completions
    raw_rows = []
    with open(args.input_csv) as f:
        for r in csv.DictReader(f):
            if "variant_id" not in r or "raw_output" not in r:
                raise SystemExit(
                    f"Input CSV missing required columns 'variant_id' and "
                    f"'raw_output'; got {list(r.keys())}")
            raw_rows.append(r)
    print(f"Loaded {len(raw_rows)} raw completions from {args.input_csv}")

    # Map variants on disk
    by_vid = {v.variant_id: v for v in discover_variants(args.dataset)}
    print(f"Discovered {len(by_vid)} active variants under {args.dataset}/")

    missing = [r["variant_id"] for r in raw_rows
               if r["variant_id"] not in by_vid]
    if missing:
        print(f"WARNING: {len(missing)} variants in CSV not found on disk "
              f"(skipped). First 5: {missing[:5]}")
    raw_rows = [r for r in raw_rows if r["variant_id"] in by_vid]

    pattern_lookup = {p.pattern_id: p for p in PATTERNS}
    # Regex to split out <think>...</think> CoT blocks from the main
    # text. Reasoning models that don't have vLLM's reasoning_content
    # extractor active (e.g. older vLLM where enable_reasoning kwarg
    # was rejected) emit their CoT inline; we split it out at scoring
    # time so the C-extraction pipeline doesn't trip on the prose.
    import re as _re
    _THINK_RE = _re.compile(r'<think>(.*?)</think>\s*', _re.DOTALL)
    _THINK_OPEN_RE = _re.compile(r'<think>(.*)$', _re.DOTALL)

    results = []
    n_decoded = 0
    for i, r in enumerate(raw_rows, 1):
        vp = by_vid[r["variant_id"]]
        precomputed_text = r["raw_output"]
        precomputed_reasoning = r.get("raw_reasoning") or None

        # Self-heal byte-level-BPE-encoded completions (see guard above): an
        # upstream detokenizer glitch can leave raw_output as "ĊOkay,ĠI...".
        if _looks_byte_level_bpe(precomputed_text):
            precomputed_text = maybe_decode_byte_level_bpe(precomputed_text)
            if precomputed_reasoning:
                precomputed_reasoning = maybe_decode_byte_level_bpe(
                    precomputed_reasoning)
            n_decoded += 1

        # Fallback: extract <think>...</think> from main text if reasoning
        # wasn't already separated by the inference pipeline.
        if "<think>" in precomputed_text and not precomputed_reasoning:
            m = _THINK_RE.search(precomputed_text)
            if m:
                # Closed tag: split cleanly.
                precomputed_reasoning = m.group(1).strip()
                precomputed_text = _THINK_RE.sub('', precomputed_text).strip()
            else:
                # Unclosed: model ran out of tokens while thinking.
                # Everything after <think> is reasoning; main text is
                # whatever came before (usually empty). This row will
                # likely fail compile — that's the correct outcome,
                # because the model never produced code.
                m2 = _THINK_OPEN_RE.search(precomputed_text)
                if m2:
                    precomputed_reasoning = m2.group(1).strip()
                    precomputed_text = _THINK_OPEN_RE.sub('', precomputed_text).strip()

        # call_llm_fn signature: (prompt: str, model: str) -> str
        # The pre-computed text is returned regardless of which prompt the
        # retry loop constructs — we're just replaying the inference.
        # Reasoning trace is captured via the get_last_reasoning_trace()
        # hook that pdob_core.evaluator reads after each call_llm_fn call;
        # we monkey-patch the module-level _last variable for that hook
        # to surface the pre-computed reasoning.
        from pdob_core import models as _m
        def fake_llm(prompt: str, model: str) -> str:
            if precomputed_reasoning:
                _m._LAST_REASONING_TRACE = precomputed_reasoning
            return precomputed_text

        model = r.get("model") or args.model
        strategy = r.get("strategy") or args.strategy
        hw_target = r.get("hw_target") or args.hw_target

        try:
            eval_result = evaluate_variant(
                vp, model, strategy, fake_llm,
                pattern_lookup=pattern_lookup,
                hw_target=hw_target,
                max_retries=args.max_retries,
                runs=args.runs,
                faithfulness=args.faithfulness,
            )
            # Ensure reasoning_trace lands on the result regardless of
            # whether evaluate_variant's hook fired (the dataset path
            # currently doesn't read it).
            if precomputed_reasoning and not getattr(eval_result,
                                                     "reasoning_trace", None):
                eval_result.reasoning_trace = precomputed_reasoning
            results.append(eval_result)
        except Exception as e:
            print(f"  [{i}/{len(raw_rows)}] {vp.variant_id} FAILED: {e}",
                  file=sys.stderr)
            continue
        if i % 25 == 0 or i == len(raw_rows):
            print(f"  [{i}/{len(raw_rows)}] scored")

    if n_decoded:
        print(f"[guard] auto-decoded {n_decoded}/{len(raw_rows)} byte-level-BPE "
              f"completions (upstream detokenizer glitch — self-healed)")

    if not results:
        raise SystemExit("No results scored — nothing to write.")

    # Write the full EvalResult CSV
    fieldnames = list(asdict(results[0]).keys())
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in results:
            w.writerow(asdict(r))
    print(f"\nWrote {len(results)} scored rows -> {out_path}")

    # Quick summary
    correct = sum(1 for r in results if r.correct)
    compiles = sum(1 for r in results if r.compiles)
    print(f"Compilation rate: {compiles}/{len(results)} "
          f"({100*compiles/len(results):.1f}%)")
    print(f"Correctness rate: {correct}/{len(results)} "
          f"({100*correct/len(results):.1f}%)")
    if correct:
        speedups = [r.speedup_vs_slow for r in results
                    if r.correct and r.speedup_vs_slow > 0]
        if speedups:
            import statistics
            print(f"Median speedup (correct): "
                  f"{statistics.median(speedups):.2f}x")


if __name__ == "__main__":
    main()
