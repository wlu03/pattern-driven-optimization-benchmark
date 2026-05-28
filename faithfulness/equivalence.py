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
