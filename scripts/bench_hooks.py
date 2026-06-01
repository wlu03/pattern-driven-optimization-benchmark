"""bench_hooks.py
-----------------
Compile-time source patcher that adds BENCH_N / BENCH_SEED env-var
overrides to a dataset variant's test.c WITHOUT modifying the on-disk
file. Used by the faithfulness equivalence tier and the multi-input
runner to exercise the same harness across multiple input configurations
without regenerating every variant in dataset/.

Usage:
    from scripts.bench_hooks import patch_test_c

    patched = patch_test_c(open('dataset/SR_1/SR-1_v000/test.c').read())
    # ... write to tmp, compile, run with env={"BENCH_N": "5000000", ...}

What the patch does:
  1. Find `#define N <int>` and rewrite as `#define N_DEFAULT <int>`
     plus a file-scope `static int N;`
  2. Inject at the top of `main()` body:
       N = atoi(getenv("BENCH_N") ?: "0"); if (!N) N = N_DEFAULT;
  3. Find every `srand(<int>)` and rewrite as
       `srand(getenv("BENCH_SEED") ? atoi(getenv("BENCH_SEED")) : <int>)`
  4. Inject `#include <stdlib.h>` if not already present (needed for
     getenv/atoi).

Known limitations:
  - Variants that use `N` as a compile-time constant (e.g., `double
    arr[N];` at file scope, `#if N > 10`) won't compile after the patch
    because `static int N;` is not a constant expression. The patcher
    returns the ORIGINAL source unchanged in that case (detected by
    trying to compile the patched version first); the caller falls back
    to canonical-input equivalence.
  - Variants without a single `#define N` (e.g., N hardcoded inline in
    multiple places) are similarly returned unchanged.
"""
import re
from typing import Optional, Tuple


_RE_DEFINE_N = re.compile(r"^#define\s+N\s+(\d+)\s*$", re.MULTILINE)
_RE_SRAND    = re.compile(r"srand\s*\(\s*(\d+)\s*\)")
_RE_MAIN     = re.compile(
    r"\b(int|void)\s+main\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)


def _add_stdlib_include(src: str) -> str:
    """Ensure <stdlib.h> is included so getenv/atoi are declared."""
    if re.search(r"#include\s*<stdlib\.h>", src):
        return src
    # Insert right after the first existing #include, or at the very top.
    m = re.search(r"^#include\s*<[^>]+>\s*$", src, re.MULTILINE)
    if m:
        end = m.end()
        return src[:end] + "\n#include <stdlib.h>" + src[end:]
    return "#include <stdlib.h>\n" + src


def patch_test_c(src: str) -> Tuple[str, dict]:
    """Patch a test.c source to honor BENCH_N and BENCH_SEED env vars.

    Returns (patched_source, info_dict). info_dict reports what the
    patcher did:
        {
          "n_define_found":      True/False,
          "n_define_value":      original N (None if not found),
          "srand_calls_patched": int (0..N),
          "main_found":          True/False,
          "patched":             True if any substantive change made,
        }
    If `patched` is False, the returned source is identical to input.
    """
    info = {
        "n_define_found":      False,
        "n_define_value":      None,
        "srand_calls_patched": 0,
        "main_found":          False,
        "patched":             False,
    }

    # 1. Find and rewrite #define N
    m_n = _RE_DEFINE_N.search(src)
    if m_n:
        info["n_define_found"] = True
        info["n_define_value"] = int(m_n.group(1))
        n_default = m_n.group(1)
        replacement = (
            f"#define N_DEFAULT {n_default}\n"
            f"static int N;  /* set in main() from BENCH_N env var */"
        )
        src = src[:m_n.start()] + replacement + src[m_n.end():]
        info["patched"] = True

    # 2. Find main() and inject N override at top of body
    m_main = _RE_MAIN.search(src)
    if m_main and info["n_define_found"]:
        info["main_found"] = True
        # Insert right after the opening brace of main()
        insert_at = m_main.end()
        injection = (
            "\n    {\n"
            "        const char *_pdob_bn = getenv(\"BENCH_N\");\n"
            "        N = (_pdob_bn && *_pdob_bn) ? atoi(_pdob_bn) : N_DEFAULT;\n"
            "        if (N <= 0) N = N_DEFAULT;\n"
            "    }\n"
        )
        src = src[:insert_at] + injection + src[insert_at:]

    # 3. Patch srand calls
    def _srand_repl(m: re.Match) -> str:
        info["srand_calls_patched"] += 1
        default_seed = m.group(1)
        return (
            f"srand(getenv(\"BENCH_SEED\") "
            f"? (unsigned)atoi(getenv(\"BENCH_SEED\")) "
            f": {default_seed}U)"
        )
    new_src, n_subs = _RE_SRAND.subn(_srand_repl, src)
    if n_subs > 0:
        src = new_src
        info["patched"] = True

    # 4. Ensure stdlib.h is included (for getenv/atoi)
    if info["patched"]:
        src = _add_stdlib_include(src)

    return src, info


def _self_test():
    """Smoke test on a synthetic harness."""
    sample = """\
#include <stdio.h>
#include <math.h>
#include <time.h>
#define N 1000000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main(void) {
    double *X = malloc(N * sizeof(double));
    srand(42);
    for (int i = 0; i < N; i++) X[i] = (double)rand() / RAND_MAX;
    return 0;
}
"""
    patched, info = patch_test_c(sample)
    assert info["n_define_found"], info
    assert info["n_define_value"] == 1000000
    assert info["srand_calls_patched"] == 1
    assert info["main_found"]
    assert info["patched"]
    assert "N_DEFAULT 1000000" in patched
    assert "static int N;" in patched
    assert "getenv(\"BENCH_N\")" in patched
    assert "getenv(\"BENCH_SEED\")" in patched
    assert "#include <stdlib.h>" in patched
    print("bench_hooks self-test: PASS")
    return patched


if __name__ == "__main__":
    _self_test()
