"""
equivalence.py
--------------
Differential semantic-equivalence testing for the 2x2 faithfulness verdict.

Tier 1 of the faithfulness cascade. Reuses the BENCH_N / BENCH_SEED /
BENCH_DIST hooks that every pattern harness already supports (see
patterns/_preamble.py) to run a model's output across multiple input
configurations and check whether it matches the harness's inline
`expected` computation on each one.

A model that hardcodes one input or special-cases one distribution will
pass under the default config but fail under a variation — this is what
the equivalence tier catches that single-input correctness misses.

Design rationale (verified citations in docs/implementation.tex):
  * Cascade architecture follows INVALIDATOR (IEEE TSE 2023, arXiv:2301.01113).
  * Multi-input differential testing follows Wu et al. (FSE 2025,
    arXiv:2504.04321): specify expected transformation up-front, verify
    equivalence via differential execution.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from pdob_core.compiler import compile_and_run, normalize_function_name, sanitize_llm_code


# Default sweep: size variation + seed diversity + IS-pattern distributions.
# Patterns that don't honor BENCH_DIST simply ignore it (no-op).
_DEFAULT_CONFIGS: list[dict] = [
    {"BENCH_N": "100000",  "BENCH_SEED": "42"},
    {"BENCH_N": "100000",  "BENCH_SEED": "7919"},
    {"BENCH_N": "1000000", "BENCH_SEED": "42"},
    {"BENCH_N": "1000000", "BENCH_SEED": "7919"},
    {"BENCH_N": "5000000", "BENCH_SEED": "42"},
    {"BENCH_N": "1000000", "BENCH_SEED": "42", "BENCH_DIST": "sorted"},
    {"BENCH_N": "1000000", "BENCH_SEED": "42", "BENCH_DIST": "reverse_sorted"},
    {"BENCH_N": "1000000", "BENCH_SEED": "42", "BENCH_DIST": "all_zero"},
    {"BENCH_N": "1000000", "BENCH_SEED": "42", "BENCH_DIST": "sparse"},
]


@dataclass
class EquivalenceResult:
    equivalent:     bool
    n_configs:      int
    n_correct:      int
    failed_configs: list[dict] = field(default_factory=list)
    compile_error:  Optional[str] = None

    @property
    def confidence(self) -> float:
        return 0.0 if self.compile_error else self.n_correct / max(self.n_configs, 1)

    def to_dict(self) -> dict:
        return {
            "equivalent":     self.equivalent,
            "n_configs":      self.n_configs,
            "n_correct":      self.n_correct,
            "confidence":     self.confidence,
            "failed_configs": self.failed_configs,
            "compile_error":  self.compile_error,
        }


def differential_equivalence(
    model_output:    str,
    test_harness:    str,
    n_inputs:        int = 9,
    configs:         Optional[list[dict]] = None,
    runs_per_config: int = 1,
    opt_level:       str = "O2",
) -> EquivalenceResult:
    """Run `model_output` through `test_harness` across multiple input configs.

    Returns equivalent=True iff model_output passes correctness on EVERY
    config. The harness's inline `expected` is computed from the math, not
    from the slow code, so equivalent=True means the output matches the
    correct answer across the sweep — independent of HOW the model achieved
    it. This is what makes the 2x2 verdict's FAITHFUL_ALTERNATIVE cell
    detectable: a model that vectorizes instead of hoisting still lands
    here as equivalent=True.
    """
    cfgs = (configs or _DEFAULT_CONFIGS)[:n_inputs]
    if not cfgs:
        return EquivalenceResult(equivalent=False, n_configs=0, n_correct=0,
                                 compile_error="no configs to test")

    code = sanitize_llm_code(
        normalize_function_name(model_output, test_harness),
        test_harness,
    )

    n_correct = 0
    failed: list[dict] = []
    compile_error: Optional[str] = None

    for i, cfg in enumerate(cfgs):
        env = {**os.environ, **cfg}
        r = compile_and_run(code, test_harness, runs=runs_per_config,
                            opt_level=opt_level, env=env)
        if not r.get("compiles"):
            # First-config compile failure is fatal — bail with diagnostic.
            # Later-config failures are unusual (env vars don't affect compile)
            # but treated as a failed config for that env.
            if i == 0:
                return EquivalenceResult(
                    equivalent=False, n_configs=0, n_correct=0,
                    compile_error=r.get("error", "")[:500],
                )
            failed.append(cfg)
            compile_error = r.get("error", "")[:500]
            continue
        if r.get("correct"):
            n_correct += 1
        else:
            failed.append(cfg)

    return EquivalenceResult(
        equivalent=(n_correct == len(cfgs)),
        n_configs=len(cfgs),
        n_correct=n_correct,
        failed_configs=failed,
        compile_error=compile_error,
    )


def differential_equivalence_on_variant(
    llm_code:        str,
    variant,                                # pdob_core.dataset_evaluator.VariantPaths
    n_inputs:        int = 9,
    configs:         Optional[list[dict]] = None,
    opt_level:       str = "O3",
    timeout_s:       int = 30,
) -> EquivalenceResult:
    """Dataset-path counterpart to `differential_equivalence`.

    Compiles the variant's on-disk slow.c, fast.c, test.c (+ optional
    helper.c) as separate translation units --- with test.c patched in
    memory by `scripts.bench_hooks.patch_test_c` so the binary honors
    the BENCH_N / BENCH_SEED env vars --- and runs it under each config.

    The LLM's code replaces the variant's slow function (renamed via the
    same mechanism as evaluate_variant uses). The harness's `correct=1`
    print signals semantic equivalence per config.

    Falls back to single-config canonical-input equivalence when:
      - bench_hooks can't patch the test.c (no `#define N`, VLA-incompatible,
        unparseable srand) — info["patched"] is False
      - the patched test.c fails to compile at the first config
    """
    import os
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    # Lazy imports to keep equivalence.py importable without bench_hooks
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.bench_hooks import patch_test_c
    from scripts.batch_test import extract_extern_decl
    from pdob_core.dataset_evaluator import extract_slow_function_name
    import re as _re

    cfgs = (configs or _DEFAULT_CONFIGS)[:n_inputs]
    if not cfgs:
        return EquivalenceResult(equivalent=False, n_configs=0, n_correct=0,
                                 compile_error="no configs to test")

    test_src = Path(variant.test_path).read_text()
    patched_test, info = patch_test_c(test_src)
    if not info.get("patched"):
        # No hooks injected — caller should fall back to canonical-input
        # equivalence; we signal this by running only the first config.
        cfgs = cfgs[:1]
        patched_test = test_src

    # Build per-TU sources. The LLM code substitutes the slow function;
    # we inject extern decls for the harness via the SLOW_CODE_HERE /
    # FAST_CODE_HERE markers exactly as scripts/batch_test does.
    slow_src = Path(variant.slow_path).read_text()
    fast_src = Path(variant.fast_path).read_text()
    helper_src = (Path(variant.helper_path).read_text()
                  if variant.helper_path else None)

    # The LLM's code stands in for slow — rename its function to match
    # what the variant's test.c expects to link against (e.g.
    # `slow_sr1_v000`). Without this, an LLM that names its function
    # `optimized` or `fast_sr1_v000` won't link.
    target_slow_name = extract_slow_function_name(slow_src)
    llm_for_slow = llm_code
    if target_slow_name:
        # Replace any plausible candidate (definition + calls) with the
        # target slow name. Heuristic: pick the first top-level function
        # definition in llm_code and rename it.
        m = _re.search(
            r"(?:^|\n)\s*(?:static\s+)?(?:[\w*\s]+?)\s+"
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            "\n" + llm_code,
        )
        if m and m.group(1) != target_slow_name:
            old = m.group(1)
            llm_for_slow = _re.sub(rf"\b{_re.escape(old)}\b",
                                    target_slow_name, llm_code)

    llm_ext  = extract_extern_decl(llm_for_slow) or ""
    fast_ext = extract_extern_decl(fast_src) or ""
    combined_test = (patched_test
                     .replace("// SLOW_CODE_HERE", llm_ext + ";")
                     .replace("// FAST_CODE_HERE", fast_ext + ";"))

    n_correct = 0
    failed: list[dict] = []
    compile_error: Optional[str] = None

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "test.c").write_text(combined_test)
        (tmp / "slow.c").write_text(llm_for_slow)   # LLM stands in for slow
        (tmp / "fast.c").write_text(fast_src)
        extras = []
        if helper_src is not None:
            (tmp / "helper.c").write_text(helper_src)
            extras = [str(tmp / "helper.c")]
        bin_path = tmp / "test_bin"
        cmd = ["gcc", f"-{opt_level}", "-fno-lto", "-o", str(bin_path),
               str(tmp / "test.c"), str(tmp / "slow.c"),
               str(tmp / "fast.c")] + extras + ["-lm"]
        try:
            cr = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return EquivalenceResult(
                equivalent=False, n_configs=0, n_correct=0,
                compile_error="compile timeout")
        if cr.returncode != 0:
            return EquivalenceResult(
                equivalent=False, n_configs=0, n_correct=0,
                compile_error=cr.stderr[-500:])

        for cfg in cfgs:
            env = {**os.environ, **cfg}
            try:
                rr = subprocess.run([str(bin_path)], capture_output=True,
                                    text=True, env=env, timeout=timeout_s)
            except subprocess.TimeoutExpired:
                failed.append(cfg)
                continue
            if rr.returncode != 0:
                failed.append(cfg); continue
            parts = dict(p.split("=") for p in rr.stdout.strip().split()
                         if "=" in p)
            if parts.get("correct", "0") == "1":
                n_correct += 1
            else:
                failed.append(cfg)

    return EquivalenceResult(
        equivalent=(n_correct == len(cfgs) and n_correct > 0),
        n_configs=len(cfgs),
        n_correct=n_correct,
        failed_configs=failed,
        compile_error=compile_error,
    )


def two_axis_verdict(structural, equivalence: EquivalenceResult):
    """Combine a structural FaithfulnessResult with an EquivalenceResult.

    Threshold for `expected_shape`:
      - FAITHFUL                → True
      - PARTIAL with score>=0.5 → True   (most checks hit; transform recognizably applied)
      - PARTIAL with score<0.5  → False
      - UNFAITHFUL / UNKNOWN    → False

    Routes to the four cells defined in faithfulness/checkers/_base.py:Cell.
    """
    from faithfulness.checkers._base import TwoAxisVerdict, Verdict
    if structural.verdict == Verdict.FAITHFUL:
        expected_shape = True
    elif structural.verdict == Verdict.PARTIAL:
        expected_shape = structural.score >= 0.5
    else:
        expected_shape = False

    return TwoAxisVerdict(
        equivalent=equivalence.equivalent,
        expected_shape=expected_shape,
        structural_result=structural,
        equivalence_result=equivalence,
    )
