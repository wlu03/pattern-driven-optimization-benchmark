"""Dataset-path evaluator.

Evaluates an LLM completion on a single dataset variant (slow.c / fast.c /
test.c / optional helper.c on disk), using the same multi-translation-unit
compile pattern as scripts/batch_test.py (with -fno-lto) so the compiler
cannot inline across file boundaries.

This is the "variant" counterpart to compiler.py's compile_and_run(), which
only handles the single-file patterns.py harnesses.
"""
import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Iterator, Optional

import os as _os
import sys as _sys

# Locate the repo root (one level above ``pdob_core/``) so we can import
# ``scripts.batch_test``.  Add to sys.path only if not already present.
_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

from scripts.batch_test import extract_extern_decl  # noqa: E402

# Headers prepended to slow.c if it doesn't already #include any.
_C_HEADERS = (
    "#include <stdio.h>\n"
    "#include <stdlib.h>\n"
    "#include <math.h>\n"
    "#include <string.h>\n\n"
)


@dataclass
class VariantPaths:
    variant_id: str
    pattern_id: str
    category: str
    pattern_name: str
    variant_desc: str
    difficulty: str
    metadata: dict
    root: str
    slow_path: str
    fast_path: str
    test_path: str
    helper_path: Optional[str]


def discover_variants(dataset_dir: str) -> Iterator[VariantPaths]:
    """Walk the dataset directory and yield one VariantPaths per variant."""
    for root, _dirs, files in os.walk(dataset_dir):
        if "metadata.json" not in files:
            continue
        if "slow.c" not in files or "fast.c" not in files or "test.c" not in files:
            continue
        meta_path = os.path.join(root, "metadata.json")
        with open(meta_path) as f:
            meta = json.load(f)
        helper_path = os.path.join(root, "helper.c")
        yield VariantPaths(
            variant_id=meta.get("variant_id", os.path.basename(root)),
            pattern_id=meta.get("pattern_id", "UNKNOWN"),
            category=meta.get("category", "Unknown"),
            pattern_name=meta.get("pattern_name", ""),
            variant_desc=meta.get("variant_desc", ""),
            difficulty=meta.get("difficulty", ""),
            metadata=meta,
            root=root,
            slow_path=os.path.join(root, "slow.c"),
            fast_path=os.path.join(root, "fast.c"),
            test_path=os.path.join(root, "test.c"),
            helper_path=helper_path if os.path.exists(helper_path) else None,
        )


def extract_slow_function_name(slow_code: str) -> Optional[str]:
    """Find the FIRST non-static top-level function name in slow.c.

    These variants name the entry point like `slow_sr1_v000`, `slow_al1_v000`,
    etc. We need this so we can rename `optimized` (from the LLM) to match
    what the variant's test.c expects to link against.

    Mirrors normalize_function_name's strategy but returns the name instead
    of rewriting.
    """
    # Strip preprocessor lines and __attribute__ noise; the inline cf3_guard
    # / expensive_sr1 helpers are typically `static` and will be skipped by
    # the regex below.
    pattern = re.compile(
        r"(?:^|\n)\s*(?!static\b)(?:[A-Za-z_]\w*[\s\*]+)+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{",
        re.MULTILINE,
    )
    keywords = {"if", "for", "while", "switch", "return", "sizeof", "do", "else"}
    for m in pattern.finditer(slow_code):
        name = m.group(1)
        if name in keywords:
            continue
        return name
    return None


def rename_optimized_to(code: str, target_name: str) -> str:
    """Rewrite the public C symbol `optimized` to `target_name`.

    Called on LLM output AFTER normalize_function_name has already renamed
    whatever the model called its function to `optimized`. We then do the
    second rename so the test.c harness (which calls e.g. `slow_sr1_v000`)
    can link against the LLM's code.
    """
    if not target_name or target_name == "optimized":
        return code
    return re.sub(r"\boptimized\b", target_name, code)


def _median(xs: list) -> float:
    if not xs:
        return 0.0
    sorted_xs = sorted(xs)
    n = len(sorted_xs)
    if n % 2 == 1:
        return sorted_xs[n // 2]
    return 0.5 * (sorted_xs[n // 2 - 1] + sorted_xs[n // 2])


def _mad(xs: list) -> float:
    """Median absolute deviation — robust spread estimator."""
    if not xs:
        return 0.0
    med = _median(xs)
    return _median([abs(x - med) for x in xs])


def _compile_multi_tu(
    tmp: str,
    test_src: str,
    slow_src: str,
    fast_src: str,
    extra_tus: list,
    opt_level: str,
    bin_path: str,
    compile_timeout: int = 30,
) -> tuple:
    """Compile (test.c, slow.c, fast.c [, helper.c]) as separate TUs with -fno-lto.

    Returns (compiled: bool, error: str).
    """
    cmd = (
        ["gcc", f"-{opt_level}", "-fno-lto", "-o", bin_path,
         test_src, slow_src, fast_src]
        + extra_tus
        + ["-lm"]
    )
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=compile_timeout)
    if r.returncode != 0:
        return False, r.stderr
    return True, ""


def _parse_variant_output(stdout: str) -> dict:
    parts = dict(p.split("=") for p in stdout.strip().split() if "=" in p)
    return {
        "slow_ms": float(parts.get("slow_ms", 0)),
        "fast_ms": float(parts.get("fast_ms", 0)),
        "correct": parts.get("correct", "0") == "1",
        "speedup": float(parts.get("speedup", 0)),
    }


def compile_and_run_variant(
    llm_code: str,
    variant: VariantPaths,
    *,
    runs: int = 10,
    opt_level: str = "O2",
    run_timeout: int = 120,
    compile_timeout: int = 30,
) -> dict:
    """Compile LLM code as a translation unit alongside the variant's
    fast.c / test.c / optional helper.c and run it `runs` times.

    The LLM code REPLACES slow.c — its function (renamed to the variant's
    expected `slow_<pattern>_v<NNN>` name by the caller) provides the symbol
    that test.c calls when it asks for the slow path.

    Returns a dict with:
      compiles: bool, correct: bool, error: str,
      llm_ms_median: float, llm_ms_mad: float, llm_ms_runs: list,
      ref_fast_ms_median: float, ref_fast_ms_mad: float, ref_fast_ms_runs: list,
      slow_ms_runs: list (the variant's own slow.c — not actually compiled
                          here, populated separately by run_reference_only).
    """
    # Read fast.c and extract its extern decl for test.c to link against.
    with open(variant.fast_path) as f:
        fast_src_body = f.read()
    with open(variant.test_path) as f:
        test_src_body = f.read()

    fast_decl = extract_extern_decl(fast_src_body)
    # The LLM code provides the "slow" symbol (renamed by caller). The decl
    # in test.c for the slow function is built from the LLM's renamed
    # signature — we mirror it by extracting from the LLM code itself so we
    # match parameter types exactly.
    slow_decl = extract_extern_decl(llm_code)

    test_with_decls = (
        test_src_body
        .replace("// SLOW_CODE_HERE", slow_decl)
        .replace("// FAST_CODE_HERE", fast_decl)
    )

    with tempfile.TemporaryDirectory() as tmp:
        slow_src = os.path.join(tmp, "slow.c")  # = LLM code (replaces variant's slow)
        fast_src = os.path.join(tmp, "fast.c")
        test_src = os.path.join(tmp, "test.c")

        # Prepend headers to LLM code if it doesn't have any. The LLM may
        # already #include things; if so, leave it alone.
        prefix = _C_HEADERS if "#include" not in llm_code else ""
        with open(slow_src, "w") as f:
            f.write(prefix + llm_code)

        fast_prefix = _C_HEADERS if "#include" not in fast_src_body else ""
        with open(fast_src, "w") as f:
            f.write(fast_prefix + fast_src_body)

        with open(test_src, "w") as f:
            f.write(test_with_decls)

        extra_tus = [variant.helper_path] if variant.helper_path else []
        bin_path = os.path.join(tmp, f"test_{opt_level}")
        try:
            compiled, err = _compile_multi_tu(
                tmp, test_src, slow_src, fast_src, extra_tus,
                opt_level, bin_path, compile_timeout=compile_timeout,
            )
        except subprocess.TimeoutExpired:
            return {"compiles": False, "correct": False,
                    "error": "compile timeout"}
        if not compiled:
            return {"compiles": False, "correct": False, "error": err}

        slow_ms_runs = []
        fast_ms_runs = []
        correct = False
        for _ in range(runs):
            try:
                r = subprocess.run(
                    [bin_path], capture_output=True, text=True, timeout=run_timeout,
                )
            except subprocess.TimeoutExpired:
                return {"compiles": True, "correct": False,
                        "error": f"runtime timeout (>{run_timeout}s)"}
            if r.returncode != 0:
                return {"compiles": True, "correct": False,
                        "error": f"runtime exit={r.returncode}: {r.stderr[:200]}"}
            parsed = _parse_variant_output(r.stdout)
            correct = parsed["correct"]  # latest run; consistent across runs
            if parsed["slow_ms"] > 0:
                slow_ms_runs.append(parsed["slow_ms"])
            if parsed["fast_ms"] > 0:
                fast_ms_runs.append(parsed["fast_ms"])

        return {
            "compiles": True,
            "correct": correct,
            "error": "",
            "llm_ms_median": _median(slow_ms_runs),
            "llm_ms_mad": _mad(slow_ms_runs),
            "llm_ms_runs": slow_ms_runs,
            "ref_fast_ms_median": _median(fast_ms_runs),
            "ref_fast_ms_mad": _mad(fast_ms_runs),
            "ref_fast_ms_runs": fast_ms_runs,
        }


def compile_and_run_reference(
    variant: VariantPaths,
    *,
    runs: int = 10,
    opt_level: str = "O2",
    run_timeout: int = 120,
    compile_timeout: int = 30,
) -> dict:
    """Compile the variant's ORIGINAL slow.c (not LLM code) alongside fast.c
    and test.c, run `runs` times. Used to get the variant's true reference
    slow_ms (the LLM run uses the LLM code in place of slow.c, so we measure
    the variant's slow path here separately).

    Returns:
      compiles, correct, error, slow_ms_median, slow_ms_mad, slow_ms_runs,
      fast_ms_median, fast_ms_mad, fast_ms_runs.
    """
    with open(variant.slow_path) as f:
        slow_body = f.read()
    with open(variant.fast_path) as f:
        fast_body = f.read()
    with open(variant.test_path) as f:
        test_body = f.read()

    slow_decl = extract_extern_decl(slow_body)
    fast_decl = extract_extern_decl(fast_body)
    test_with_decls = (
        test_body
        .replace("// SLOW_CODE_HERE", slow_decl)
        .replace("// FAST_CODE_HERE", fast_decl)
    )

    with tempfile.TemporaryDirectory() as tmp:
        slow_src = os.path.join(tmp, "slow.c")
        fast_src = os.path.join(tmp, "fast.c")
        test_src = os.path.join(tmp, "test.c")
        with open(slow_src, "w") as f:
            prefix = _C_HEADERS if "#include" not in slow_body else ""
            f.write(prefix + slow_body)
        with open(fast_src, "w") as f:
            prefix = _C_HEADERS if "#include" not in fast_body else ""
            f.write(prefix + fast_body)
        with open(test_src, "w") as f:
            f.write(test_with_decls)
        extra_tus = [variant.helper_path] if variant.helper_path else []
        bin_path = os.path.join(tmp, f"ref_{opt_level}")
        try:
            compiled, err = _compile_multi_tu(
                tmp, test_src, slow_src, fast_src, extra_tus,
                opt_level, bin_path, compile_timeout=compile_timeout,
            )
        except subprocess.TimeoutExpired:
            return {"compiles": False, "correct": False, "error": "compile timeout"}
        if not compiled:
            return {"compiles": False, "correct": False, "error": err}

        slow_runs = []
        fast_runs = []
        correct = False
        for _ in range(runs):
            try:
                r = subprocess.run(
                    [bin_path], capture_output=True, text=True, timeout=run_timeout,
                )
            except subprocess.TimeoutExpired:
                return {"compiles": True, "correct": False,
                        "error": f"runtime timeout (>{run_timeout}s)"}
            if r.returncode != 0:
                return {"compiles": True, "correct": False,
                        "error": f"runtime exit={r.returncode}: {r.stderr[:200]}"}
            parsed = _parse_variant_output(r.stdout)
            correct = parsed["correct"]
            if parsed["slow_ms"] > 0:
                slow_runs.append(parsed["slow_ms"])
            if parsed["fast_ms"] > 0:
                fast_runs.append(parsed["fast_ms"])

        return {
            "compiles": True,
            "correct": correct,
            "error": "",
            "slow_ms_median": _median(slow_runs),
            "slow_ms_mad": _mad(slow_runs),
            "slow_ms_runs": slow_runs,
            "fast_ms_median": _median(fast_runs),
            "fast_ms_mad": _mad(fast_runs),
            "fast_ms_runs": fast_runs,
        }


def geometric_mean(xs: list) -> Optional[float]:
    """exp(mean(log(x))) over positive values. Returns None if empty.

    Use this for averaging speedup ratios — arithmetic mean is wrong for
    ratios because (2x and 0.5x) should average to 1.0, not 1.25.
    """
    positives = [x for x in xs if x is not None and x > 0]
    if not positives:
        return None
    return math.exp(sum(math.log(x) for x in positives) / len(positives))
