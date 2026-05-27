import re


# ─────────────────────────────────────────────────────────────────────────
# Multi-input runtime preamble (Issue A — item 4) + tolerance helper (B/10)
#
# Injected at the top of every PatternEntry.test_harness so each harness can
# be re-run with different (n, seed, distribution) configurations from the
# outside via environment variables — without touching the bench loop:
#
#   BENCH_N        — override default n (size of input)
#   BENCH_SEED     — override default srand() seed
#   BENCH_DIST     — for IS-* patterns: "random" (default), "sorted",
#                    "reverse_sorted", "all_zero", "sparse"
#
# Backward compatibility: when the env vars are unset, _bench_n / _bench_seed
# return the existing hardcoded defaults, so behavior is byte-identical to
# the pre-change benchmark (existing CSVs remain comparable).
#
# Also exposes:
#   _bench_close(a, b, atol, rtol)
#     Combined absolute + relative tolerance check. Replaces the previous
#     purely-relative checks (which failed on tiny magnitudes) and the
#     dataset's purely-absolute checks (which failed on large magnitudes).
#     For double patterns use (1e-9, 1e-6); for float32 (1e-6, 1e-4).
# ─────────────────────────────────────────────────────────────────────────
_HARNESS_PREAMBLE = r"""
/* ── bench harness preamble (auto-injected) ───────────────────────────── */
#include <string.h>
static int _bench_n(int default_n) {
    const char *e = getenv("BENCH_N");
    return e ? atoi(e) : default_n;
}
static unsigned _bench_seed(unsigned default_seed) {
    const char *e = getenv("BENCH_SEED");
    return e ? (unsigned)atoi(e) : default_seed;
}
static const char *_bench_dist(void) {
    const char *e = getenv("BENCH_DIST");
    return e ? e : "random";
}
/* Fill `arr` (length n) with values from one of several distributions, all
   bounded to [lo, hi] (random/sparse) or determined by n (sorted variants).
   Only IS-* harnesses actually swap their fill loop for this helper; other
   harnesses tolerate BENCH_DIST being set without crashing because they
   simply ignore it.  Distributions:
     "random"          — uniform random in [lo, hi]   (default)
     "sorted"          — arr[i] = lo + (hi-lo)*i/(n-1)
     "reverse_sorted"  — arr[i] = lo + (hi-lo)*(n-1-i)/(n-1)
     "all_zero"        — arr[i] = 0
     "sparse"          — 95% zeros, 5% uniform in [lo, hi]                  */
static void _bench_fill_dist(double *arr, int n, double lo, double hi) {
    const char *d = _bench_dist();
    double span = hi - lo;
    if (strcmp(d, "sorted") == 0) {
        for (int i = 0; i < n; i++)
            arr[i] = (n > 1) ? lo + span * ((double)i / (double)(n - 1)) : lo;
    } else if (strcmp(d, "reverse_sorted") == 0) {
        for (int i = 0; i < n; i++)
            arr[i] = (n > 1) ? lo + span * ((double)(n - 1 - i) / (double)(n - 1)) : lo;
    } else if (strcmp(d, "all_zero") == 0) {
        for (int i = 0; i < n; i++) arr[i] = 0.0;
    } else if (strcmp(d, "sparse") == 0) {
        for (int i = 0; i < n; i++)
            arr[i] = (rand() % 100 < 95) ? 0.0 : (lo + span * ((double)rand() / RAND_MAX));
    } else { /* "random" (default) and any unknown value */
        for (int i = 0; i < n; i++)
            arr[i] = lo + span * ((double)rand() / RAND_MAX);
    }
}
/* Int variant for sort/integer harnesses (IS-4 etc.) */
static void _bench_fill_dist_int(int *arr, int n, int lo, int hi) {
    const char *d = _bench_dist();
    int span = (hi > lo) ? (hi - lo) : 1;
    if (strcmp(d, "sorted") == 0) {
        for (int i = 0; i < n; i++)
            arr[i] = lo + (int)((long long)span * i / (n > 1 ? n - 1 : 1));
    } else if (strcmp(d, "reverse_sorted") == 0) {
        for (int i = 0; i < n; i++)
            arr[i] = lo + (int)((long long)span * (n - 1 - i) / (n > 1 ? n - 1 : 1));
    } else if (strcmp(d, "all_zero") == 0) {
        for (int i = 0; i < n; i++) arr[i] = 0;
    } else if (strcmp(d, "sparse") == 0) {
        for (int i = 0; i < n; i++)
            arr[i] = (rand() % 100 < 95) ? 0 : (lo + rand() % span);
    } else {
        for (int i = 0; i < n; i++)
            arr[i] = lo + rand() % span;
    }
}
/* Combined absolute + relative tolerance: handles both tiny and huge
   magnitudes correctly. Returns 1 iff |a - b| <= atol + rtol*|b|.        */
static inline int _bench_close(double a, double b, double atol, double rtol) {
    double d = a - b; if (d < 0) d = -d;
    double mb = b; if (mb < 0) mb = -mb;
    return d <= atol + rtol * mb;
}
/* macOS / Apple Silicon: there is no `taskset` analogue. The best we can do
   is bias the scheduler toward performance cores via the QoS class. Runs
   automatically before main() so every harness picks up the hook without
   editing each one individually. On non-Apple platforms this is a no-op
   that the linker discards. */
#ifdef __APPLE__
#include <pthread.h>
#include <sys/qos.h>
__attribute__((constructor))
static void _bench_macos_init(void) {
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INTERACTIVE, 0);
}
#endif
/* ── end preamble ─────────────────────────────────────────────────────── */
"""


def _apply_preamble(harness: str) -> str:
    """Inject the multi-input + tolerance preamble into a test_harness.

    The preamble is injected after the include block. We also do the
    n/seed substitutions that are uniform across (almost) all harnesses:
      int n = X;     -> int n = _bench_n(X);
      int n = X, ... -> int n = _bench_n(X), ...
      srand(42);     -> srand(_bench_seed(42));
    Harnesses without `srand(...)` (e.g. AL-1 / AL-4 which take a small
    fixed integer) and those without an `int n = ` line (CF-3/CF-4 use
    deterministic data — handled specially) are left to per-harness edits.
    """
    # Inject preamble right after the last #include directive
    lines = harness.split('\n')
    last_include_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('#include'):
            last_include_idx = i
    if last_include_idx >= 0:
        lines.insert(last_include_idx + 1, _HARNESS_PREAMBLE)
    harness = '\n'.join(lines)

    # int n = NNN;  ->  int n = _bench_n(NNN);
    harness = re.sub(
        r'\bint\s+n\s*=\s*(\d+)\s*;',
        r'int n = _bench_n(\1);',
        harness
    )
    # int n = NNN, m = MMM;
    harness = re.sub(
        r'\bint\s+n\s*=\s*(\d+)\s*,\s*m\s*=\s*(\d+)\s*;',
        r'int n = _bench_n(\1), m = \2;',
        harness
    )
    # srand(NN);  ->  srand(_bench_seed(NN));
    harness = re.sub(
        r'\bsrand\s*\(\s*(\d+)\s*\)\s*;',
        r'srand(_bench_seed(\1));',
        harness
    )
    return harness
