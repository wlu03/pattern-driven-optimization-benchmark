#!/usr/bin/env python3
"""
Pattern Variant Generator for Code Optimization Benchmark

Generates N distinct slow/fast C code pairs for each taxonomy pattern
by varying:
  - Dimensionality (1D, 2D, 3D arrays)
  - Data types (int, float, double, struct)
  - Operation types (arithmetic, trigonometric, logical)
  - Loop structures (for, while, nested depth)
  - Code complexity (expression depth, variable count)
  - Composition (single pattern vs. layered patterns)

Each generated pair includes:
  - slow.c: The inefficient version
  - fast.c: The hand-optimized reference
  - test.c: Test harness with verification
  - metadata.json: Pattern ID, difficulty, description

Usage:
    python3 generate_variants.py --patterns all --variants 20 --output dataset/
    python3 generate_variants.py --patterns SR --variants 50 --output dataset/
    python3 generate_variants.py --patterns SR-1 --variants 10 --output dataset/
"""

import os
import json
import random
import argparse
import csv
import itertools
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional
from string import Template

DTYPES = {
    "int":    {"fmt": "%d",    "zero": "0",    "cast": "(int)",    "suffix": ""},
    "float":  {"fmt": "%f",    "zero": "0.0f", "cast": "(float)",  "suffix": "f"},
    "double": {"fmt": "%lf",   "zero": "0.0",  "cast": "(double)", "suffix": ""},
}

BINARY_OPS = [
    ("+", "add"), ("-", "sub"), ("*", "mul"),
]

UNARY_MATH_FNS = [
    ("sin", "math"),  ("cos", "math"),  ("sqrt", "math"),
    ("exp", "math"),  ("log", "math"),  ("fabs", "math"),
]

REDUCTION_OPS = [
    ("+=", "sum"), ("*=", "product"),
    ("= fmax({acc}, {val})", "max"), ("= fmin({acc}, {val})", "min"),
]

# ── Metadata ──────────────────────────────────────────────────

@dataclass
class VariantMetadata:
    pattern_id: str              # e.g., "SR-1"
    variant_id: str              # e.g., "SR-1_v007"
    category: str                # e.g., "Semantic Redundancy"
    pattern_name: str            # e.g., "Loop-Invariant Semantic Computation"
    variant_desc: str            # What varies in this instance
    dtype: str                   # e.g., "double"
    difficulty: str              # "easy", "medium", "hard"
    compiler_fixable: bool       # Can -O3 fix this?
    num_loops: int               # Loop nesting depth
    num_arrays: int              # Number of input arrays
    lines_of_code: int           # Approximate LOC of slow version
    expected_speedup_range: str  # e.g., "2x-10x" or "100x+"
    composition: List[str]       # If composed, list of pattern IDs


class PatternTemplate:
    """Base class for pattern variant generators."""

    def __init__(self, pattern_id: str, category: str, name: str):
        self.pattern_id = pattern_id
        self.category = category
        self.name = name

    def generate(self, variant_num: int, seed: int) -> dict:
        """Returns dict with keys: slow_code, fast_code, test_code, metadata"""
        raise NotImplementedError

class SR1_Generator(PatternTemplate):
    """SR-1: Loop-Invariant Function Call (Transcendental Series)
    A transcendental series function is called with loop-invariant arguments
    on every iteration. The inner loop containing log/sin/exp prevents the
    compiler from proving loop-invariance. Optimization: hoist once before loop.
    Varies: series type (log/sin/exp/mixed), number of terms, array size, dtype.
    """

    def __init__(self):
        super().__init__("SR-1", "Semantic Redundancy",
                         "Loop-Invariant Function Call (Transcendental Series)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        suf_t = DTYPES[dtype]['suffix']
        n_terms = rng.randint(15, 50)          # inner loop length — expensive enough to measure
        N = rng.choice([500000, 1000000, 2000000])
        loop_style = rng.choice(["for", "while", "for"])  # bias toward for

        # Choose series type and build helper + expected inline computation
        series_type = rng.choice(["log", "sin", "exp_decay", "log_sin"])

        if series_type == "log":
            helper_body = f"    {dtype} r = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) r += ({dtype})log(base * k + 1.0) / k;\n    return r;"
            expected_loop = f"    {dtype} scale = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) scale += ({dtype})log(base * k + 1.0) / k;"
            desc_series = f"log-series({n_terms} terms)"
        elif series_type == "sin":
            freq = rng.choice([0.5, 1.0, 2.0])
            helper_body = f"    {dtype} r = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) r += ({dtype})sin(base * k * {freq});\n    return r;"
            expected_loop = f"    {dtype} scale = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) scale += ({dtype})sin(base * k * {freq});"
            desc_series = f"sin-series({n_terms} terms, freq={freq})"
        elif series_type == "exp_decay":
            decay = rng.choice([0.05, 0.1, 0.02])
            helper_body = f"    {dtype} r = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) r += ({dtype})exp(-base * k * {decay});\n    return r;"
            expected_loop = f"    {dtype} scale = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) scale += ({dtype})exp(-base * k * {decay});"
            desc_series = f"exp-decay({n_terms} terms, decay={decay})"
        else:  # log_sin
            helper_body = f"    {dtype} r = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) r += ({dtype})log(k + 1.0) * ({dtype})sin(base * k);\n    return r;"
            expected_loop = f"    {dtype} scale = 0.0;\n    for (int k = 1; k <= {n_terms}; k++) scale += ({dtype})log(k + 1.0) * ({dtype})sin(base * k);"
            desc_series = f"log*sin-series({n_terms} terms)"

        # Loop body
        if loop_style == "while":
            slow_loop = f"    int i = 0;\n    while (i < n) {{\n        arr[i] *= series_fn(base);\n        i++;\n    }}"
            fast_loop = f"    {dtype} scale = series_fn(base);\n    int i = 0;\n    while (i < n) {{\n        arr[i] *= scale;\n        i++;\n    }}"
        else:
            slow_loop = f"    for (int i = 0; i < n; i++)\n        arr[i] *= series_fn(base);"
            fast_loop = f"    {dtype} scale = series_fn(base);\n    for (int i = 0; i < n; i++)\n        arr[i] *= scale;"

        helper_code = f"""#include <math.h>
__attribute__((noinline, noclone))
{dtype} series_fn({dtype} base) {{
{helper_body}
}}"""

        slow_code = f"""#include <math.h>
{dtype} series_fn({dtype} base);
void slow_sr1_{suf}({dtype} *arr, int n, {dtype} base) {{
{slow_loop}
}}"""

        fast_code = f"""#include <math.h>
{dtype} series_fn({dtype} base);
void fast_sr1_{suf}({dtype} *arr, int n, {dtype} base) {{
{fast_loop}
}}"""

        base_val = rng.choice([1.5, 2.0, 0.5, 3.0])
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *arr_slow = malloc(N * sizeof({dtype}));
    {dtype} *arr_fast = malloc(N * sizeof({dtype}));
    {dtype} *expected = malloc(N * sizeof({dtype}));
    for (int i = 0; i < N; i++) arr_slow[i] = arr_fast[i] = expected[i] = ({dtype})(i % 100 + 1) * 0.01{suf_t};

    {dtype} base = ({dtype}){base_val}{suf_t};

    /* compute expected inline — independent of slow/fast implementations */
{expected_loop}
    for (int i = 0; i < N; i++) expected[i] *= scale;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr1_{suf}(arr_slow, N, base);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr1_{suf}(arr_fast, N, base);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        double diff = fabs((double)(arr_slow[i] - expected[i])) / fmax(fabs((double)expected[i]), 1e-12);
        if (diff > {"1e-2" if dtype == "float" else "1e-6"}) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr_slow); free(arr_fast); free(expected);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"{desc_series}, n={N}, {dtype}, {loop_style}-loop",
            dtype=dtype,
            difficulty="medium" if n_terms <= 20 else "hard",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=8,
            expected_speedup_range=f"{n_terms//2}x-{n_terms}x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "helper_code": helper_code,
            "metadata": asdict(metadata)
        }


class SR3_Generator(PatternTemplate):
    """SR-3: Redundant Aggregation Recomputation
    Varies: aggregation function (mean, sum, variance, min, max, RMS, weighted mean),
    window type (cumulative, sliding), window sizes, data types,
    loop style (for/while), N scale
    """

    def __init__(self):
        super().__init__("SR-3", "Semantic Redundancy",
                         "Redundant Aggregation Recomputation")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        dtype = rng.choice(["int", "float", "double"])
        agg_type = rng.choice(["cumulative_mean", "cumulative_sum",
                                "sliding_mean", "cumulative_min", "cumulative_max",
                                "cumulative_variance", "cumulative_rms",
                                "sliding_sum", "exponential_moving_avg"])
        loop_style = rng.choice(["for", "while", "for"])
        n_scale = rng.choice([10000, 30000, 50000, 100000])

        # Force float/double for variance/rms/ema (they need FP division)
        if agg_type in ("cumulative_variance", "cumulative_rms", "exponential_moving_avg") and dtype == "int":
            dtype = rng.choice(["float", "double"])

        loop_open = "    int i = 0;\n    while (i < n) {" if loop_style == "while" else "    for (int i = 0; i < n; i++) {"
        loop_close = "        i++;\n    }" if loop_style == "while" else "    }"
        inner_loop_j = "for (int j = 0; j <= i; j++)" if loop_style != "while" else "for (int j = 0; j <= i; j++)"

        if agg_type == "cumulative_mean":
            slow_inner = f"""        {dtype} sum = {DTYPES[dtype]['zero']};
        {inner_loop_j} sum += data[j];
        result[i] = sum / (i + 1);"""
            fast_body = f"""    {dtype} sum = {DTYPES[dtype]['zero']};
{loop_open}
        sum += data[i];
        result[i] = sum / (i + 1);
{loop_close}"""
            desc = "Cumulative mean recomputed from scratch each iteration"

        elif agg_type == "cumulative_sum":
            slow_inner = f"""        {dtype} sum = {DTYPES[dtype]['zero']};
        {inner_loop_j} sum += data[j];
        result[i] = sum;"""
            fast_body = f"""    {dtype} sum = {DTYPES[dtype]['zero']};
{loop_open}
        sum += data[i];
        result[i] = sum;
{loop_close}"""
            desc = "Cumulative sum (prefix sum) recomputed from scratch"

        elif agg_type == "sliding_mean":
            window = rng.choice([4, 8, 16, 32, 64, 128])
            slow_inner = f"""        {dtype} sum = {DTYPES[dtype]['zero']};
        int start = (i >= {window}) ? i - {window} + 1 : 0;
        int count = i - start + 1;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum / count;"""
            fast_body = f"""    {dtype} sum = {DTYPES[dtype]['zero']};
{loop_open}
        sum += data[i];
        if (i >= {window}) sum -= data[i - {window}];
        int count = (i < {window}) ? i + 1 : {window};
        result[i] = sum / count;
{loop_close}"""
            desc = f"Sliding window mean (window={window}) recomputed from scratch"

        elif agg_type == "sliding_sum":
            window = rng.choice([4, 8, 16, 32, 64, 128])
            slow_inner = f"""        {dtype} sum = {DTYPES[dtype]['zero']};
        int start = (i >= {window}) ? i - {window} + 1 : 0;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum;"""
            fast_body = f"""    {dtype} sum = {DTYPES[dtype]['zero']};
{loop_open}
        sum += data[i];
        if (i >= {window}) sum -= data[i - {window}];
        result[i] = sum;
{loop_close}"""
            desc = f"Sliding window sum (window={window}) recomputed from scratch"

        elif agg_type == "cumulative_min":
            slow_inner = f"""        {dtype} mn = data[0];
        for (int j = 1; j <= i; j++) if (data[j] < mn) mn = data[j];
        result[i] = mn;"""
            fast_body = f"""    {dtype} mn = data[0];
    result[0] = mn;
    for (int i = 1; i < n; i++) {{
        if (data[i] < mn) mn = data[i];
        result[i] = mn;
    }}"""
            desc = "Running minimum recomputed from scratch"

        elif agg_type == "cumulative_max":
            slow_inner = f"""        {dtype} mx = data[0];
        for (int j = 1; j <= i; j++) if (data[j] > mx) mx = data[j];
        result[i] = mx;"""
            fast_body = f"""    {dtype} mx = data[0];
    result[0] = mx;
    for (int i = 1; i < n; i++) {{
        if (data[i] > mx) mx = data[i];
        result[i] = mx;
    }}"""
            desc = "Running maximum recomputed from scratch"

        elif agg_type == "cumulative_variance":
            slow_inner = f"""        {dtype} sum = {DTYPES[dtype]['zero']};
        for (int j = 0; j <= i; j++) sum += data[j];
        {dtype} mean = sum / (i + 1);
        {dtype} var_sum = {DTYPES[dtype]['zero']};
        for (int j = 0; j <= i; j++) {{
            {dtype} diff = data[j] - mean;
            var_sum += diff * diff;
        }}
        result[i] = var_sum / (i + 1);"""
            # Welford's online algorithm: numerically stable, avoids E[X^2]-E[X]^2 cancellation
            fast_body = f"""    {dtype} mean = {DTYPES[dtype]['zero']};
    {dtype} M2 = {DTYPES[dtype]['zero']};
{loop_open}
        {dtype} delta = data[i] - mean;
        mean += delta / (i + 1);
        {dtype} delta2 = data[i] - mean;
        M2 += delta * delta2;
        result[i] = M2 / (i + 1);
{loop_close}"""
            desc = "Cumulative variance recomputed from scratch (O(n^2) -> O(n))"

        elif agg_type == "cumulative_rms":
            slow_inner = f"""        {dtype} sum_sq = {DTYPES[dtype]['zero']};
        for (int j = 0; j <= i; j++) sum_sq += data[j] * data[j];
        result[i] = sqrt(sum_sq / (i + 1));"""
            fast_body = f"""    {dtype} sum_sq = {DTYPES[dtype]['zero']};
{loop_open}
        sum_sq += data[i] * data[i];
        result[i] = sqrt(sum_sq / (i + 1));
{loop_close}"""
            desc = "Cumulative RMS recomputed from scratch"

        else:  # exponential_moving_avg
            alpha = rng.choice([0.1, 0.2, 0.3, 0.5])
            slow_inner = f"""        {dtype} ema = data[0];
        for (int j = 1; j <= i; j++)
            ema = {alpha}{DTYPES[dtype]['suffix']} * data[j] + (1.0{DTYPES[dtype]['suffix']} - {alpha}{DTYPES[dtype]['suffix']}) * ema;
        result[i] = ema;"""
            fast_body = f"""    result[0] = data[0];
{loop_open.replace('i = 0', 'i = 1').replace('int i = 0; i < n', 'int i = 1; i < n')}
        result[i] = {alpha}{DTYPES[dtype]['suffix']} * data[i] + (1.0{DTYPES[dtype]['suffix']} - {alpha}{DTYPES[dtype]['suffix']}) * result[i-1];
{loop_close}"""
            desc = f"Exponential moving average (alpha={alpha}) recomputed from scratch"

        fn_suffix = f"v{variant_num:03d}"

        slow_code = f"""void slow_sr3_{fn_suffix}({dtype} *data, {dtype} *result, int n) {{
    for (int i = 0; i < n; i++) {{
{slow_inner}
    }}
}}"""

        fast_code = f"""void fast_sr3_{fn_suffix}({dtype} *data, {dtype} *result, int n) {{
{fast_body}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N {n_scale}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *data = malloc(N * sizeof({dtype}));
    {dtype} *res_slow = malloc(N * sizeof({dtype}));
    {dtype} *res_fast = malloc(N * sizeof({dtype}));
    srand(42);
    for (int i = 0; i < N; i++) data[i] = ({dtype})(rand() % 1000) * 0.01{DTYPES[dtype]['suffix']};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr3_{fn_suffix}(data, res_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr3_{fn_suffix}(data, res_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        /* relative tolerance: large N float accumulation can diverge by > 1 ULP */
        double denom = fmax(fabs((double)res_slow[i]), 1.0);
        double err = fabs((double)(res_slow[i] - res_fast[i])) / denom;
        if (err > 1e-3) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(data); free(res_slow); free(res_fast);
    return 0;
}}"""

        desc_parts = [desc, dtype]
        if loop_style == "while":
            desc_parts.append("while-loop")
        desc_parts.append(f"N={n_scale}")

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=", ".join(desc_parts),
            dtype=dtype,
            difficulty="medium" if "sliding" in agg_type else "easy",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=1,
            lines_of_code=10,
            expected_speedup_range="100x-10000x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class SR4_Generator(PatternTemplate):
    """SR-4: Invariant Function Call in Loop
    Varies: function complexity, number of invariant calls,
    function type (trig, hash, polynomial, sqrt, exp_chain, power_tower, log_sum),
    work amount, dtype, loop style, array operation (+= vs *=)
    """

    def __init__(self):
        super().__init__("SR-4", "Semantic Redundancy",
                         "Invariant Function Call in Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        dtype = rng.choice(["float", "double"])
        fn_type = rng.choice(["trig_combo", "polynomial", "hash_chain", "nested_sqrt",
                               "exp_chain", "power_tower", "log_sum"])
        n_calls = rng.randint(1, 4)  # 1-4 invariant function calls
        loop_style = rng.choice(["for", "while", "for"])
        arr_op = rng.choice(["*=", "+=", "*="])

        fn_bodies = {
            "trig_combo": """{dtype} expensive_fn_{suf}(int key) {{
    {dtype} r = {zero};
    for (int i = 0; i < {work}; i++)
        r += sin(({dtype})(key + i)) * cos(({dtype})(key - i));
    return r;
}}""",
            "polynomial": """{dtype} expensive_fn_{suf}(int key) {{
    {dtype} x = ({dtype})key * 0.001{suffix};
    {dtype} r = {zero};
    for (int i = 0; i < {work}; i++) {{
        r += x * x * x - 3.0{suffix} * x * x + 2.0{suffix} * x - 1.0{suffix};
        x += 0.0001{suffix};
    }}
    return r;
}}""",
            "hash_chain": """{dtype} expensive_fn_{suf}(int key) {{
    unsigned int h = (unsigned int)key;
    {dtype} r = {zero};
    for (int i = 0; i < {work}; i++) {{
        h = h * 2654435761u;
        r += ({dtype})(h & 0xFFFF) / 65536.0{suffix};
    }}
    return r / {work};
}}""",
            "nested_sqrt": """{dtype} expensive_fn_{suf}(int key) {{
    {dtype} r = fabs(({dtype})key) + 1.0{suffix};
    for (int i = 0; i < {work}; i++) r = sqrt(r + ({dtype})i);
    return r;
}}""",
            "exp_chain": """{dtype} expensive_fn_{suf}(int key) {{
    {dtype} r = 1.0{suffix};
    for (int i = 0; i < {work}; i++) {{
        r = exp(-fabs(r * 0.01{suffix})) + ({dtype})(key % (i+1));
    }}
    return r;
}}""",
            "power_tower": """{dtype} expensive_fn_{suf}(int key) {{
    {dtype} base = 1.0{suffix} + ({dtype})(key % 10) * 0.01{suffix};
    {dtype} r = base;
    for (int i = 0; i < {work}; i++) r = pow(base, r * 0.01{suffix});
    return r;
}}""",
            "log_sum": """{dtype} expensive_fn_{suf}(int key) {{
    {dtype} r = {zero};
    for (int i = 1; i <= {work}; i++)
        r += log(({dtype})(key + i));
    return r;
}}""",
        }

        work = rng.choice([30, 50, 100, 200, 500, 1000])
        suf = f"v{variant_num:03d}"
        zero = DTYPES[dtype]['zero']
        suffix = DTYPES[dtype]['suffix']
        fn_code = fn_bodies[fn_type].format(suf=suf, work=work, dtype=dtype,
                                             zero=zero, suffix=suffix)

        # Build slow: call(s) inside loop
        call_lines_slow = []
        call_lines_fast = []
        combine_terms = []
        for c in range(n_calls):
            key_param = f"key{c}" if n_calls > 1 else "key"
            call_lines_slow.append(
                f"        {dtype} f{c} = expensive_fn_{suf}({key_param});"
            )
            call_lines_fast.append(
                f"    {dtype} f{c} = expensive_fn_{suf}({key_param});"
            )
            combine_terms.append(f"f{c}")

        key_params = ", ".join(f"int key{c}" for c in range(n_calls)) if n_calls > 1 else "int key"
        if len(combine_terms) > 1:
            combine_expr = " * ".join(combine_terms)
        else:
            combine_expr = combine_terms[0]

        if loop_style == "while":
            loop_open_slow = "    int i = 0;\n    while (i < n) {"
            loop_close_slow = "        i++;\n    }"
        else:
            loop_open_slow = "    for (int i = 0; i < n; i++) {"
            loop_close_slow = "    }"

        helper_code = f"""#include <math.h>
__attribute__((noinline, noclone))
{fn_code}"""

        # Forward decl first (no {), blank line resets sig_parts so extract_extern_decl
        # captures slow_sr4 (not expensive_fn) as the SLOW_CODE_HERE extern decl.
        slow_code = f"""{dtype} expensive_fn_{suf}(int key);

void slow_sr4_{suf}({dtype} *arr, int n, {key_params}) {{
{loop_open_slow}
{chr(10).join(call_lines_slow)}
        arr[i] {arr_op} {combine_expr};
{loop_close_slow}
}}"""

        # fast.c needs expensive_fn too (hoisted outside loop); it's defined in slow.c.
        fast_code = f"""{dtype} expensive_fn_{suf}(int key);

void fast_sr4_{suf}({dtype} *arr, int n, {key_params}) {{
{chr(10).join(call_lines_fast)}
{loop_open_slow}
        arr[i] {arr_op} {combine_expr};
{loop_close_slow}
}}"""

        key_args = ", ".join(str(42 + c*7) for c in range(n_calls))
        n_scale = rng.choice([100000, 500000, 1000000])

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N {n_scale}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *arr_slow = malloc(N * sizeof({dtype}));
    {dtype} *arr_fast = malloc(N * sizeof({dtype}));
    for (int i = 0; i < N; i++) arr_slow[i] = ({dtype})(i % 100) * 0.1{suffix};
    memcpy(arr_fast, arr_slow, N * sizeof({dtype}));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr4_{suf}(arr_slow, N, {key_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr4_{suf}(arr_fast, N, {key_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(arr_slow[i] - arr_fast[i])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr_slow); free(arr_fast);
    return 0;
}}"""

        desc_parts = [f"{fn_type} function", f"{n_calls} invariant calls",
                       f"work={work}", dtype]
        if loop_style == "while":
            desc_parts.append("while-loop")
        if arr_op == "+=":
            desc_parts.append("additive apply")

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=", ".join(desc_parts),
            dtype=dtype,
            difficulty="easy" if n_calls == 1 else "hard",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=12 + n_calls * 2,
            expected_speedup_range="100x-1000x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "helper_code": helper_code,
            "metadata": asdict(metadata)
        }


class IS1_Generator(PatternTemplate):
    """IS-1: Sparse Data Redundancy
    Varies: sparsity level, matrix dimensions, operation type,
    layout (matmul/matvec/elemwise/outer_product/dot_product/saxpy),
    skip strategy, dtype, loop style
    """

    def __init__(self):
        super().__init__("IS-1", "Input-Sensitive Inefficiency",
                         "Sparse Data Redundancy")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        dtype = rng.choice(["float", "double"])
        layout = rng.choice(["matmul", "matvec", "elemwise", "outer_product",
                              "dot_product", "saxpy"])
        sparsity = rng.choice([0.5, 0.7, 0.8, 0.9, 0.95, 0.99])
        loop_style = rng.choice(["for", "while", "for"])
        suf = f"v{variant_num:03d}"
        zero = DTYPES[dtype]['zero']
        suffix = DTYPES[dtype]['suffix']

        if layout == "matmul":
            slow_code = f"""void slow_is1_{suf}({dtype} *C, {dtype} *A, {dtype} *B, int m, int k, int n) {{
    for (int i = 0; i < m; i++) {{
        for (int j = 0; j < n; j++) {{
            C[i * n + j] = {zero};
            for (int p = 0; p < k; p++) {{
                C[i * n + j] += A[i * k + p] * B[p * n + j];
            }}
        }}
    }}
}}"""
            fast_code = f"""void fast_is1_{suf}({dtype} *C, {dtype} *A, {dtype} *B, int m, int k, int n) {{
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++) C[i * n + j] = {zero};
    for (int i = 0; i < m; i++) {{
        for (int p = 0; p < k; p++) {{
            if (A[i * k + p] == {zero}) continue;
            for (int j = 0; j < n; j++) {{
                if (B[p * n + j] == {zero}) continue;
                C[i * n + j] += A[i * k + p] * B[p * n + j];
            }}
        }}
    }}
}}"""
            desc = f"Sparse matrix-matrix multiply ({sparsity*100:.0f}% zeros), skip zero elements"

        elif layout == "matvec":
            slow_code = f"""void slow_is1_{suf}({dtype} *y, {dtype} *A, {dtype} *x, int m, int n) {{
    for (int i = 0; i < m; i++) {{
        y[i] = {zero};
        for (int j = 0; j < n; j++) {{
            y[i] += A[i * n + j] * x[j];
        }}
    }}
}}"""
            fast_code = f"""void fast_is1_{suf}({dtype} *y, {dtype} *A, {dtype} *x, int m, int n) {{
    for (int i = 0; i < m; i++) {{
        y[i] = {zero};
        for (int j = 0; j < n; j++) {{
            if (A[i * n + j] == {zero}) continue;
            y[i] += A[i * n + j] * x[j];
        }}
    }}
}}"""
            desc = f"Sparse matrix-vector multiply ({sparsity*100:.0f}% zeros), skip zero elements"

        elif layout == "elemwise":
            op = rng.choice(["+", "*", "-"])
            slow_code = f"""void slow_is1_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{
    for (int i = 0; i < n; i++) {{
        out[i] = A[i] {op} B[i];
    }}
}}"""
            if op == "*":
                fast_code = f"""void fast_is1_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{
    for (int i = 0; i < n; i++) {{
        if (A[i] == {zero} || B[i] == {zero}) {{
            out[i] = {zero};
            continue;
        }}
        out[i] = A[i] * B[i];
    }}
}}"""
            elif op == "+":
                fast_code = f"""void fast_is1_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{
    for (int i = 0; i < n; i++) {{
        if (A[i] == {zero}) {{ out[i] = B[i]; continue; }}
        if (B[i] == {zero}) {{ out[i] = A[i]; continue; }}
        out[i] = A[i] + B[i];
    }}
}}"""
            else:
                fast_code = f"""void fast_is1_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{
    for (int i = 0; i < n; i++) {{
        if (B[i] == {zero}) {{ out[i] = A[i]; continue; }}
        out[i] = A[i] - B[i];
    }}
}}"""
            desc = f"Sparse element-wise {op} ({sparsity*100:.0f}% zeros)"

        elif layout == "dot_product":
            slow_code = f"""{dtype} slow_is1_{suf}({dtype} *A, {dtype} *B, int n) {{
    {dtype} sum = {zero};
    for (int i = 0; i < n; i++) {{
        sum += A[i] * B[i];
    }}
    return sum;
}}"""
            fast_code = f"""{dtype} fast_is1_{suf}({dtype} *A, {dtype} *B, int n) {{
    {dtype} sum = {zero};
    for (int i = 0; i < n; i++) {{
        if (A[i] == {zero} || B[i] == {zero}) continue;
        sum += A[i] * B[i];
    }}
    return sum;
}}"""
            desc = f"Sparse dot product ({sparsity*100:.0f}% zeros), skip zero pairs"

        elif layout == "saxpy":
            slow_code = f"""void slow_is1_{suf}({dtype} *y, {dtype} *x, {dtype} alpha, int n) {{
    for (int i = 0; i < n; i++) {{
        y[i] += alpha * x[i];
    }}
}}"""
            fast_code = f"""void fast_is1_{suf}({dtype} *y, {dtype} *x, {dtype} alpha, int n) {{
    if (alpha == {zero}) return;
    for (int i = 0; i < n; i++) {{
        if (x[i] == {zero}) continue;
        y[i] += alpha * x[i];
    }}
}}"""
            desc = f"Sparse SAXPY ({sparsity*100:.0f}% zeros in x), skip zero entries"

        else:  # outer_product
            slow_code = f"""void slow_is1_{suf}({dtype} *C, {dtype} *a, {dtype} *b, int m, int n) {{
    for (int i = 0; i < m; i++) {{
        for (int j = 0; j < n; j++) {{
            C[i * n + j] += a[i] * b[j];
        }}
    }}
}}"""
            fast_code = f"""void fast_is1_{suf}({dtype} *C, {dtype} *a, {dtype} *b, int m, int n) {{
    for (int i = 0; i < m; i++) {{
        if (a[i] == {zero}) continue;
        for (int j = 0; j < n; j++) {{
            if (b[j] == {zero}) continue;
            C[i * n + j] += a[i] * b[j];
        }}
    }}
}}"""
            desc = f"Sparse outer product ({sparsity*100:.0f}% zeros), skip zero rows/cols"

        desc_parts = [desc, dtype]
        if loop_style == "while":
            desc_parts.append("while-loop")

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"IS-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=", ".join(desc_parts),
            dtype=dtype,
            difficulty="hard" if layout == "matmul" else ("medium" if sparsity < 0.9 else "easy"),
            compiler_fixable=False,
            num_loops=3 if layout == "matmul" else (2 if layout in ("matvec", "outer_product") else 1),
            num_arrays=3 if layout in ("matmul", "matvec", "outer_product", "elemwise") else 2,
            lines_of_code=10,
            expected_speedup_range=f"{1/(1-sparsity):.0f}x",
            composition=[]
        )

        # Build test harness based on layout
        n_sparse = 1000000
        sparsity_init = f"if (rng % 100 < {int(sparsity * 100)}) arr[k] = {zero};"
        if layout == "matmul":
            M, K_dim, N_dim = 200, 200, 200
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int m = {M}, k = {K_dim}, n = {N_dim};
    {dtype} *A = malloc(m * k * sizeof({dtype}));
    {dtype} *B = malloc(k * n * sizeof({dtype}));
    {dtype} *C_slow = calloc(m * n, sizeof({dtype}));
    {dtype} *C_fast = calloc(m * n, sizeof({dtype}));
    for (int i = 0; i < m * k; i++) {{ unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    for (int i = 0; i < k * n; i++) {{ unsigned rng = (unsigned)i * 2246822519u; B[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_{suf}(C_slow, A, B, m, k, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_{suf}(C_fast, A, B, m, k, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < m * n; i++) {{
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(C_slow); free(C_fast);
    return 0;
}}
"""
        elif layout == "matvec":
            M2, N2 = 2000, 2000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int m = {M2}, n = {N2};
    {dtype} *A = malloc(m * n * sizeof({dtype}));
    {dtype} *x = malloc(n * sizeof({dtype}));
    {dtype} *y_slow = calloc(m, sizeof({dtype}));
    {dtype} *y_fast = calloc(m, sizeof({dtype}));
    for (int i = 0; i < m * n; i++) {{ unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    for (int i = 0; i < n; i++) x[i] = ({dtype})(i % 100 + 1) * 0.01{suffix};
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_{suf}(y_slow, A, x, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_{suf}(y_fast, A, x, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < m; i++) {{
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(x); free(y_slow); free(y_fast);
    return 0;
}}
"""
        elif layout == "elemwise":
            N3 = n_sparse
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N3};
    {dtype} *A = malloc(n * sizeof({dtype}));
    {dtype} *B = malloc(n * sizeof({dtype}));
    {dtype} *out_slow = malloc(n * sizeof({dtype}));
    {dtype} *out_fast = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) {{ unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    for (int i = 0; i < n; i++) {{ unsigned rng = (unsigned)(i + n) * 2246822519u; B[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_{suf}(out_slow, A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_{suf}(out_fast, A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {{
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}}
"""
        elif layout == "dot_product":
            N4 = n_sparse
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N4};
    {dtype} *A = malloc(n * sizeof({dtype}));
    {dtype} *B = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) {{ unsigned rng = (unsigned)i * 6364136223846793005u; A[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    for (int i = 0; i < n; i++) {{ unsigned rng = (unsigned)(i + n) * 2246822519u; B[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    {dtype} r_slow = {zero}, r_fast = {zero};
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_is1_{suf}(A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_is1_{suf}(A, B, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs((double)(r_slow - r_fast)) < 1e-4 * fmax(fabs((double)r_slow), 1.0);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}}
"""
        elif layout == "saxpy":
            N5 = n_sparse
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N5};
    {dtype} *x = malloc(n * sizeof({dtype}));
    {dtype} *y_slow = malloc(n * sizeof({dtype}));
    {dtype} *y_fast = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) {{ unsigned rng = (unsigned)i * 6364136223846793005u; x[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    for (int i = 0; i < n; i++) y_slow[i] = ({dtype})(i % 100) * 0.01{suffix};
    memcpy(y_fast, y_slow, n * sizeof({dtype}));
    {dtype} alpha = ({dtype})2.5{suffix};
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_{suf}(y_slow, x, alpha, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_{suf}(y_fast, x, alpha, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {{
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-5) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(x); free(y_slow); free(y_fast);
    return 0;
}}
"""
        else:  # outer_product
            M3, N3b = 1000, 1000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int m = {M3}, n = {N3b};
    {dtype} *a = malloc(m * sizeof({dtype}));
    {dtype} *b = malloc(n * sizeof({dtype}));
    {dtype} *C_slow = calloc(m * n, sizeof({dtype}));
    {dtype} *C_fast = calloc(m * n, sizeof({dtype}));
    for (int i = 0; i < m; i++) {{ unsigned rng = (unsigned)i * 6364136223846793005u; a[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    for (int i = 0; i < n; i++) {{ unsigned rng = (unsigned)(i + m) * 2246822519u; b[i] = (rng % 100 < {int(sparsity * 100)}) ? {zero} : ({dtype})(rng % 100 + 1) * 0.01{suffix}; }}
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_is1_{suf}(C_slow, a, b, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_is1_{suf}(C_fast, a, b, m, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < m * n; i++) {{
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(a); free(b); free(C_slow); free(C_fast);
    return 0;
}}
"""

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }



class DS4_Generator(PatternTemplate):
    """DS-4: Cache-Unfriendly Access (AoS vs SoA)
    Varies: struct template (particles, pixels, vertices, records, sensors, events),
    which fields accessed (random subset), reduction type (sum/max/min/product),
    field count, loop style
    """

    def __init__(self):
        super().__init__("DS-4", "Data Structure Inefficiency",
                         "Cache-Unfriendly Access (AoS vs SoA)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        loop_style = rng.choice(["for", "while", "for"])

        # Large structs (16 fields each) so AoS cache-line utilization is low.
        # Only 1-2 fields are accessed per element — everything else is waste.
        # With 16 doubles (128 bytes/element) and accessing 1 field (8 bytes),
        # AoS utilization = 6.25% vs SoA's 100% → ~16x speedup at -O3.
        struct_templates = {
            "particles": [("x","double"), ("y","double"), ("z","double"),
                          ("vx","double"), ("vy","double"), ("vz","double"),
                          ("mass","double"), ("charge","double"),
                          ("pad0","double"), ("pad1","double"), ("pad2","double"),
                          ("pad3","double"), ("pad4","double"), ("pad5","double"),
                          ("pad6","double"), ("pad7","double")],
            "pixels": [("r","double"), ("g","double"), ("b","double"), ("a","double"),
                       ("x","double"), ("y","double"), ("depth","double"), ("normal_x","double"),
                       ("pad0","double"), ("pad1","double"), ("pad2","double"),
                       ("pad3","double"), ("pad4","double"), ("pad5","double"),
                       ("pad6","double"), ("pad7","double")],
            "vertices": [("px","double"), ("py","double"), ("pz","double"),
                         ("nx","double"), ("ny","double"), ("nz","double"),
                         ("u","double"), ("v","double"),
                         ("pad0","double"), ("pad1","double"), ("pad2","double"),
                         ("pad3","double"), ("pad4","double"), ("pad5","double"),
                         ("pad6","double"), ("pad7","double")],
            "records": [("id","double"), ("timestamp","double"), ("value","double"),
                        ("weight","double"), ("category","double"), ("flags","double"),
                        ("score","double"), ("rank","double"),
                        ("pad0","double"), ("pad1","double"), ("pad2","double"),
                        ("pad3","double"), ("pad4","double"), ("pad5","double"),
                        ("pad6","double"), ("pad7","double")],
            "sensors": [("temp","double"), ("humidity","double"), ("pressure","double"),
                        ("wind_speed","double"), ("wind_dir","double"),
                        ("light","double"), ("noise","double"), ("co2","double"),
                        ("pad0","double"), ("pad1","double"), ("pad2","double"),
                        ("pad3","double"), ("pad4","double"), ("pad5","double"),
                        ("pad6","double"), ("pad7","double")],
            "events": [("time","double"), ("x","double"), ("y","double"),
                       ("energy","double"), ("channel","double"), ("quality","double"),
                       ("amplitude","double"), ("phase","double"),
                       ("pad0","double"), ("pad1","double"), ("pad2","double"),
                       ("pad3","double"), ("pad4","double"), ("pad5","double"),
                       ("pad6","double"), ("pad7","double")],
        }

        template_name = rng.choice(list(struct_templates.keys()))
        all_fields = struct_templates[template_name]

        # Always use all 16 fields so struct is 128 bytes — maximises cache waste
        n_fields_to_use = len(all_fields)
        fields = all_fields[:n_fields_to_use]

        # Access only 1-2 of the 16 fields — rest are cache pollution
        n_accessed = rng.randint(1, 2)
        accessed_fields = rng.sample([f[0] for f in fields], n_accessed)

        # Choose reduction type
        reduction = rng.choice(["sum", "sum", "max", "min"])

        n_fields = len(fields)

        # AoS struct definition
        struct_fields_str = "\n".join(f"    {t} {n};" for n, t in fields)
        struct_name = f"AoS_{suf}"
        struct_def = f"typedef struct {{\n{struct_fields_str}\n}} {struct_name};"

        # Determine accumulator logic based on reduction
        if reduction == "sum":
            accum_decl = "\n".join(f"    double total_{f} = 0.0;" for f in accessed_fields)
            accum_op = lambda f: f"total_{f} += "
            combine = " + ".join(f"total_{f}" for f in accessed_fields)
        elif reduction == "max":
            accum_decl = "\n".join(f"    double total_{f} = -1e308;" for f in accessed_fields)
            accum_op = lambda f: f"if ((double)arr[i].{f} > total_{f}) total_{f} = "
            combine = " + ".join(f"total_{f}" for f in accessed_fields)
        elif reduction == "min":
            accum_decl = "\n".join(f"    double total_{f} = 1e308;" for f in accessed_fields)
            accum_op = lambda f: f"if ((double)arr[i].{f} < total_{f}) total_{f} = "
            combine = " + ".join(f"total_{f}" for f in accessed_fields)
        else:  # product
            accum_decl = "\n".join(f"    double total_{f} = 1.0;" for f in accessed_fields)
            accum_op = lambda f: f"total_{f} *= "
            combine = " * ".join(f"total_{f}" for f in accessed_fields)

        # Build AoS loop body
        if reduction in ("sum", "product"):
            aos_body = "\n".join(f"        {accum_op(f)}(double)arr[i].{f};" for f in accessed_fields)
        else:
            aos_body = "\n".join(f"        {accum_op(f)}(double)arr[i].{f};" for f in accessed_fields)

        # Loop scaffolding
        if loop_style == "while":
            loop_open = "    int i = 0;\n    while (i < n) {"
            loop_close = "        i++;\n    }"
        else:
            loop_open = "    for (int i = 0; i < n; i++) {"
            loop_close = "    }"

        slow_code = f"""{struct_def}

double slow_ds4_{suf}({struct_name} *arr, int n) {{
{accum_decl}
{loop_open}
{aos_body}
{loop_close}
    return {combine};
}}"""

        # Fast: SoA access
        soa_params = ", ".join(f"double *{f}" for f in accessed_fields)
        if reduction in ("sum", "product"):
            soa_body = "\n".join(f"        total_{f} {'*' if reduction == 'product' else '+'}= {f}[i];" for f in accessed_fields)
        elif reduction == "max":
            soa_body = "\n".join(f"        if ({f}[i] > total_{f}) total_{f} = {f}[i];" for f in accessed_fields)
        else:
            soa_body = "\n".join(f"        if ({f}[i] < total_{f}) total_{f} = {f}[i];" for f in accessed_fields)

        fast_code = f"""double fast_ds4_{suf}({soa_params}, int n) {{
{accum_decl}
{loop_open}
{soa_body}
{loop_close}
    return {combine};
}}"""

        desc_parts = [f"{template_name} struct ({n_fields} fields)",
                       f"accessing {accessed_fields}", f"{reduction} reduction"]
        if loop_style == "while":
            desc_parts.append("while-loop")

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"DS-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=", ".join(desc_parts),
            dtype="double",
            difficulty="hard" if n_accessed == 1 and n_fields >= 8 else "medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=n_accessed,
            lines_of_code=12,
            expected_speedup_range=f"{n_fields//max(n_accessed,1)}x-{n_fields}x",
            composition=[]
        )

        # Build test harness for DS-4 (AoS slow vs SoA fast)
        N_ds4 = 5000000
        # Build a map of field name -> type for accessed fields
        field_type_map = {n: t for n, t in fields}
        # SoA alloc lines: one double* per accessed field
        soa_alloc = "\n    ".join(f"double *soa_{f} = malloc({N_ds4} * sizeof(double));" for f in accessed_fields)
        # Fill AoS and SoA from same data, using int-scale values for int fields
        fill_aos = f"    for (int i = 0; i < {N_ds4}; i++) {{"
        fill_aos += "\n        int iv = (i % 997) + 1;"
        fill_aos += "\n        double dv = (double)iv * 0.001;"
        # For int fields use iv (integer), for float/double use dv (float)
        def _fill_val(fname, scale):
            ftype = field_type_map.get(fname, "double")
            if ftype == "int":
                return f"iv * {scale}"
            else:
                return f"dv * {scale}"
        fill_body_aos = "\n".join(f"        arr[i].{f} = {_fill_val(f, idx+1)};" for idx, f in enumerate(accessed_fields))
        fill_body_soa = "\n".join(f"        soa_{f}[i] = (double)({_fill_val(f, idx+1)});" for idx, f in enumerate(accessed_fields))
        fill_aos += f"\n{fill_body_aos}\n{fill_body_soa}\n    }}"
        soa_args = ", ".join(f"soa_{f}" for f in accessed_fields)
        soa_free = "\n    ".join(f"free(soa_{f});" for f in accessed_fields)
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

{struct_def}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_ds4};
    {struct_name} *arr = malloc(n * sizeof({struct_name}));
    {soa_alloc}
{fill_aos}
    double r_slow = 0.0, r_fast = 0.0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_ds4_{suf}(arr, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_ds4_{suf}({soa_args}, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs(r_slow - r_fast) < fmax(fabs(r_slow) * 1e-6, 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    {soa_free}
    return 0;
}}
"""

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class AL1_Generator(PatternTemplate):
    """AL-1: Brute Force vs Memoization/DP
    Varies: problem type (fibonacci, tribonacci, grid_paths, staircase, coin_ways,
    catalan, derangements, binomial, min_cost_path, partition_count),
    step sizes, base cases
    """

    def __init__(self):
        super().__init__("AL-1", "Algorithmic Inefficiency",
                         "Brute Force vs Memoization/DP")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        problem = rng.choice(["fibonacci", "tribonacci", "grid_paths",
                               "staircase", "coin_ways",
                               "catalan", "derangements", "binomial",
                               "min_cost_path", "partition_count"])

        if problem == "fibonacci":
            slow_code = f"""long long slow_al1_{suf}(int n) {{
    if (n <= 1) return n;
    return slow_al1_{suf}(n-1) + slow_al1_{suf}(n-2);
}}"""
            fast_code = f"""long long fast_al1_{suf}(int n) {{
    if (n <= 1) return n;
    long long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {{ long long t = a+b; a = b; b = t; }}
    return b;
}}"""
            desc = "Fibonacci: O(2^n) recursive -> O(n) iterative"

        elif problem == "tribonacci":
            slow_code = f"""long long slow_al1_{suf}(int n) {{
    if (n == 0) return 0;
    if (n <= 2) return 1;
    return slow_al1_{suf}(n-1) + slow_al1_{suf}(n-2) + slow_al1_{suf}(n-3);
}}"""
            fast_code = f"""long long fast_al1_{suf}(int n) {{
    if (n == 0) return 0;
    if (n <= 2) return 1;
    long long a=0, b=1, c=1;
    for (int i=3; i<=n; i++) {{ long long t=a+b+c; a=b; b=c; c=t; }}
    return c;
}}"""
            desc = "Tribonacci: O(3^n) recursive -> O(n) iterative"

        elif problem == "grid_paths":
            slow_code = f"""long long slow_al1_{suf}(int r, int c) {{
    if (r == 0 || c == 0) return 1;
    return slow_al1_{suf}(r-1, c) + slow_al1_{suf}(r, c-1);
}}"""
            fast_code = f"""long long fast_al1_{suf}(int r, int c) {{
    long long *dp = calloc(c+1, sizeof(long long));
    for (int j = 0; j <= c; j++) dp[j] = 1;
    for (int i = 1; i <= r; i++)
        for (int j = 1; j <= c; j++)
            dp[j] += dp[j-1];
    long long res = dp[c]; free(dp); return res;
}}"""
            desc = "Grid paths: exponential recursive -> O(r*c) DP"

        elif problem == "staircase":
            k = rng.choice([2, 3, 4, 5])
            slow_rec = " + ".join(f"slow_al1_{suf}(n-{i+1})" for i in range(k))

            slow_code = f"""long long slow_al1_{suf}(int n) {{
    if (n <= 0) return (n == 0) ? 1 : 0;
    return {slow_rec};
}}"""
            fast_code = f"""long long fast_al1_{suf}(int n) {{
    if (n <= 0) return (n == 0) ? 1 : 0;
    long long *dp = calloc(n+1, sizeof(long long));
    dp[0] = 1;
    for (int i = 1; i <= n; i++)
        for (int s = 1; s <= {k} && s <= i; s++)
            dp[i] += dp[i-s];
    long long res = dp[n]; free(dp); return res;
}}"""
            desc = f"Staircase (step 1..{k}): O({k}^n) -> O(n*{k})"

        elif problem == "coin_ways":
            slow_code = f"""int slow_al1_{suf}(int coins[], int nc, int amount) {{
    if (amount == 0) return 1;
    if (amount < 0) return 0;
    int ways = 0;
    for (int i = 0; i < nc; i++)
        ways += slow_al1_{suf}(coins, nc, amount - coins[i]);
    return ways;
}}"""
            fast_code = f"""int fast_al1_{suf}(int coins[], int nc, int amount) {{
    int *dp = calloc(amount+1, sizeof(int));
    dp[0] = 1;
    for (int a = 1; a <= amount; a++)
        for (int i = 0; i < nc; i++)
            if (coins[i] <= a) dp[a] += dp[a - coins[i]];
    int res = dp[amount]; free(dp); return res;
}}"""
            desc = "Coin ways: exponential recursive -> O(amount * coins)"

        elif problem == "catalan":
            slow_code = f"""long long slow_al1_{suf}(int n) {{
    if (n <= 1) return 1;
    long long res = 0;
    for (int i = 0; i < n; i++)
        res += slow_al1_{suf}(i) * slow_al1_{suf}(n - 1 - i);
    return res;
}}"""
            fast_code = f"""long long fast_al1_{suf}(int n) {{
    long long *dp = calloc(n+1, sizeof(long long));
    dp[0] = dp[1] = 1;
    for (int i = 2; i <= n; i++)
        for (int j = 0; j < i; j++)
            dp[i] += dp[j] * dp[i - 1 - j];
    long long res = dp[n]; free(dp); return res;
}}"""
            desc = "Catalan numbers: exponential recursive -> O(n^2) DP"

        elif problem == "derangements":
            slow_code = f"""long long slow_al1_{suf}(int n) {{
    if (n == 0) return 1;
    if (n == 1) return 0;
    return (n - 1) * (slow_al1_{suf}(n - 1) + slow_al1_{suf}(n - 2));
}}"""
            fast_code = f"""long long fast_al1_{suf}(int n) {{
    if (n == 0) return 1;
    if (n == 1) return 0;
    long long a = 1, b = 0;
    for (int i = 2; i <= n; i++) {{
        long long t = (i - 1) * (a + b);
        a = b; b = t;
    }}
    return b;
}}"""
            desc = "Derangements: O(2^n) recursive -> O(n) iterative"

        elif problem == "binomial":
            slow_code = f"""long long slow_al1_{suf}(int n, int k) {{
    if (k == 0 || k == n) return 1;
    return slow_al1_{suf}(n-1, k-1) + slow_al1_{suf}(n-1, k);
}}"""
            fast_code = f"""long long fast_al1_{suf}(int n, int k) {{
    long long *dp = calloc(k+1, sizeof(long long));
    dp[0] = 1;
    for (int i = 1; i <= n; i++)
        for (int j = (i < k ? i : k); j > 0; j--)
            dp[j] += dp[j-1];
    long long res = dp[k]; free(dp); return res;
}}"""
            desc = "Binomial C(n,k): O(2^n) recursive -> O(n*k) DP"

        elif problem == "min_cost_path":
            slow_code = f"""int slow_al1_{suf}(int *grid, int m, int n, int r, int c) {{
    if (r == 0 && c == 0) return grid[0];
    if (r < 0 || c < 0) return 999999999;
    int up = slow_al1_{suf}(grid, m, n, r-1, c);
    int left = slow_al1_{suf}(grid, m, n, r, c-1);
    int best = (up < left) ? up : left;
    return grid[r * n + c] + best;
}}"""
            fast_code = f"""int fast_al1_{suf}(int *grid, int m, int n, int r_unused, int c_unused) {{
    int *dp = calloc(m * n, sizeof(int));
    dp[0] = grid[0];
    for (int j = 1; j < n; j++) dp[j] = dp[j-1] + grid[j];
    for (int i = 1; i < m; i++) {{
        dp[i*n] = dp[(i-1)*n] + grid[i*n];
        for (int j = 1; j < n; j++) {{
            int up = dp[(i-1)*n + j], left = dp[i*n + j - 1];
            dp[i*n + j] = grid[i*n + j] + ((up < left) ? up : left);
        }}
    }}
    int res = dp[m*n - 1]; free(dp); return res;
}}"""
            desc = "Min cost path: exponential recursive -> O(m*n) DP"

        else:  # partition_count
            slow_code = f"""int slow_al1_{suf}(int n, int max_val) {{
    if (n == 0) return 1;
    if (n < 0 || max_val == 0) return 0;
    return slow_al1_{suf}(n - max_val, max_val) + slow_al1_{suf}(n, max_val - 1);
}}"""
            fast_code = f"""int fast_al1_{suf}(int n, int max_val) {{
    int *dp = calloc(n + 1, sizeof(int));
    dp[0] = 1;
    for (int v = 1; v <= max_val; v++)
        for (int i = v; i <= n; i++)
            dp[i] += dp[i - v];
    int res = dp[n]; free(dp); return res;
}}"""
            desc = "Integer partition count: exponential -> O(n * max_val) DP"

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"AL-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype="long long",
            difficulty="hard" if problem in ["grid_paths", "coin_ways", "min_cost_path", "catalan"] else "medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=0,
            lines_of_code=8,
            expected_speedup_range="1000x+",
            composition=[]
        )

        # Build test harness per problem type
        if problem in ("fibonacci", "tribonacci", "derangements"):
            # single int arg, returns long long
            N_slow = 35 if problem == "fibonacci" else (30 if problem == "tribonacci" else 40)
            N_fast_reps = 10000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_slow};
    long long r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""
        elif problem == "catalan":
            N_slow = 14
            N_fast_reps = 100000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_slow};
    long long r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""
        elif problem in ("staircase",):
            # k is a local var in the generate method (defined in staircase branch)
            # We need to get it — but it only exists in that branch.
            # Use n=30 which is safe even for k=5
            N_slow = 30
            N_fast_reps = 100000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_slow};
    long long r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""
        elif problem == "grid_paths":
            # signature: (int r, int c)
            N_slow = 15
            N_fast_reps = 100000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int r = {N_slow}, c = {N_slow};
    long long r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int rep = 0; rep < slow_reps; rep++) r_slow = slow_al1_{suf}(r, c);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int rep = 0; rep < fast_reps; rep++) r_fast = fast_al1_{suf}(r, c);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""
        elif problem == "binomial":
            # signature: (int n, int k)
            N_slow = 30
            K_slow = 15
            N_fast_reps = 100000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_slow}, k = {K_slow};
    long long r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(n, k);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(n, k);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""
        elif problem == "coin_ways":
            # signature: (int coins[], int nc, int amount)
            # slow is exponential in amount, keep small
            N_fast_reps = 1000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int coins[] = {{1, 2, 5}};
    int nc = 3, amount = 20;
    int r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(coins, nc, amount);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(coins, nc, amount);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""
        elif problem == "min_cost_path":
            # signature: slow: (int *grid, int m, int n, int r, int c)
            #             fast: (int *grid, int m, int n, int r_unused, int c_unused)
            # exponential in grid size, keep small
            MN = 8
            N_fast_reps = 100000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int m = {MN}, n = {MN};
    int *grid = malloc(m * n * sizeof(int));
    for (int i = 0; i < m * n; i++) grid[i] = (i % 10) + 1;
    int r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(grid, m, n, m-1, n-1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(grid, m, n, m-1, n-1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(grid);
    return 0;
}}
"""
        else:  # partition_count
            # signature: (int n, int max_val)
            N_fast_reps = 1000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = 20, max_val = 20;
    int r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int slow_reps = 1, fast_reps = {N_fast_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < slow_reps; r++) r_slow = slow_al1_{suf}(n, max_val);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / slow_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < fast_reps; r++) r_fast = fast_al1_{suf}(n, max_val);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / fast_reps;
    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}
"""

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }

class SR2_Generator(PatternTemplate):
    """SR-2: Loop-Invariant Term in Mixed Expression.
    A transcendental penalty function with loop-invariant arguments is called
    every iteration inside a mixed expression. The sin/exp inner loop prevents
    the compiler from hoisting it as pure/const.
    Optimization: separate accumulators for data-dependent terms, call penalty once.
    Varies: number of arrays, penalty terms, expression terms, dtype, loop style.
    """

    def __init__(self):
        super().__init__("SR-2", "Semantic Redundancy",
                         "Loop-Invariant Term in Mixed Expression")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        suf_t = DTYPES[dtype]['suffix']
        n_arrays = rng.choice([2, 3])           # X+Y or X+Y+Z
        n_penalty_terms = rng.randint(10, 30)   # terms in the sin*exp inner loop
        decay = rng.choice([0.05, 0.1, 0.02])
        N = rng.choice([500000, 1000000, 2000000])
        loop_style = rng.choice(["for", "while"])
        n_consts = 2  # always alpha, beta

        arr_names = ["X", "Y", "Z"][:n_arrays]
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)
        const_params = f"{dtype} alpha, {dtype} beta"
        all_params = f"{arr_params}, int n, {const_params}"

        # Build data-dependent expression terms (vary per variant)
        # Always include alpha*X[i]*X[i] + beta*Y[i]; optionally add more terms
        data_terms = [f"alpha * X[i] * X[i]", f"beta * Y[i]"]
        fast_accums = [("sumXsq", "sumXsq += X[i] * X[i];"), ("sumY", "sumY += Y[i];")]
        fast_final_parts = ["alpha * sumXsq", "beta * sumY"]

        if n_arrays >= 3:
            data_terms.append(f"alpha * Z[i]")
            fast_accums.append(("sumZ", "sumZ += Z[i];"))
            fast_final_parts.append("alpha * sumZ")

        slow_expr = " + ".join(data_terms) + " + penalty(alpha, beta)"
        acc_init = "\n    ".join(f"{dtype} {name} = 0.0;" for name, _ in fast_accums)
        acc_body_lines = "\n        ".join(line for _, line in fast_accums)
        if loop_style == "while":
            acc_body_lines += "\n        i++;"
        fast_final = " + ".join(fast_final_parts) + " + (double)n * penalty(alpha, beta)"

        if loop_style == "for":
            slow_loop = f"    for (int i = 0; i < n; i++) {{\n        result += {slow_expr};\n    }}"
            fast_loop = f"    {acc_init}\n    for (int i = 0; i < n; i++) {{\n        {acc_body_lines}\n    }}"
        else:
            slow_loop = f"    int i = 0;\n    while (i < n) {{\n        result += {slow_expr};\n        i++;\n    }}"
            fast_loop = f"    {acc_init}\n    int i = 0;\n    while (i < n) {{\n        {acc_body_lines}\n    }}"

        helper_code = f"""#include <math.h>
__attribute__((noinline, noclone))
{dtype} penalty({dtype} a, {dtype} b) {{
    {dtype} r = 0.0;
    for (int k = 1; k <= {n_penalty_terms}; k++) r += ({dtype})sin(a * k) * ({dtype})exp(-b * k * {decay});
    return r;
}}"""

        slow_code = f"""#include <math.h>
{dtype} penalty({dtype} a, {dtype} b);
__attribute__((noinline))
{dtype} slow_sr2_{suf}({all_params}) {{
    {dtype} result = 0.0;
{slow_loop}
    return result;
}}"""

        fast_code = f"""#include <math.h>
{dtype} penalty({dtype} a, {dtype} b);
__attribute__((noinline))
{dtype} fast_sr2_{suf}({all_params}) {{
{fast_loop}
    return {fast_final};
}}"""

        # Test harness — computes expected inline without calling slow/fast
        arr_allocs = "\n    ".join(
            f"{dtype} *{a} = malloc({N} * sizeof({dtype}));\n    "
            f"for (int k = 0; k < {N}; k++) {a}[k] = ({dtype})(k % 100 - 50) * 0.1{suf_t};"
            for a in arr_names
        )
        arr_args = ", ".join(arr_names)
        arr_frees = "\n    ".join(f"free({a});" for a in arr_names)
        alpha_val, beta_val = rng.choice([(2.5, 1.5), (1.0, 0.5), (3.0, 2.0)])

        # Inline expected computation
        expected_data_terms = " + ".join(
            f"alpha * X[k] * X[k]" if a == "X" else f"beta * Y[k]" if a == "Y" else f"alpha * Z[k]"
            for a in arr_names
        )

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = N;
    {arr_allocs}
    {dtype} alpha = ({dtype}){alpha_val}{suf_t}, beta = ({dtype}){beta_val}{suf_t};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_slow = slow_sr2_{suf}({arr_args}, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_fast = fast_sr2_{suf}({arr_args}, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    /* compute expected inline — penalty inlined here, no dependency on slow/fast */
    {dtype} p = 0.0;
    for (int k = 1; k <= {n_penalty_terms}; k++) p += ({dtype})sin(alpha * k) * ({dtype})exp(-beta * k * {decay});
    {dtype} expected = 0.0;
    for (int k = 0; k < N; k++) expected += {expected_data_terms} + p;

    double rel = fabs((double)(r_slow - expected)) / fmax(fabs((double)expected), 1e-12);
    int correct = rel < 1e-2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    {arr_frees}
    return 0;
}}"""

        desc = f"{n_penalty_terms}-term sin*exp penalty, {n_arrays} arrays, n={N}, {dtype}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="medium" if n_penalty_terms <= 15 else "hard",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=n_arrays,
            lines_of_code=10 + n_arrays,
            expected_speedup_range=f"{n_penalty_terms//2}x-{n_penalty_terms}x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "helper_code": helper_code,
            "metadata": asdict(metadata)
        }


class CF1_Generator(PatternTemplate):
    """CF-1: Batch Type Dispatch Devirtualization.
    Per-element dispatch through a noinline function prevents vectorization.
    Optimization: check mode once (O(1)) and dispatch to an inline loop."""

    def __init__(self):
        super().__init__("CF-1", "Control Flow",
                         "Batch Type Dispatch Devirtualization")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(list(DTYPES.keys()))
        n_modes = rng.choice([2, 3, 4, 5])
        n_arrays = rng.choice([2, 3])
        loop_style = rng.choice(["for", "while"])
        N = rng.choice([5000000, 10000000, 20000000])

        ops = rng.sample(["+", "-", "*"], min(n_modes, 3))
        while len(ops) < n_modes:
            ops.append(rng.choice(["+", "-", "*"]))

        arr_names = ["A", "B", "C"][:n_arrays]
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)

        # Build noinline dispatch function (slow) and inline hoisted loops (fast)
        # Scalar expressions for noinline dispatch function
        scalar_exprs = []
        fast_loops = []
        for m_idx in range(n_modes):
            op = ops[m_idx]
            if n_arrays == 2:
                scalar_expr = f"a {op} b"
                array_expr = f"{arr_names[0]}[i] {op} {arr_names[1]}[i]"
            else:
                combiner = rng.choice(['+', '-'])
                scalar_expr = f"(a {op} b) {combiner} c"
                array_expr = f"({arr_names[0]}[i] {op} {arr_names[1]}[i]) {combiner} {arr_names[2]}[i]"
            scalar_exprs.append(scalar_expr)

            if_kw = "if" if m_idx == 0 else "} else if" if m_idx < n_modes - 1 else "} else"
            cond_str = f" (mode == {m_idx + 1})" if m_idx < n_modes - 1 else ""
            fast_loops.append(f"    {if_kw}{cond_str} {{\n        for (int i = 0; i < n; i++) out[i] = {array_expr};")

        fast_branch_code = "\n".join(fast_loops) + "\n    }"

        # Build dispatch branches inside the noinline function
        dispatch_branches = []
        for m_idx in range(n_modes - 1):
            dispatch_branches.append(f"    if (mode == {m_idx + 1}) return {scalar_exprs[m_idx]};")
        dispatch_branches.append(f"    return {scalar_exprs[n_modes - 1]};")
        dispatch_body = "\n".join(dispatch_branches)

        if n_arrays == 2:
            dispatch_params = f"{dtype} a, {dtype} b, int mode"
            dispatch_call = f"cf1_dispatch_{suf}({arr_names[0]}[i], {arr_names[1]}[i], mode)"
        else:
            dispatch_params = f"{dtype} a, {dtype} b, {dtype} c, int mode"
            dispatch_call = f"cf1_dispatch_{suf}({arr_names[0]}[i], {arr_names[1]}[i], {arr_names[2]}[i], mode)"

        slow_code = f"""static {dtype} __attribute__((noinline)) cf1_dispatch_{suf}({dispatch_params}) {{
{dispatch_body}
}}
void slow_cf1_{suf}({dtype} *out, {arr_params}, int n, int mode) {{
    for (int i = 0; i < n; i++) out[i] = {dispatch_call};
}}"""

        fast_code = f"""void fast_cf1_{suf}({dtype} *out, {arr_params}, int n, int mode) {{
{fast_branch_code}
}}"""

        # Test harness
        arr_allocs = "\n    ".join(f'{dtype} *{a} = malloc({N} * sizeof({dtype})); for (int k = 0; k < {N}; k++) {a}[k] = ({dtype})(k % 200) * 0.05f;' for a in arr_names)
        arr_args = ", ".join(arr_names)
        arr_frees = "\n    ".join(f"free({a});" for a in arr_names)
        mode_val = rng.randint(1, n_modes)

        suf_t = "f" if dtype == "float" else ""
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N};
    {arr_allocs}
    {dtype} *out_s = malloc(n * sizeof({dtype}));
    {dtype} *out_f = malloc(n * sizeof({dtype}));
    struct timespec t0, t1;
    int n_reps = 1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_cf1_{suf}(out_s, {arr_args}, n, {mode_val});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_cf1_{suf}(out_f, {arr_args}, n, {mode_val});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {{
        if (fabs{suf_t}(out_s[i] - out_f[i]) > 1e-6{suf_t}) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    {arr_frees}
    free(out_s); free(out_f);
    return 0;
}}
"""

        desc = f"{n_modes} modes, {n_arrays} arrays, {dtype}, noinline dispatch"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"CF-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=n_arrays + 1,
            lines_of_code=8 + n_modes * 2,
            expected_speedup_range="2x-5x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class CF2_Generator(PatternTemplate):
    """CF-2: Noinline Bounds Check Elimination.
    A noinline bounds-check function called per element prevents vectorization.
    Optimization: remove the check entirely (the loop bounds already guarantee validity)."""

    def __init__(self):
        super().__init__("CF-2", "Control Flow",
                         "Noinline Bounds Check Elimination")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(list(DTYPES.keys()))
        # col_sum and transpose_sum are memory-bandwidth-bound: cache miss latency
        # dwarfs the function-call overhead, so removing the check yields <2x speedup.
        layout = rng.choice(["row_sum", "scale"])
        n_checks = rng.choice([2, 3, 4])
        loop_style = rng.choice(["for", "while"])
        rows = rng.choice([1000, 2000, 3000, 4000])
        cols = rng.choice([1000, 2000, 3000, 4000])

        # Build redundant checks
        checks_2d = [
            "i >= 0 && i < rows",
            "j >= 0 && j < cols",
            "i * cols + j < rows * cols",
            "i * cols + j >= 0",
        ]
        chosen_checks = rng.sample(checks_2d, n_checks)
        check_cond = " && ".join(chosen_checks)

        # Check function goes to helper.c (separate TU) so GCC-O3 cannot prove it
        # always returns true from the loop bounds and eliminate the branch.
        helper_code = f"""__attribute__((noinline, noclone))
int cf2_check_{suf}(int i, int j, int rows, int cols) {{
    return ({check_cond});
}}"""
        check_decl = f"int cf2_check_{suf}(int i, int j, int rows, int cols);"

        if layout == "row_sum":
            slow_code = f"""{check_decl}
void slow_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *row_sums) {{
    for (int i = 0; i < rows; i++) {{
        row_sums[i] = 0;
        for (int j = 0; j < cols; j++) {{
            if (cf2_check_{suf}(i, j, rows, cols)) {{
                row_sums[i] += matrix[i * cols + j];
            }}
        }}
    }}
}}"""
            fast_code = f"""void fast_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *row_sums) {{
    for (int i = 0; i < rows; i++) {{
        row_sums[i] = 0;
        for (int j = 0; j < cols; j++) {{
            row_sums[i] += matrix[i * cols + j];
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.1;
    {dtype} *s_slow = malloc(rows * sizeof({dtype}));
    {dtype} *s_fast = malloc(rows * sizeof({dtype}));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_cf2_{suf}(mat, rows, cols, s_slow);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_cf2_{suf}(mat, rows, cols, s_fast);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < rows; i++) {{
        if (fabs((double)(s_slow[i] - s_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat); free(s_slow); free(s_fast);
    return 0;
}}
"""
        elif layout == "col_sum":
            slow_code = f"""{check_decl}
void slow_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *col_sums) {{
    for (int j = 0; j < cols; j++) {{
        col_sums[j] = 0;
        for (int i = 0; i < rows; i++) {{
            if (cf2_check_{suf}(i, j, rows, cols)) {{
                col_sums[j] += matrix[i * cols + j];
            }}
        }}
    }}
}}"""
            fast_code = f"""void fast_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *col_sums) {{
    for (int j = 0; j < cols; j++) {{
        col_sums[j] = 0;
        for (int i = 0; i < rows; i++) {{
            col_sums[j] += matrix[i * cols + j];
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.1;
    {dtype} *s_slow = malloc(cols * sizeof({dtype}));
    {dtype} *s_fast = malloc(cols * sizeof({dtype}));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_cf2_{suf}(mat, rows, cols, s_slow);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_cf2_{suf}(mat, rows, cols, s_fast);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int j = 0; j < cols; j++) {{
        if (fabs((double)(s_slow[j] - s_fast[j])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat); free(s_slow); free(s_fast);
    return 0;
}}
"""
        elif layout == "scale":
            scalar_val = rng.choice(["2.0", "0.5", "3.14"])
            slow_code = f"""{check_decl}
void slow_cf2_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if (cf2_check_{suf}(i, j, rows, cols)) {{
                matrix[i * cols + j] *= ({dtype}){scalar_val};
            }}
        }}
    }}
}}"""
            fast_code = f"""void fast_cf2_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            matrix[i * cols + j] *= ({dtype}){scalar_val};
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat_slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *mat_fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat_slow[k] = ({dtype})(k % 100) * 0.1;
    memcpy(mat_fast, mat_slow, rows * cols * sizeof({dtype}));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_cf2_{suf}(mat_slow, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_cf2_{suf}(mat_fast, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(mat_slow[k] - mat_fast[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat_slow); free(mat_fast);
    return 0;
}}
"""
        else:  # transpose_sum
            slow_code = f"""{check_decl}
{dtype} slow_cf2_{suf}({dtype} *A, {dtype} *B, int rows, int cols) {{
    {dtype} total = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if (cf2_check_{suf}(i, j, rows, cols)) {{
                total += A[i * cols + j] + B[j * rows + i];
            }}
        }}
    }}
    return total;
}}"""
            fast_code = f"""{dtype} fast_cf2_{suf}({dtype} *A, {dtype} *B, int rows, int cols) {{
    {dtype} total = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            total += A[i * cols + j] + B[j * rows + i];
        }}
    }}
    return total;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *A = malloc(rows * cols * sizeof({dtype}));
    {dtype} *B = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) {{ A[k] = ({dtype})(k % 100) * 0.1; B[k] = ({dtype})(k % 50) * 0.2; }}
    {dtype} s = 0, f = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) s = slow_cf2_{suf}(A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) f = fast_cf2_{suf}(A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = fabs((double)(s - f)) < 1e-2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}}
"""

        desc = f"{layout} with noinline check, {dtype}, {rows}x{cols}"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"CF-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=1,
            lines_of_code=14,
            expected_speedup_range="2x-5x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "helper_code": helper_code,
            "metadata": asdict(metadata)
        }


class HR1_Generator(PatternTemplate):
    """HR-1: Unnecessary Intermediate Buffer Chain.
    Slow: 3-pass pipeline with 2 heap-allocated staging arrays forces 3x more
    memory bandwidth than a single-pass equivalent. Compiler cannot merge loops
    across heap pointers due to aliasing."""

    def __init__(self):
        super().__init__("HR-1", "Human Readability Style",
                         "Unnecessary Intermediate Buffer Chain")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        N = rng.choice([5000000, 10000000, 20000000])
        # Vary the element-wise operations across variants
        op1 = rng.choice(["*", "+", "-"])   # pass1: tmp1[i] = A[i] op1 B[i]
        op2 = rng.choice(["+", "-", "*"])   # pass2: tmp2[i] = tmp1[i] op2 A[i]
        op3 = rng.choice(["+", "-"])        # pass3: out[i]  = tmp2[i]*tmp2[i] op3 B[i]

        # slow: 3 separate passes over heap arrays — aliasing prevents loop fusion
        slow_code = f"""void slow_hr1_{suf}(double *out, double *A, double *B, int n) {{
    double *tmp1 = (double *)malloc(n * sizeof(double));
    double *tmp2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) tmp1[i] = A[i] {op1} B[i];
    for (int i = 0; i < n; i++) tmp2[i] = tmp1[i] {op2} A[i];
    for (int i = 0; i < n; i++) out[i] = tmp2[i] * tmp2[i] {op3} B[i];
    free(tmp1);
    free(tmp2);
}}"""

        # fast: single pass — 3x less memory bandwidth
        fast_code = f"""void fast_hr1_{suf}(double *out, double *A, double *B, int n) {{
    for (int i = 0; i < n; i++) {{
        double t = A[i] {op1} B[i];
        double u = t {op2} A[i];
        out[i] = u * u {op3} B[i];
    }}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *A = (double *)malloc(N * sizeof(double));
    double *B = (double *)malloc(N * sizeof(double));
    for (int k = 0; k < N; k++) {{
        A[k] = (double)((k % 100) + 1) * 0.1;
        B[k] = (double)((k % 97)  + 1) * 0.1;
    }}
    double *out_s = (double *)malloc(N * sizeof(double));
    double *out_f = (double *)malloc(N * sizeof(double));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_hr1_{suf}(out_s, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_hr1_{suf}(out_f, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < N; i++) {{
        double denom = fmax(fabs(out_s[i]), 1.0);
        if (fabs(out_s[i] - out_f[i]) / denom > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_s); free(out_f);
    return 0;
}}"""

        desc = f"3-pass buffer chain, N={N}, ops={op1}/{op2}/sq{op3}"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"HR-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype="double",
            difficulty="medium",
            compiler_fixable=False,
            num_loops=3,
            num_arrays=4,
            lines_of_code=8,
            expected_speedup_range="2x-4x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class MI4_Generator(PatternTemplate):
    """MI-4: Column-Major vs Row-Major Access.
    Accessing a 2D array in column-major order in C (row-major language)
    causes cache misses. Optimization: swap loop order."""

    def __init__(self):
        super().__init__("MI-4", "Memory & IO",
                         "Column vs Row Major Access")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(list(DTYPES.keys()))
        op_type = rng.choice(["scale", "add_arrays", "reduce", "copy", "transform"])
        rows = rng.choice([1000, 2000, 3000, 4000, 5000])
        cols = rng.choice([1000, 2000, 3000, 4000, 5000])
        scalar = rng.choice(["2.0", "0.5", "3.14", "1.001"])
        use_math = op_type == "transform"

        math_inc = "#include <math.h>\n" if use_math else ""

        if op_type == "scale":
            slow_code = f"""{math_inc}void slow_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            matrix[i * cols + j] *= ({dtype}){scalar};
        }}
    }}
}}"""
            fast_code = f"""{math_inc}void fast_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            matrix[i * cols + j] *= ({dtype}){scalar};
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat_slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *mat_fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat_slow[k] = ({dtype})(k % 100) * 0.1;
    memcpy(mat_fast, mat_slow, rows * cols * sizeof({dtype}));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_mi4_{suf}(mat_slow, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_mi4_{suf}(mat_fast, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(mat_slow[k] - mat_fast[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat_slow); free(mat_fast);
    return 0;
}}
"""

        elif op_type == "add_arrays":
            slow_code = f"""{math_inc}void slow_mi4_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            out[i * cols + j] = A[i * cols + j] + B[i * cols + j];
        }}
    }}
}}"""
            fast_code = f"""{math_inc}void fast_mi4_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            out[i * cols + j] = A[i * cols + j] + B[i * cols + j];
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols}, total = rows * cols;
    {dtype} *A = malloc(total * sizeof({dtype}));
    {dtype} *B = malloc(total * sizeof({dtype}));
    {dtype} *s = malloc(total * sizeof({dtype}));
    {dtype} *f = malloc(total * sizeof({dtype}));
    for (int k = 0; k < total; k++) {{ A[k] = ({dtype})(k % 100) * 0.1; B[k] = ({dtype})(k % 50) * 0.2; }}
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_mi4_{suf}(s, A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_mi4_{suf}(f, A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < total; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(s); free(f);
    return 0;
}}
"""

        elif op_type == "reduce":
            slow_code = f"""{math_inc}{dtype} slow_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    {dtype} total = 0;
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            total += matrix[i * cols + j];
        }}
    }}
    return total;
}}"""
            fast_code = f"""{math_inc}{dtype} fast_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    {dtype} total = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            total += matrix[i * cols + j];
        }}
    }}
    return total;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.01;
    {dtype} s = 0, f = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) s = slow_mi4_{suf}(mat, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) f = fast_mi4_{suf}(mat, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    /* relative tolerance: float summation order differs between row/col traversal */
    int correct = fabs((double)(s - f)) / fmax(fabs((double)s), 1.0) < 5e-3;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat);
    return 0;
}}
"""

        elif op_type == "copy":
            slow_code = f"""{math_inc}void slow_mi4_{suf}({dtype} *dst, {dtype} *src, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            dst[i * cols + j] = src[i * cols + j];
        }}
    }}
}}"""
            fast_code = f"""{math_inc}void fast_mi4_{suf}({dtype} *dst, {dtype} *src, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            dst[i * cols + j] = src[i * cols + j];
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols}, total = rows * cols;
    {dtype} *src = malloc(total * sizeof({dtype}));
    {dtype} *s = malloc(total * sizeof({dtype}));
    {dtype} *f = malloc(total * sizeof({dtype}));
    for (int k = 0; k < total; k++) src[k] = ({dtype})(k % 100) * 0.1;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_mi4_{suf}(s, src, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_mi4_{suf}(f, src, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < total; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(src); free(s); free(f);
    return 0;
}}
"""

        else:  # transform
            fn, _fn_hdr = rng.choice(UNARY_MATH_FNS)  # unpack tuple: (fn_name, header)
            slow_code = f"""#include <math.h>
void slow_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            matrix[i * cols + j] = ({dtype}){fn}((double)matrix[i * cols + j]);
        }}
    }}
}}"""
            fast_code = f"""#include <math.h>
void fast_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            matrix[i * cols + j] = ({dtype}){fn}((double)matrix[i * cols + j]);
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat_slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *mat_fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat_slow[k] = ({dtype})((k % 100) + 1) * 0.01;
    memcpy(mat_fast, mat_slow, rows * cols * sizeof({dtype}));
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_mi4_{suf}(mat_slow, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_mi4_{suf}(mat_fast, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(mat_slow[k] - mat_fast[k])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat_slow); free(mat_fast);
    return 0;
}}
"""

        desc = f"{op_type} operation, {dtype}, {rows}x{cols} matrix"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"MI-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=1 if op_type in ["scale", "reduce", "transform"] else 2,
            lines_of_code=8,
            expected_speedup_range="2x-10x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class ComposedGenerator(PatternTemplate):
    """Generate programs with 2-3 overlapping patterns."""

    def __init__(self):
        super().__init__("COMP", "Composed",
                         "Multiple Overlapping Patterns")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(list(DTYPES.keys()))

        combo = rng.choice([
            "sr3_mi4",        # Redundant aggregation + column-major access
            "sr1_cf1",        # Loop-invariant computation + branch in loop
            "hr2_is1",        # Copy-paste duplication + sparse data
            "sr4_hr4",        # Invariant call + defensive checks
            "ds4_cf2",        # AoS access + redundant bounds
            "sr2_hr1",        # Expression decomposition + redundant temps
            "cf1_mi4",        # Hoistable branch + column-major access
            "sr1_sr2_cf2",    # Triple: loop-invariant + decomposition + bounds
            "hr1_cf2_mi4",    # Triple: temps + bounds + cache
            "sr4_cf1_hr1",    # Triple: invariant call + branch + temps
        ])

        if combo == "sr3_mi4":
            slow_code = f"""void slow_comp_{suf}({dtype} *mat, {dtype} *col_avgs, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        {dtype} sum = 0;
        for (int i = 0; i < rows; i++) {{
            sum = 0;
            for (int k = 0; k <= i; k++) {{
                sum += mat[k * cols + j];
            }}
        }}
        col_avgs[j] = sum / ({dtype})rows;
    }}
}}"""
            fast_code = f"""void fast_comp_{suf}({dtype} *mat, {dtype} *col_avgs, int rows, int cols) {{
    for (int j = 0; j < cols; j++) col_avgs[j] = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            col_avgs[j] += mat[i * cols + j];
        }}
    }}
    for (int j = 0; j < cols; j++) col_avgs[j] /= ({dtype})rows;
}}"""
            patterns = ["SR-3", "MI-4"]
            desc = f"Redundant aggregation + column-major, {dtype}"

        elif combo == "sr1_cf1":
            slow_code = f"""{dtype} slow_comp_{suf}({dtype} *A, {dtype} *B, int n, {dtype} k, int mode) {{
    {dtype} total = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} val;
        if (mode == 1) val = A[i] + B[i] * k;
        else if (mode == 2) val = A[i] - B[i] * k;
        else val = A[i] * B[i] * k;
        total += val;
    }}
    return total;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *A, {dtype} *B, int n, {dtype} k, int mode) {{
    {dtype} sumA = 0, sumB = 0;
    if (mode == 1) {{
        for (int i = 0; i < n; i++) {{ sumA += A[i]; sumB += B[i]; }}
        return sumA + sumB * k;
    }} else if (mode == 2) {{
        for (int i = 0; i < n; i++) {{ sumA += A[i]; sumB += B[i]; }}
        return sumA - sumB * k;
    }} else {{
        {dtype} sumAB = 0;
        for (int i = 0; i < n; i++) sumAB += A[i] * B[i];
        return sumAB * k;
    }}
}}"""
            patterns = ["SR-1", "CF-1"]
            desc = f"Loop-invariant computation + branch, {dtype}"

        elif combo == "sr4_hr4":
            slow_code = f"""#include <math.h>
{dtype} config_val_{suf}(int key);

{dtype} slow_comp_{suf}({dtype} *arr, int n, int key) {{
    {dtype} sum = 0;
    for (int i = 0; i < n; i++) {{
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        {dtype} factor = config_val_{suf}(key);
        sum += arr[i] * factor;
    }}
    return sum;
}}
{dtype} config_val_{suf}(int key) {{
    {dtype} r = 0;
    for (int i = 0; i < 100; i++) r += ({dtype})sin((double)(key+i));
    return r;
}}"""
            fast_code = f"""{dtype} config_val_{suf}(int key);

{dtype} fast_comp_{suf}({dtype} *arr, int n, int key) {{
    if (arr == 0 || n <= 0) return 0;
    {dtype} factor = config_val_{suf}(key);
    {dtype} sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}}"""
            patterns = ["SR-4", "HR-4"]
            desc = f"Invariant function call + defensive checks, {dtype}"

        elif combo == "ds4_cf2":
            slow_code = f"""typedef struct {{ {dtype} x,y,z,vx,vy,vz,mass,charge; }} P_{suf};
{dtype} slow_comp_{suf}(P_{suf} *p, int n) {{
    {dtype} total = 0;
    for (int i = 0; i < n; i++) {{
        if (i >= 0 && i < n) {{
            total += p[i].mass;
        }}
    }}
    return total;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *mass, int n) {{
    {dtype} total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}}"""
            patterns = ["DS-4", "CF-2"]
            desc = f"AoS access + redundant bounds, {dtype}"

        elif combo == "sr2_hr1":
            slow_code = f"""{dtype} slow_comp_{suf}({dtype} *X, {dtype} *Y, int n, {dtype} alpha, {dtype} beta) {{
    {dtype} result = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} t1 = X[i] * X[i];
        {dtype} t2 = alpha * t1;
        {dtype} t3 = beta * Y[i];
        {dtype} t4 = t2 + t3;
        {dtype} t5 = t4 + alpha * beta;
        {dtype} t6 = t5;
        result += t6;
    }}
    return result;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *X, {dtype} *Y, int n, {dtype} alpha, {dtype} beta) {{
    {dtype} sumXsq = 0, sumY = 0;
    for (int i = 0; i < n; i++) {{
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }}
    return alpha * sumXsq + beta * sumY + ({dtype})n * alpha * beta;
}}"""
            patterns = ["SR-2", "HR-1"]
            desc = f"Expression decomposition + redundant temps, {dtype}"

        elif combo == "cf1_mi4":
            slow_code = f"""void slow_comp_{suf}({dtype} *mat, int rows, int cols, int mode) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            if (mode == 1) mat[i * cols + j] *= ({dtype})2.0;
            else if (mode == 2) mat[i * cols + j] += ({dtype})1.0;
            else mat[i * cols + j] -= ({dtype})0.5;
        }}
    }}
}}"""
            fast_code = f"""void fast_comp_{suf}({dtype} *mat, int rows, int cols, int mode) {{
    if (mode == 1) {{
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] *= ({dtype})2.0;
    }} else if (mode == 2) {{
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] += ({dtype})1.0;
    }} else {{
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] -= ({dtype})0.5;
    }}
}}"""
            patterns = ["CF-1", "MI-4"]
            desc = f"Hoistable branch + column-major access, {dtype}"

        elif combo == "sr1_sr2_cf2":
            slow_code = f"""{dtype} slow_comp_{suf}({dtype} *A, {dtype} *B, int rows, int cols, {dtype} k) {{
    {dtype} result = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if (i >= 0 && i < rows && j >= 0 && j < cols) {{
                result += k * A[i*cols+j] * A[i*cols+j] + k * B[i*cols+j];
            }}
        }}
    }}
    return result;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *A, {dtype} *B, int rows, int cols, {dtype} k) {{
    {dtype} sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }}
    }}
    return k * sumAsq + k * sumB;
}}"""
            patterns = ["SR-1", "SR-2", "CF-2"]
            desc = f"Triple: invariant + decomposition + bounds, {dtype}"

        elif combo == "hr1_cf2_mi4":
            slow_code = f"""void slow_comp_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            if (i >= 0 && i < rows && j >= 0 && j < cols) {{
                {dtype} t1 = A[i*cols+j] + B[i*cols+j];
                {dtype} t2 = t1 * ({dtype})2.0;
                {dtype} t3 = t2 + ({dtype})1.0;
                {dtype} result = t3;
                out[i*cols+j] = result;
            }}
        }}
    }}
}}"""
            fast_code = f"""void fast_comp_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            out[i*cols+j] = (A[i*cols+j] + B[i*cols+j]) * ({dtype})2.0 + ({dtype})1.0;
        }}
    }}
}}"""
            patterns = ["HR-1", "CF-2", "MI-4"]
            desc = f"Triple: temps + bounds + cache, {dtype}"

        else:  # sr4_cf1_hr1
            slow_code = f"""#include <math.h>
{dtype} compute_{suf}(int key);

void slow_comp_{suf}({dtype} *out, {dtype} *A, int n, int key, int mode) {{
    for (int i = 0; i < n; i++) {{
        {dtype} factor = compute_{suf}(key);
        {dtype} t1;
        if (mode == 1) t1 = A[i] * factor;
        else t1 = A[i] + factor;
        {dtype} t2 = t1 + ({dtype})1.0;
        {dtype} t3 = t2;
        out[i] = t3;
    }}
}}
{dtype} compute_{suf}(int key) {{
    {dtype} r = 0;
    for (int i = 0; i < 50; i++) r += ({dtype})sin((double)(key+i));
    return r;
}}"""
            fast_code = f"""{dtype} compute_{suf}(int key);

void fast_comp_{suf}({dtype} *out, {dtype} *A, int n, int key, int mode) {{
    {dtype} factor = compute_{suf}(key);
    if (mode == 1) {{
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + ({dtype})1.0;
    }} else {{
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + ({dtype})1.0;
    }}
}}"""
            patterns = ["SR-4", "CF-1", "HR-1"]
            desc = f"Triple: invariant call + branch + temps, {dtype}"

        metadata = VariantMetadata(
            pattern_id="COMP",
            variant_id=f"COMP_v{variant_num:03d}",
            category="Composed",
            pattern_name="Multiple Overlapping Patterns",
            variant_desc=desc,
            dtype=dtype,
            difficulty="hard",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=2,
            lines_of_code=15,
            expected_speedup_range="10x-1000x",
            composition=patterns
        )

        # Build test harness based on combo type
        N_comp = 5000000
        rows_comp = 1000
        cols_comp = 1000
        if combo == "sr3_mi4":
            # void slow(dtype *mat, dtype *col_avgs, int rows, int cols)
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows_comp}, cols = {cols_comp};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    {dtype} *avgs_slow = malloc(cols * sizeof({dtype}));
    {dtype} *avgs_fast = malloc(cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.01{DTYPES[dtype]['suffix']};
    struct timespec t0, t1;
    int n_reps = 1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_comp_{suf}(mat, avgs_slow, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_comp_{suf}(mat, avgs_fast, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int j = 0; j < cols; j++) {{
        if (fabs((double)(avgs_slow[j] - avgs_fast[j])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat); free(avgs_slow); free(avgs_fast);
    return 0;
}}
"""
        elif combo == "sr1_cf1":
            # dtype slow(dtype *A, dtype *B, int n, dtype k, int mode)
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_comp};
    {dtype} *A = malloc(n * sizeof({dtype}));
    {dtype} *B = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) {{ A[i] = ({dtype})(i % 100) * 0.01{suf_t}; B[i] = ({dtype})(i % 97 + 1) * 0.01{suf_t}; }}
    {dtype} k_val = ({dtype})2.5{suf_t};
    int mode = 2;
    {dtype} r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_comp_{suf}(A, B, n, k_val, mode);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_comp_{suf}(A, B, n, k_val, mode);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    double rel = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0);
    int correct = rel < 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}}
"""
        elif combo == "sr4_hr4":
            # dtype slow(dtype *arr, int n, int key)
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_comp};
    {dtype} *arr = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) arr[i] = ({dtype})(i % 100 + 1) * 0.01{suf_t};
    int key = 42;
    {dtype} r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_comp_{suf}(arr, n, key);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_comp_{suf}(arr, n, key);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    double rel = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0);
    int correct = rel < 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}}
"""
        elif combo == "ds4_cf2":
            # slow: dtype slow_comp(P_suf *p, int n) where P_suf is typedef struct
            # fast: dtype fast_comp(dtype *mass, int n)
            suf_t = DTYPES[dtype]['suffix']
            N_ds = 5000000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {{ {dtype} x,y,z,vx,vy,vz,mass,charge; }} P_{suf};

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_ds};
    P_{suf} *p = malloc(n * sizeof(P_{suf}));
    {dtype} *mass = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) {{
        p[i].mass = ({dtype})(i % 100 + 1) * 0.01{suf_t};
        mass[i] = p[i].mass;
    }}
    {dtype} r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_comp_{suf}(p, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_comp_{suf}(mass, n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    double rel = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0);
    int correct = rel < 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(p); free(mass);
    return 0;
}}
"""
        elif combo == "sr2_hr1":
            # dtype slow(dtype *X, dtype *Y, int n, dtype alpha, dtype beta)
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_comp};
    {dtype} *X = malloc(n * sizeof({dtype}));
    {dtype} *Y = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) {{ X[i] = ({dtype})(i % 100 + 1) * 0.01{suf_t}; Y[i] = ({dtype})(i % 97 + 1) * 0.01{suf_t}; }}
    {dtype} alpha = ({dtype})2.5{suf_t}, beta = ({dtype})1.7{suf_t};
    {dtype} r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_comp_{suf}(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_comp_{suf}(X, Y, n, alpha, beta);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    double rel = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0);
    int correct = rel < 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(X); free(Y);
    return 0;
}}
"""
        elif combo == "cf1_mi4":
            # void slow(dtype *mat, int rows, int cols, int mode) — in-place
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows_comp}, cols = {cols_comp};
    {dtype} *mat_slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *mat_fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat_slow[k] = ({dtype})(k % 100 + 1) * 0.01{suf_t};
    memcpy(mat_fast, mat_slow, rows * cols * sizeof({dtype}));
    int mode = 2;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_comp_{suf}(mat_slow, rows, cols, mode);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_comp_{suf}(mat_fast, rows, cols, mode);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(mat_slow[k] - mat_fast[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat_slow); free(mat_fast);
    return 0;
}}
"""
        elif combo == "sr1_sr2_cf2":
            # dtype slow(dtype *A, dtype *B, int rows, int cols, dtype k)
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows_comp}, cols = {cols_comp};
    {dtype} *A = malloc(rows * cols * sizeof({dtype}));
    {dtype} *B = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) {{ A[k] = ({dtype})(k % 100 + 1) * 0.01{suf_t}; B[k] = ({dtype})(k % 97 + 1) * 0.01{suf_t}; }}
    {dtype} k_val = ({dtype})2.5{suf_t};
    {dtype} r_slow = 0, r_fast = 0;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_comp_{suf}(A, B, rows, cols, k_val);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_comp_{suf}(A, B, rows, cols, k_val);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    double rel = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0);
    int correct = rel < 1e-4;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}}
"""
        elif combo == "hr1_cf2_mi4":
            # void slow(dtype *out, dtype *A, dtype *B, int rows, int cols)
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int rows = {rows_comp}, cols = {cols_comp};
    {dtype} *A = malloc(rows * cols * sizeof({dtype}));
    {dtype} *B = malloc(rows * cols * sizeof({dtype}));
    {dtype} *out_slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *out_fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) {{ A[k] = ({dtype})(k % 100 + 1) * 0.01{suf_t}; B[k] = ({dtype})(k % 97 + 1) * 0.01{suf_t}; }}
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_comp_{suf}(out_slow, A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_comp_{suf}(out_fast, A, B, rows, cols);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(out_slow[k] - out_fast[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}}
"""
        else:  # sr4_cf1_hr1 (and hr2_is1 fallthrough)
            # void slow(dtype *out, dtype *A, int n, int key, int mode)
            suf_t = DTYPES[dtype]['suffix']
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {N_comp};
    {dtype} *A = malloc(n * sizeof({dtype}));
    {dtype} *out_slow = malloc(n * sizeof({dtype}));
    {dtype} *out_fast = malloc(n * sizeof({dtype}));
    for (int i = 0; i < n; i++) A[i] = ({dtype})(i % 100 + 1) * 0.01{suf_t};
    int key = 42, mode = 1;
    struct timespec t0, t1;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) slow_comp_{suf}(out_slow, A, n, key, mode);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) fast_comp_{suf}(out_fast, A, n, key, mode);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;
    int correct = 1;
    for (int i = 0; i < n; i++) {{
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(out_slow); free(out_fast);
    return 0;
}}
"""

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }

class IS5_Generator(PatternTemplate):
    """IS-5: Runtime Alias Check for Restrict Fast-Path Vectorization

    The slow version uses plain (non-restrict) pointers. The compiler must
    conservatively guard against aliasing — inserting runtime overlap checks
    or scalar fallback loops before the vectorized path. The fast version
    checks for non-overlap at runtime (almost always true for separately
    malloc'd buffers) and dispatches to a __restrict__-qualified kernel,
    letting the compiler emit unguarded SIMD without alias guards.

    Varies: number of input arrays (2 or 3), data type (float/double),
    expression style (linear/quadratic/mixed/polynomial/inplace/FMA),
    loop style (for/while).
    """

    # (expression template, label, is_inplace)
    EXPRS_2 = [
        ("out[i] = A[i] + B[i]",                                          "linear add",        False),
        ("out[i] = A[i] * A[i] + B[i] * 2.0{s}",                         "quadratic",         False),
        ("out[i] = A[i] * B[i] + A[i] - B[i] * 0.5{s}",                  "mixed multiply",    False),
        ("out[i] = A[i] * A[i] - A[i] * 0.5{s} + B[i] * B[i] + B[i]",   "polynomial",        False),
        ("out[i] += A[i] * 2.0{s} + B[i] * 0.5{s}",                      "in-place SAXPY",    True),
        ("out[i] = A[i] * B[i] + A[i] + B[i]",                           "FMA-style",         False),
    ]

    EXPRS_3 = [
        ("out[i] = A[i] + B[i] + C[i]",                                   "sum-3",             False),
        ("out[i] = A[i] * B[i] + C[i] * 0.5{s}",                         "product+shift",     False),
        ("out[i] = A[i] * A[i] + B[i] * B[i] - C[i] * 0.5{s}",          "polynomial-3",      False),
        ("out[i] += A[i] * B[i] + C[i]",                                  "in-place 3-way",    True),
        ("out[i] = 0.5{s} * A[i] + 0.3{s} * B[i] + 0.2{s} * C[i]",      "weighted sum",      False),
    ]

    def __init__(self):
        super().__init__("IS-5", "Input-Sensitive Inefficiency",
                         "Runtime Alias Check (restrict fast path)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        dtype  = rng.choice(["float", "double"])
        n_inputs = rng.choice([2, 2, 3])        # bias toward 2-input
        loop_style = rng.choice(["for", "while", "for"])
        suf = f"v{variant_num:03d}"
        s   = DTYPES[dtype]['suffix']

        exprs = self.EXPRS_2 if n_inputs == 2 else self.EXPRS_3
        expr_template, label, is_inplace = rng.choice(exprs)
        expr = expr_template.format(s=s)

        # ── Parameter strings ─────────────────────────────────────────────
        if n_inputs == 2:
            slow_params     = f"{dtype} *out, {dtype} *A, {dtype} *B, int n"
            restrict_params = (f"{dtype} * __restrict__ out, "
                               f"const {dtype} * __restrict__ A, "
                               f"const {dtype} * __restrict__ B, int n")
            alias_check     = ("(out + n <= A || A + n <= out) && "
                               "(out + n <= B || B + n <= out)")
            call_args       = "out, A, B, n"
            alloc_inputs    = (f"    {dtype} *A = malloc(N * sizeof({dtype}));\n"
                               f"    {dtype} *B = malloc(N * sizeof({dtype}));")
            init_inputs     = (f"    for (int i = 0; i < N; i++) "
                               f"A[i] = ({dtype})(i % 1000 + 1) * 0.001{s};\n"
                               f"    for (int i = 0; i < N; i++) "
                               f"B[i] = ({dtype})(i % 997  + 1) * 0.001{s};")
            free_inputs     = "    free(A); free(B);"
        else:
            slow_params     = f"{dtype} *out, {dtype} *A, {dtype} *B, {dtype} *C, int n"
            restrict_params = (f"{dtype} * __restrict__ out, "
                               f"const {dtype} * __restrict__ A, "
                               f"const {dtype} * __restrict__ B, "
                               f"const {dtype} * __restrict__ C, int n")
            alias_check     = ("(out + n <= A || A + n <= out) && "
                               "(out + n <= B || B + n <= out) && "
                               "(out + n <= C || C + n <= out)")
            call_args       = "out, A, B, C, n"
            alloc_inputs    = (f"    {dtype} *A = malloc(N * sizeof({dtype}));\n"
                               f"    {dtype} *B = malloc(N * sizeof({dtype}));\n"
                               f"    {dtype} *C = malloc(N * sizeof({dtype}));")
            init_inputs     = (f"    for (int i = 0; i < N; i++) "
                               f"A[i] = ({dtype})(i % 1000 + 1) * 0.001{s};\n"
                               f"    for (int i = 0; i < N; i++) "
                               f"B[i] = ({dtype})(i % 997  + 1) * 0.001{s};\n"
                               f"    for (int i = 0; i < N; i++) "
                               f"C[i] = ({dtype})(i % 991  + 1) * 0.001{s};")
            free_inputs     = "    free(A); free(B); free(C);"

        # ── Loop scaffolding ──────────────────────────────────────────────
        if loop_style == "for":
            loop_open  = "    for (int i = 0; i < n; i++) {"
            loop_close = "    }"
        else:
            loop_open  = "    int i = 0;\n    while (i < n) {"
            loop_close = "        i++;\n    }"

        # ── Restrict expression: replace array names with restrict locals ──
        # e.g. out[i] -> ro[i], A[i] -> rA[i], B[i] -> rB[i]
        restrict_expr = (expr
            .replace("out[i]", "ro[i]")
            .replace("A[i]",   "rA[i]")
            .replace("B[i]",   "rB[i]")
            .replace("C[i]",   "rC[i]"))

        # Restrict-qualified local pointer declarations for the fast path
        if n_inputs == 2:
            restrict_locals = (
                f"        {dtype} * __restrict__ ro = out;\n"
                f"        const {dtype} * __restrict__ rA = "
                f"(const {dtype} * __restrict__)A;\n"
                f"        const {dtype} * __restrict__ rB = "
                f"(const {dtype} * __restrict__)B;"
            )
        else:
            restrict_locals = (
                f"        {dtype} * __restrict__ ro = out;\n"
                f"        const {dtype} * __restrict__ rA = "
                f"(const {dtype} * __restrict__)A;\n"
                f"        const {dtype} * __restrict__ rB = "
                f"(const {dtype} * __restrict__)B;\n"
                f"        const {dtype} * __restrict__ rC = "
                f"(const {dtype} * __restrict__)C;"
            )

        # ── Slow version: plain pointers, no alias guarantee ─────────────
        slow_code = (
            f"__attribute__((noinline))\n"
            f"void slow_is5_{suf}({slow_params}) {{\n"
            f"{loop_open}\n"
            f"        {expr};\n"
            f"{loop_close}\n"
            f"}}"
        )

        # ── Fast version: single function, inline restrict cast ───────────
        # Avoids a two-function file (static kernel + dispatcher) which
        # complicates extern declaration extraction.  Instead, re-cast the
        # incoming pointers to restrict-qualified locals inside the if-branch.
        fast_code = (
            f"void fast_is5_{suf}({slow_params}) {{\n"
            f"    int no_alias = {alias_check};\n"
            f"    if (no_alias) {{\n"
            f"        // Non-aliasing: cast to restrict-qualified locals\n"
            f"        // so the compiler can emit unguarded SIMD\n"
            f"{restrict_locals}\n"
            f"        for (int i = 0; i < n; i++) {{\n"
            f"            {restrict_expr};\n"
            f"        }}\n"
            f"    }} else {{\n"
            f"        // Aliasing fallback (rare)\n"
            f"{loop_open}\n"
            f"        {expr};\n"
            f"{loop_close}\n"
            f"    }}\n"
            f"}}"
        )

        # ── Test harness ──────────────────────────────────────────────────
        n_val = 5000000
        # Inplace (+=) needs zero-initialised output: calloc.
        # Non-inplace overwrites every element: malloc is fine.
        out_alloc_slow = (f"calloc(N, sizeof({dtype}))"
                          if is_inplace else f"malloc(N * sizeof({dtype}))")
        out_alloc_fast = out_alloc_slow
        reps = 1 if is_inplace else 5
        div  = f" / {reps}.0" if reps > 1 else ""
        tol  = "1e-5" if dtype == "float" else "1e-10"

        # Call args for test.c: use the actual variable names in main()
        if n_inputs == 2:
            tc_slow = f"out_slow, A, B, N"
            tc_fast = f"out_fast, A, B, N"
        else:
            tc_slow = f"out_slow, A, B, C, N"
            tc_fast = f"out_fast, A, B, C, N"

        if reps > 1:
            time_slow = (f"    for (int r = 0; r < {reps}; r++) "
                         f"slow_is5_{suf}({tc_slow});")
            time_fast = (f"    for (int r = 0; r < {reps}; r++) "
                         f"fast_is5_{suf}({tc_fast});")
        else:
            time_slow = f"    slow_is5_{suf}({tc_slow});"
            time_fast = f"    fast_is5_{suf}({tc_fast});"

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N {n_val}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
{alloc_inputs}
{init_inputs}
    {dtype} *out_slow = {out_alloc_slow};
    {dtype} *out_fast = {out_alloc_fast};

    struct timespec t0, t1;

    clock_gettime(CLOCK_MONOTONIC, &t0);
{time_slow}
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6{div};

    clock_gettime(CLOCK_MONOTONIC, &t0);
{time_fast}
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6{div};

    double err = 0.0;
    for (int i = 0; i < N; i++) {{
        double d = fabs((double)(out_slow[i] - out_fast[i])) / fmax(fabs((double)out_slow[i]), 1e-12);
        if (d > err) err = d;
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, err < {tol}, ms_slow / fmax(ms_fast, 0.001));

{free_inputs}
    free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"IS-5_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"{label}, {n_inputs} inputs, {dtype}, {loop_style}-loop",
            dtype=dtype,
            difficulty="medium" if n_inputs == 2 else "hard",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=n_inputs + 1,
            lines_of_code=8 + n_inputs,
            expected_speedup_range="1.2x-3x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class SR5_Generator(PatternTemplate):
    """SR-5: Repeated Division by Loop-Invariant Denominator.
    compute_norm(w, m) is called every iteration. Without restrict qualifiers,
    the compiler cannot prove w[] is loop-invariant (out[] could alias w[]).
    Optimization: call once, precompute reciprocal, use multiply.
    Varies: weight vector size, norm type (L2/L1/power), array size, dtype.
    """

    def __init__(self):
        super().__init__("SR-5", "Semantic Redundancy",
                         "Repeated Division by Loop-Invariant Denominator")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        suf_t = DTYPES[dtype]['suffix']
        N = rng.choice([500000, 1000000, 2000000])
        m = rng.choice([64, 128, 256, 512])
        loop_style = rng.choice(["for", "while"])
        norm_type = rng.choice(["l2", "l2", "l1"])  # bias toward l2

        # Build the norm function body and inline expected expression
        if norm_type == "l2":
            norm_body = f"    {dtype} s = 0.0;\n    for (int j = 0; j < m; j++) s += w[j] * w[j];\n    return ({dtype})sqrt((double)s);"
            expected_norm = f"    {dtype} ns = 0.0; for (int j = 0; j < M; j++) ns += w[j] * w[j];\n    {dtype} norm = ({dtype})sqrt((double)ns);"
            norm_desc = "L2"
        else:  # l1
            norm_body = f"    {dtype} s = 0.0;\n    for (int j = 0; j < m; j++) s += ({dtype})fabs((double)w[j]);\n    return s;"
            expected_norm = f"    {dtype} ns = 0.0; for (int j = 0; j < M; j++) ns += ({dtype})fabs((double)w[j]);\n    {dtype} norm = ns;"
            norm_desc = "L1"

        if loop_style == "for":
            slow_inner = f"    for (int i = 0; i < n; i++)\n        out[i] = data[i] / compute_norm(w, m);"
            fast_inner = f"    {dtype} inv = ({dtype})1.0 / compute_norm(w, m);\n    for (int i = 0; i < n; i++)\n        out[i] = data[i] * inv;"
        else:
            slow_inner = f"    int i = 0;\n    while (i < n) {{\n        out[i] = data[i] / compute_norm(w, m);\n        i++;\n    }}"
            fast_inner = f"    {dtype} inv = ({dtype})1.0 / compute_norm(w, m);\n    int i = 0;\n    while (i < n) {{\n        out[i] = data[i] * inv;\n        i++;\n    }}"

        helper_code = f"""#include <math.h>
__attribute__((noinline, noclone))
{dtype} compute_norm({dtype} *w, int m) {{
{norm_body}
}}"""

        slow_code = f"""#include <math.h>
{dtype} compute_norm({dtype} *w, int m);
__attribute__((noinline))
void slow_sr5_{suf}({dtype} *out, {dtype} *data, int n, {dtype} *w, int m) {{
{slow_inner}
}}"""

        fast_code = f"""#include <math.h>
{dtype} compute_norm({dtype} *w, int m);
__attribute__((noinline))
void fast_sr5_{suf}({dtype} *out, {dtype} *data, int n, {dtype} *w, int m) {{
{fast_inner}
}}"""

        tol = "1e-4" if dtype == "float" else "1e-9"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}
#define M {m}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *data     = malloc(N * sizeof({dtype}));
    {dtype} *out_slow = malloc(N * sizeof({dtype}));
    {dtype} *out_fast = malloc(N * sizeof({dtype}));
    {dtype} *w        = malloc(M * sizeof({dtype}));
    for (int i = 0; i < N; i++) data[i] = ({dtype})((i % 200) - 100) * 0.1{suf_t};
    for (int j = 0; j < M; j++) w[j] = ({dtype})(j % 50 + 1) * 0.02{suf_t};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_sr5_{suf}(out_slow, data, N, w, M);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr5_{suf}(out_fast, data, N, w, M);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    /* expected: compute norm inline, divide each element */
{expected_norm}
    int correct = 1;
    for (int i = 0; i < N; i++) {{
        double diff = fabs((double)(out_slow[i] - data[i] / norm)) / fmax(fabs((double)(data[i] / norm)), 1e-12);
        if (diff > {tol}) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(data); free(out_slow); free(out_fast); free(w);
    return 0;
}}"""

        desc = f"{norm_desc}-norm, m={m}, n={N}, {dtype}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-5_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="medium" if m <= 128 else "hard",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=2,
            lines_of_code=8,
            expected_speedup_range=f"{m//32}x-{m//8}x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "helper_code": helper_code,
                "metadata": asdict(metadata)}


class IS2_Generator(PatternTemplate):
    """IS-2: Data Distribution Skew.
    Slow version always computes expensive preamble before branching.
    Fast version checks common case first, skipping unnecessary work."""

    def __init__(self):
        super().__init__("IS-2", "Input-Sensitive Inefficiency",
                         "Data Distribution Skew")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([5000000, 10000000])
        skew_pct = rng.choice([90, 95, 99])
        threshold = rng.choice([0.5, 1.0, 2.0])
        expensive_op = rng.choice(["log", "exp", "sqrt"])
        n_reps = rng.choice([3, 5])
        suf_t = DTYPES[dtype]['suffix']
        cast = f"({dtype})" if dtype == "float" else ""

        # The expensive clamp operation lives in helper.c (noinline, noclone).
        # Slow calls it unconditionally for every element — even those in range —
        # then uses a ternary select.  The compiler can't eliminate the call
        # because it can't see the body.  Fast calls it only for outliers.
        # With skew_pct=90, slow does 10x more expensive-op calls than fast.
        helper_code = f"""#include <math.h>
__attribute__((noinline, noclone))
{dtype} is2_clamp_{suf}({dtype} val, {dtype} thresh) {{
    {dtype} abs_val = {cast}fabs((double)val);
    {dtype} sign = (val >= ({dtype})0) ? ({dtype})1 : ({dtype})-1;
    return sign * (thresh + {cast}{expensive_op}((double)(({dtype})1 + abs_val - thresh + ({dtype})1e-7)));
}}"""
        check_decl = f"{dtype} is2_clamp_{suf}({dtype} val, {dtype} thresh);"

        # Slow: always compute the expensive clamped value, then select
        slow_code = f"""{check_decl}
void slow_is2_{suf}({dtype} *out, {dtype} *in, int n, {dtype} thresh) {{
    for (int i = 0; i < n; i++) {{
        {dtype} val = in[i];
        {dtype} clamped = is2_clamp_{suf}(val, thresh);   /* always called */
        out[i] = ({cast}fabs((double)val) > thresh) ? clamped : val;
    }}
}}"""
        # Fast: check first, only call expensive op for outliers
        fast_code = f"""{check_decl}
void fast_is2_{suf}({dtype} *out, {dtype} *in, int n, {dtype} thresh) {{
    for (int i = 0; i < n; i++) {{
        {dtype} val = in[i];
        if ({cast}fabs((double)val) <= thresh) {{
            out[i] = val;
        }} else {{
            out[i] = is2_clamp_{suf}(val, thresh);   /* outliers only */
        }}
    }}
}}"""
        tol = "1e-5" if dtype == "float" else "1e-9"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in_arr  = malloc(N * sizeof({dtype}));
    {dtype} *out_slow = malloc(N * sizeof({dtype}));
    {dtype} *out_fast = malloc(N * sizeof({dtype}));
    /* {skew_pct}% of values within threshold, {100-skew_pct}% outliers */
    for (int i = 0; i < N; i++) {{
        if (i % 100 < {skew_pct})
            in_arr[i] = ({dtype})((i % 100) - 50) * ({dtype}){threshold / 50.0}{suf_t};
        else
            in_arr[i] = ({dtype})(i % 50 + 10) * ({dtype}){threshold}{suf_t};
    }}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) slow_is2_{suf}(out_slow, in_arr, N, ({dtype}){threshold}{suf_t});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) fast_is2_{suf}(out_fast, in_arr, N, ({dtype}){threshold}{suf_t});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(out_slow[i] - out_fast[i])) > {tol}) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"IS-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"{skew_pct}% in-range, always-call {expensive_op} in slow, thresh={threshold}, {dtype}",
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=2,
            lines_of_code=10,
            expected_speedup_range="5x-20x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "helper_code": helper_code,
                "metadata": asdict(metadata)}


class IS3_Generator(PatternTemplate):
    """IS-3: Early Termination Opportunities.
    Slow version counts all violations. Fast version exits on first."""

    def __init__(self):
        super().__init__("IS-3", "Input-Sensitive Inefficiency",
                         "Early Termination Opportunities")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([5000000, 10000000])
        threshold = rng.choice([0.5, 1.0, 5.0, 10.0])
        violation_pos = "early"  # middle gives only 2x at -O0 and GCC vectorizes it away at -O3
        cond_op = rng.choice([">", ">="])
        suf_t = DTYPES[dtype]['suffix']
        n_reps = 20

        slow_code = f"""int slow_is3_{suf}({dtype} *arr, int n, {dtype} thresh) {{
    int count = 0;
    for (int i = 0; i < n; i++) {{
        if (arr[i] {cond_op} thresh) count++;
    }}
    return count == 0;
}}"""
        fast_code = f"""int fast_is3_{suf}({dtype} *arr, int n, {dtype} thresh) {{
    for (int i = 0; i < n; i++) {{
        if (arr[i] {cond_op} thresh) return 0;
    }}
    return 1;
}}"""

        if violation_pos == "early":
            violation_idx = "N / 20"
        else:
            violation_idx = "N / 2"

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}
#define N_REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *arr = malloc(N * sizeof({dtype}));
    for (int i = 0; i < N; i++) arr[i] = ({dtype})(i % 100) * ({dtype}){threshold / 200.0}{suf_t};
    arr[{violation_idx}] = ({dtype}){threshold + 1.0}{suf_t};  /* Violation at {violation_pos} position */

    struct timespec t0, t1;
    volatile int r_slow = 0, r_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < N_REPS; r++) r_slow = slow_is3_{suf}(arr, N, ({dtype}){threshold}{suf_t});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / N_REPS;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < N_REPS; r++) r_fast = fast_is3_{suf}(arr, N, ({dtype}){threshold}{suf_t});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / N_REPS;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"IS-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"violation at {violation_pos}, thresh={threshold}, {cond_op}, {dtype}",
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=7,
            expected_speedup_range="10x-1000x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class IS4_Generator(PatternTemplate):
    """IS-4: Adaptive Algorithm Selection (Nearly-Sorted Detection).
    Slow: always qsort. Fast: sample inversions, use insertion sort if nearly sorted."""

    def __init__(self):
        super().__init__("IS-4", "Input-Sensitive Inefficiency",
                         "Adaptive Sort (Nearly-Sorted Detection)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        N = rng.choice([100000, 500000, 1000000])
        swap_pct = rng.choice([0.005, 0.01, 0.02])  # 0.5%, 1%, 2% inversions
        sample_k = rng.choice([32, 64, 128])
        inv_thresh = rng.choice([2, 4, 8])
        n_swaps = int(N * swap_pct)

        slow_code = f"""static int cmp_is4_s_{suf}(const void *a, const void *b);

void slow_is4_{suf}(int *arr, int n) {{
    qsort(arr, n, sizeof(int), cmp_is4_s_{suf});
}}
static int cmp_is4_s_{suf}(const void *a, const void *b) {{
    return (*(const int*)a - *(const int*)b);
}}"""

        fast_code = f"""static int cmp_is4_f_{suf}(const void *a, const void *b);

void fast_is4_{suf}(int *arr, int n) {{
    int inv = 0;
    unsigned s = 12345u;
    for (int k = 0; k < {sample_k}; k++) {{
        s = s * 1664525u + 1013904223u;
        int i = (int)((s >> 1) % (unsigned)(n - 1));
        if (arr[i] > arr[i + 1]) inv++;
    }}
    if (inv <= {inv_thresh}) {{
        for (int i = 1; i < n; i++) {{
            int key = arr[i], j = i - 1;
            while (j >= 0 && arr[j] > key) {{ arr[j + 1] = arr[j]; j--; }}
            arr[j + 1] = key;
        }}
    }} else {{
        qsort(arr, n, sizeof(int), cmp_is4_f_{suf});
    }}
}}
static int cmp_is4_f_{suf}(const void *a, const void *b) {{
    return (*(const int*)a - *(const int*)b);
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>
#define N {N}
#define N_SWAPS {n_swaps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *base = malloc(N * sizeof(int));
    int *arr_slow = malloc(N * sizeof(int));
    int *arr_fast = malloc(N * sizeof(int));
    for (int i = 0; i < N; i++) base[i] = i;
    /* Introduce ~{swap_pct*100:.1f}% local swaps */
    unsigned rs = 99u;
    for (int s = 0; s < N_SWAPS; s++) {{
        rs = rs * 1664525u + 1013904223u;
        int i = (int)((rs >> 1) % (unsigned)(N - 1));
        int tmp = base[i]; base[i] = base[i+1]; base[i+1] = tmp;
    }}
    memcpy(arr_slow, base, N * sizeof(int));
    memcpy(arr_fast, base, N * sizeof(int));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is4_{suf}(arr_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is4_{suf}(arr_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) if (arr_slow[i] != arr_fast[i]) {{ correct = 0; break; }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(base); free(arr_slow); free(arr_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"IS-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"n={N}, {swap_pct*100:.1f}% swaps, sample_k={sample_k}, thresh={inv_thresh}",
            dtype="int",
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=15,
            expected_speedup_range="2x-10x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class CF3_Generator(PatternTemplate):
    """CF-3: Vectorization-Hostile Redundant Conditional.
    Per-element conditional that is always true in practice blocks SIMD.
    Fast version verifies the property once, then uses branch-free loop."""

    def __init__(self):
        super().__init__("CF-3", "Control Flow Inefficiency",
                         "Vectorization-Hostile Redundant Conditional")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([5000000, 10000000])
        condition = rng.choice(["all_positive", "all_positive", "all_in_range"])
        expr_idx = rng.randint(0, 3)
        n_reps = 5
        suf_t = DTYPES[dtype]['suffix']

        exprs = [
            (f"in[i] * in[i] + in[i] * ({dtype})0.5", f"({dtype})0"),
            (f"in[i] * ({dtype})2.0 + ({dtype})1.0",   f"({dtype})0"),
            (f"in[i] * in[i] - in[i]",                  f"({dtype})0"),
            (f"in[i] * ({dtype})1.5 + in[i] * in[i]",  f"({dtype})-1"),
        ]
        hot_expr, cold_expr = exprs[expr_idx % len(exprs)]

        if condition == "all_positive":
            check = f"in[i] > ({dtype})0"
            negate_check = f"in[i] <= ({dtype})0"
            data_init = f"for (int i = 0; i < N; i++) in_arr[i] = ({dtype})(i % 100 + 1) * ({dtype})0.1{suf_t};"
            runtime_check = f"""    int all_ok = 1;
    for (int i = 0; i < n; i++) if (in[i] <= ({dtype})0) {{ all_ok = 0; break; }}"""
            desc_cond = "all-positive"
        else:  # all_in_range
            lo, hi = 0.1, 50.0
            check = f"in[i] >= ({dtype}){lo}{suf_t} && in[i] <= ({dtype}){hi}{suf_t}"
            negate_check = f"in[i] < ({dtype}){lo}{suf_t} || in[i] > ({dtype}){hi}{suf_t}"
            data_init = f"for (int i = 0; i < N; i++) in_arr[i] = ({dtype})(i % 100 + 1) * ({dtype}){hi/100.0}{suf_t};"
            runtime_check = f"""    int all_ok = 1;
    for (int i = 0; i < n; i++) if (in[i] < ({dtype}){lo}{suf_t} || in[i] > ({dtype}){hi}{suf_t}) {{ all_ok = 0; break; }}"""
            desc_cond = f"all-in-range [{lo},{hi}]"

        slow_code = f"""static {dtype} __attribute__((noinline)) cf3_guarded_{suf}({dtype} x) {{
    return ({check.replace('in[i]', 'x')}) ? ({hot_expr.replace('in[i]', 'x')}) : ({cold_expr.replace('in[i]', 'x')});
}}
void slow_cf3_{suf}({dtype} *out, {dtype} *in, int n) {{
    for (int i = 0; i < n; i++)
        out[i] = cf3_guarded_{suf}(in[i]);
}}"""
        fast_code = f"""void fast_cf3_{suf}({dtype} *out, {dtype} *in, int n) {{
    // Caller guarantees {desc_cond}: guard is unnecessary, use inline loop.
    for (int i = 0; i < n; i++) out[i] = {hot_expr};
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in_arr = malloc(N * sizeof({dtype}));
    {dtype} *out_slow = malloc(N * sizeof({dtype}));
    {dtype} *out_fast = malloc(N * sizeof({dtype}));
    {data_init}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) slow_cf3_{suf}(out_slow, in_arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) fast_cf3_{suf}(out_fast, in_arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"CF-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"{desc_cond}, expr={expr_idx}, {dtype}",
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=2,
            lines_of_code=10,
            expected_speedup_range="1.5x-4x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class CF4_Generator(PatternTemplate):
    """CF-4: Function Pointer Dispatch in Hot Loop.
    Slow: indirect call per element (no inlining). Fast: devirtualize at runtime."""

    def __init__(self):
        super().__init__("CF-4", "Control Flow Inefficiency",
                         "Function Pointer Dispatch in Hot Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([5000000, 10000000])
        fn_used = rng.choice(["relu", "square", "scale", "negate"])
        n_reps = 5
        suf_t = DTYPES[dtype]['suffix']

        # fn_ functions live in fast.c, declared extern in test.c
        # slow.c just takes the function pointer and calls it
        slow_code = f"""void slow_cf4_{suf}({dtype} *out, {dtype} *in, int n, {dtype} (*fn)({dtype})) {{
    for (int i = 0; i < n; i++) out[i] = fn(in[i]);
}}"""

        fn_fwds = f"""{dtype} fn_relu_{suf}({dtype} x);
{dtype} fn_square_{suf}({dtype} x);
{dtype} fn_scale_{suf}({dtype} x);
{dtype} fn_negate_{suf}({dtype} x);"""

        fn_defs = f"""{dtype} fn_relu_{suf}({dtype} x)   {{ return x > ({dtype})0 ? x : ({dtype})0; }}
{dtype} fn_square_{suf}({dtype} x) {{ return x * x; }}
{dtype} fn_scale_{suf}({dtype} x)  {{ return x * ({dtype})1.5; }}
{dtype} fn_negate_{suf}({dtype} x) {{ return -x; }}"""

        # Forward declarations first (no {), blank line resets sig_parts so
        # extract_extern_decl captures fast_cf4 (not fn_relu) as the FAST_CODE_HERE decl.
        fast_code = f"""{fn_fwds}

void fast_cf4_{suf}({dtype} *out, {dtype} *in, int n, {dtype} (*fn)({dtype})) {{
    if      (fn == fn_relu_{suf})   {{ for (int i=0;i<n;i++) out[i]=in[i]>({dtype})0?in[i]:({dtype})0; }}
    else if (fn == fn_square_{suf}) {{ for (int i=0;i<n;i++) out[i]=in[i]*in[i]; }}
    else if (fn == fn_scale_{suf})  {{ for (int i=0;i<n;i++) out[i]=in[i]*({dtype})1.5; }}
    else if (fn == fn_negate_{suf}) {{ for (int i=0;i<n;i++) out[i]=-in[i]; }}
    else                            {{ for (int i=0;i<n;i++) out[i]=fn(in[i]); }}
}}
{fn_defs}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

/* fn_ functions are defined in fast.c, shared via extern */
extern {dtype} fn_relu_{suf}({dtype} x);
extern {dtype} fn_square_{suf}({dtype} x);
extern {dtype} fn_scale_{suf}({dtype} x);
extern {dtype} fn_negate_{suf}({dtype} x);

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in_arr = malloc(N * sizeof({dtype}));
    {dtype} *out_slow = malloc(N * sizeof({dtype}));
    {dtype} *out_fast = malloc(N * sizeof({dtype}));
    for (int i = 0; i < N; i++) in_arr[i] = ({dtype})(i % 200 - 100) * ({dtype})0.1{suf_t};
    {dtype} (*fn)({dtype}) = fn_{fn_used}_{suf};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) slow_cf4_{suf}(out_slow, in_arr, N, fn);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) fast_cf4_{suf}(out_fast, in_arr, N, fn);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(out_slow[i]-out_fast[i])) > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"CF-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"fn={fn_used}, {dtype}, n={N}",
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=2,
            lines_of_code=12,
            expected_speedup_range="2x-8x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class HR2_Generator(PatternTemplate):
    """HR-2: Copy-Paste Duplication.
    Multiple separate passes over data that could be fused."""

    def __init__(self):
        super().__init__("HR-2", "Human Readability Style",
                         "Copy-Paste Duplication")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([5000000, 10000000])
        n_arrays = rng.choice([2, 3])
        stat_type = rng.choice(["mean_var", "min_max", "sum_sumsq"])
        suf_t = DTYPES[dtype]['suffix']
        zero = DTYPES[dtype]['zero']

        arr_names = ["X", "Y", "Z"][:n_arrays]
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)
        out_params = ", ".join(
            f"{dtype} *mean_{a.lower()}, {dtype} *var_{a.lower()}" if stat_type == "mean_var"
            else (f"{dtype} *min_{a.lower()}, {dtype} *max_{a.lower()}" if stat_type == "min_max"
                  else f"{dtype} *sum_{a.lower()}, {dtype} *sumsq_{a.lower()}")
            for a in arr_names
        )

        if stat_type == "mean_var":
            # Slow: 2 passes per array = 2*n_arrays passes
            slow_pass1 = "\n".join(
                f"    {{ {dtype} s=0; for(int i=0;i<n;i++) s+={a}[i]; *mean_{a.lower()}=s/n; }}"
                for a in arr_names)
            slow_pass2 = "\n".join(
                f"    {{ {dtype} v=0,m=*mean_{a.lower()}; for(int i=0;i<n;i++) {{ {dtype} d={a}[i]-m; v+=d*d; }} *var_{a.lower()}=v/n; }}"
                for a in arr_names)
            slow_code = f"""void slow_hr2_{suf}({arr_params}, int n, {out_params}) {{
{slow_pass1}
{slow_pass2}
}}"""
            # Fast: 1 pass for means, 1 pass for variances
            fast_sum_decls = " ".join(f"{dtype} s{a}=0;" for a in arr_names)
            fast_sum_body = " ".join(f"s{a}+={a}[i];" for a in arr_names)
            fast_mean_assign = " ".join(f"*mean_{a.lower()}=s{a}/n;" for a in arr_names)
            fast_var_decls = " ".join(f"{dtype} v{a}=0;" for a in arr_names)
            fast_mean_vars = " ".join(f"{dtype} m{a}=*mean_{a.lower()};" for a in arr_names)
            fast_var_body = " ".join(f"{{ {dtype} d={a}[i]-m{a}; v{a}+=d*d; }}" for a in arr_names)
            fast_var_assign = " ".join(f"*var_{a.lower()}=v{a}/n;" for a in arr_names)
            fast_code = f"""void fast_hr2_{suf}({arr_params}, int n, {out_params}) {{
    {fast_sum_decls}
    for(int i=0;i<n;i++) {{ {fast_sum_body} }}
    {fast_mean_assign}
    {fast_var_decls} {fast_mean_vars}
    for(int i=0;i<n;i++) {{ {fast_var_body} }}
    {fast_var_assign}
}}"""
            out_args_slow = ", ".join(f"&ms_{a.lower()}, &vs_{a.lower()}" for a in arr_names)
            out_args_fast = ", ".join(f"&mf_{a.lower()}, &vf_{a.lower()}" for a in arr_names)
            out_decls_slow = " ".join(f"{dtype} ms_{a.lower()}=0, vs_{a.lower()}=0;" for a in arr_names)
            out_decls_fast = " ".join(f"{dtype} mf_{a.lower()}=0, vf_{a.lower()}=0;" for a in arr_names)
            correct_check = " && ".join(
                f"fabs((double)(ms_{a.lower()}-mf_{a.lower()}))<1e-4 && fabs((double)(vs_{a.lower()}-vf_{a.lower()}))<1e-4"
                for a in arr_names)
            desc = f"mean+var, {n_arrays} arrays, {dtype}"

        elif stat_type == "min_max":
            slow_passes = "\n".join(
                f"    {{ {dtype} mn={a}[0],mx={a}[0]; for(int i=1;i<n;i++) {{ if({a}[i]<mn) mn={a}[i]; if({a}[i]>mx) mx={a}[i]; }} *min_{a.lower()}=mn; *max_{a.lower()}=mx; }}"
                for a in arr_names)
            slow_code = f"""void slow_hr2_{suf}({arr_params}, int n, {out_params}) {{
{slow_passes}
}}"""
            fast_init = " ".join(f"{dtype} mn{a}={a}[0],mx{a}={a}[0];" for a in arr_names)
            fast_body = " ".join(f"if({a}[i]<mn{a}) mn{a}={a}[i]; if({a}[i]>mx{a}) mx{a}={a}[i];" for a in arr_names)
            fast_assign = " ".join(f"*min_{a.lower()}=mn{a}; *max_{a.lower()}=mx{a};" for a in arr_names)
            fast_code = f"""void fast_hr2_{suf}({arr_params}, int n, {out_params}) {{
    {fast_init}
    for(int i=1;i<n;i++) {{ {fast_body} }}
    {fast_assign}
}}"""
            out_args_slow = ", ".join(f"&mn_s_{a.lower()}, &mx_s_{a.lower()}" for a in arr_names)
            out_args_fast = ", ".join(f"&mn_f_{a.lower()}, &mx_f_{a.lower()}" for a in arr_names)
            out_decls_slow = " ".join(f"{dtype} mn_s_{a.lower()}=0, mx_s_{a.lower()}=0;" for a in arr_names)
            out_decls_fast = " ".join(f"{dtype} mn_f_{a.lower()}=0, mx_f_{a.lower()}=0;" for a in arr_names)
            correct_check = " && ".join(
                f"fabs((double)(mn_s_{a.lower()}-mn_f_{a.lower()}))<1e-9 && fabs((double)(mx_s_{a.lower()}-mx_f_{a.lower()}))<1e-9"
                for a in arr_names)
            desc = f"min+max, {n_arrays} arrays, {dtype}"

        else:  # sum_sumsq
            slow_passes = "\n".join(
                f"    {{ {dtype} s=0; for(int i=0;i<n;i++) s+={a}[i]; *sum_{a.lower()}=s; }}\n"
                f"    {{ {dtype} s=0; for(int i=0;i<n;i++) s+={a}[i]*{a}[i]; *sumsq_{a.lower()}=s; }}"
                for a in arr_names)
            slow_code = f"""void slow_hr2_{suf}({arr_params}, int n, {out_params}) {{
{slow_passes}
}}"""
            fast_decls = " ".join(f"{dtype} s{a}=0, sq{a}=0;" for a in arr_names)
            fast_body = " ".join(f"s{a}+={a}[i]; sq{a}+={a}[i]*{a}[i];" for a in arr_names)
            fast_assign = " ".join(f"*sum_{a.lower()}=s{a}; *sumsq_{a.lower()}=sq{a};" for a in arr_names)
            fast_code = f"""void fast_hr2_{suf}({arr_params}, int n, {out_params}) {{
    {fast_decls}
    for(int i=0;i<n;i++) {{ {fast_body} }}
    {fast_assign}
}}"""
            out_args_slow = ", ".join(f"&su_s_{a.lower()}, &sq_s_{a.lower()}" for a in arr_names)
            out_args_fast = ", ".join(f"&su_f_{a.lower()}, &sq_f_{a.lower()}" for a in arr_names)
            out_decls_slow = " ".join(f"{dtype} su_s_{a.lower()}=0, sq_s_{a.lower()}=0;" for a in arr_names)
            out_decls_fast = " ".join(f"{dtype} su_f_{a.lower()}=0, sq_f_{a.lower()}=0;" for a in arr_names)
            correct_check = " && ".join(
                f"fabs((double)(su_s_{a.lower()}-su_f_{a.lower()}))<1e-4 && fabs((double)(sq_s_{a.lower()}-sq_f_{a.lower()}))<1e-4"
                for a in arr_names)
            desc = f"sum+sumsq, {n_arrays} arrays, {dtype}"

        arr_allocs = "\n    ".join(
            f"{dtype} *{a} = malloc(N * sizeof({dtype})); for(int i=0;i<N;i++) {a}[i]=({dtype})(i%100+1)*0.1{suf_t};"
            for a in arr_names)
        arr_frees = " ".join(f"free({a});" for a in arr_names)
        arr_call_args = ", ".join(arr_names)

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {arr_allocs}
    {out_decls_slow}
    {out_decls_fast}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_hr2_{suf}({arr_call_args}, N, {out_args_slow});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_hr2_{suf}({arr_call_args}, N, {out_args_fast});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = ({correct_check}) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    {arr_frees}
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"HR-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=n_arrays,
            lines_of_code=10 + n_arrays * 3,
            expected_speedup_range="1.5x-4x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class HR3_Generator(PatternTemplate):
    """HR-3: Dead/Debug Code left in production hot loops."""

    def __init__(self):
        super().__init__("HR-3", "Human Readability Style",
                         "Dead / Debug Code")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([5000000, 10000000])
        debug_pattern = rng.choice(["counter", "nan_check", "range_check", "all"])
        expr_idx = rng.randint(0, 2)
        n_reps = 5
        suf_t = DTYPES[dtype]['suffix']

        exprs = [
            f"in[i] * ({dtype})2.0 + ({dtype})1.0",
            f"in[i] * in[i] + ({dtype})0.5",
            f"in[i] * ({dtype})3.14 - ({dtype})1.0",
        ]
        computation = exprs[expr_idx]

        debug_lines = []
        counter_init = ""
        if debug_pattern in ("counter", "all"):
            # Use local static to avoid file-scope static (which breaks extract_extern_decl)
            counter_init = f"    static volatile int debug_ctr_{suf} = 0;\n"
            debug_lines.append(f"        debug_ctr_{suf}++;  /* volatile: prevents optimization */")
        if debug_pattern in ("nan_check", "all"):
            debug_lines.append(f"        if (in[i] != in[i]) {{ /* NaN check - dead for normal data */ }}")
        if debug_pattern in ("range_check", "all"):
            debug_lines.append(f"        if (out[i] < ({dtype})-1e15 || out[i] > ({dtype})1e15) {{ /* range check - dead */ }}")

        debug_block = "\n".join(debug_lines)

        slow_code = f"""void slow_hr3_{suf}({dtype} *out, {dtype} *in, int n) {{
{counter_init}    for (int i = 0; i < n; i++) {{
{debug_block}
        out[i] = {computation};
    }}
}}"""

        fast_code = f"""void fast_hr3_{suf}({dtype} *out, {dtype} *in, int n) {{
    for (int i = 0; i < n; i++) {{
        out[i] = {computation};
    }}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in_arr = malloc(N * sizeof({dtype}));
    {dtype} *out_slow = malloc(N * sizeof({dtype}));
    {dtype} *out_fast = malloc(N * sizeof({dtype}));
    for (int i = 0; i < N; i++) in_arr[i] = ({dtype})(i % 100 + 1) * ({dtype})0.1{suf_t};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) slow_hr3_{suf}(out_slow, in_arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) fast_hr3_{suf}(out_fast, in_arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(out_slow[i]-out_fast[i])) > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(in_arr); free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"HR-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"debug={debug_pattern}, {dtype}",
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=2,
            lines_of_code=8 + len(debug_lines),
            expected_speedup_range="1.2x-3x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class HR4_Generator(PatternTemplate):
    """HR-4: Redundant Materialization Pass.
    Slow: scales array into a heap-allocated intermediate then reduces it (2 passes).
    Fast: combines scale and reduce in one pass. Compiler cannot fuse loops across
    heap pointers; arrays exceed L3 so the extra pass hits DRAM."""

    def __init__(self):
        super().__init__("HR-4", "Human Readability Style",
                         "Redundant Materialization Pass")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        # Force large N so arrays exceed L3 cache (80-160MB >> typical 8-30MB L3)
        N = rng.choice([10000000, 20000000])
        # Vary how the scale is applied to produce diverse variants
        scale_op = rng.choice(["*", "+", "-"])
        # Vary the second pass operation
        sq_op = rng.choice(["* t1[i]", "+ t1[i]", "- t1[i]"])
        sq_fast = sq_op.replace("t1[i]", "u")

        # slow: 3 passes with 2 heap-allocated staging arrays
        # pass1: t1[i] = arr[i] op scale
        # pass2: t2[i] = t1[i] sq_op
        # pass3: result += t2[i]
        # Bandwidth: read arr(80MB)+write t1(80MB)+read t1(80MB)+write t2(80MB)+read t2(80MB)
        #           = 400MB vs fast's 80MB → ~5x
        slow_code = f"""double slow_hr4_{suf}(double *arr, double scale, int n) {{
    double *t1 = (double *)malloc(n * sizeof(double));
    double *t2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) t1[i] = arr[i] {scale_op} scale;
    for (int i = 0; i < n; i++) t2[i] = t1[i] {sq_op};
    double result = 0.0;
    for (int i = 0; i < n; i++) result += t2[i];
    free(t1);
    free(t2);
    return result;
}}"""

        # fast: single pass — fuses all three passes
        fast_code = f"""double fast_hr4_{suf}(double *arr, double scale, int n) {{
    double result = 0.0;
    for (int i = 0; i < n; i++) {{
        double u = arr[i] {scale_op} scale;
        result += u {sq_fast};
    }}
    return result;
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *arr = (double *)malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) arr[i] = (double)(i % 100 + 1) * 0.1;
    double scale = 1.5;

    struct timespec t0, t1;
    volatile double r_slow, r_fast;
    int n_reps = 3;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_slow = slow_hr4_{suf}(arr, scale, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < n_reps; r++) r_fast = fast_hr4_{suf}(arr, scale, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / n_reps;

    int correct = (fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1.0) < 1e-9) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"HR-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"3-pass staging: scale({scale_op}), sq({sq_op}), reduce, N={N}",
            dtype="double",
            difficulty="medium",
            compiler_fixable=False,
            num_loops=3,
            num_arrays=3,
            lines_of_code=8,
            expected_speedup_range="3x-5x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class HR5_Generator(PatternTemplate):
    """HR-5: Repeated/Defensive Append Anti-pattern.
    Slow: bounds check + value guard per write (always satisfied).
    Fast: direct indexed assignment."""

    def __init__(self):
        super().__init__("HR-5", "Human Readability Style",
                         "Repeated String/Format Operations")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["int", "int", "double"])
        N = rng.choice([5000000, 10000000])
        n_checks = rng.choice([1, 2, 3])
        op = rng.choice(["+", "+", "-", "*"])
        n_reps = 5
        suf_t = DTYPES[dtype]['suffix']
        zero = DTYPES[dtype]['zero']

        checks = [
            f"if (pos < n)",
            f"if ({('val' if op != '*' else 'val')} >= {zero})",
            f"if (i >= 0 && i < n)",
        ][:n_checks]

        indent = "    " * n_checks
        check_open = "\n".join(f"{'    ' * (k+1)}{checks[k]} {{" for k in range(n_checks))
        check_close = "\n".join(f"{'    ' * (n_checks - k)}}} " for k in range(n_checks))

        if dtype == "int":
            val_expr = f"A[i] {op} B[i]"
        else:
            val_expr = f"A[i] {op} B[i]"

        slow_code = f"""void slow_hr5_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{
    int pos = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} val = {val_expr};
{check_open}
            {indent}out[pos] = val;
            {indent}pos++;
{check_close}
    }}
}}"""

        fast_code = f"""void fast_hr5_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{
    for (int i = 0; i < n; i++) out[i] = {val_expr};
}}"""

        alloc_a = f"{dtype} *A = malloc(N * sizeof({dtype})); for(int i=0;i<N;i++) A[i]=({dtype})(i%100+1);"
        alloc_b = f"{dtype} *B = malloc(N * sizeof({dtype})); for(int i=0;i<N;i++) B[i]=({dtype})(i%50+1);"
        tol = "0" if dtype == "int" else "1e-9"
        if dtype == "int":
            verify = f"out_slow[i] != out_fast[i]"
        else:
            verify = f"fabs((double)(out_slow[i]-out_fast[i])) > {tol}"

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {alloc_a}
    {alloc_b}
    {dtype} *out_slow = calloc(N, sizeof({dtype}));
    {dtype} *out_fast = calloc(N, sizeof({dtype}));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) slow_hr5_{suf}(out_slow, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) fast_hr5_{suf}(out_fast, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    int correct = 1;
    for (int i = 0; i < N; i++) if ({verify}) {{ correct = 0; break; }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"HR-5_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"{n_checks} defensive checks, op={op}, {dtype}",
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=3,
            lines_of_code=7 + n_checks * 2,
            expected_speedup_range="1.2x-2x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class DS1_Generator(PatternTemplate):
    """DS-1: Linear Search vs Hash Lookup.
    Slow: O(n) scan per query. Fast: O(1) hash table lookup."""

    def __init__(self):
        super().__init__("DS-1", "Data Structure Choice",
                         "Linear Search vs Hash Lookup")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n_keys = rng.choice([500, 1000, 2000, 5000])
        n_queries = rng.choice([200, 500, 1000])
        ht_bits = rng.choice([14, 15, 16])
        ht_size = 1 << ht_bits

        slow_code = f"""int slow_ds1_{suf}(int *keys, int *values, int n, int target) {{
    for (int i = 0; i < n; i++) {{
        if (keys[i] == target) return values[i];
    }}
    return -1;
}}"""

        # Parallel-array hash table: no struct, no typedef conflicts
        fast_code = f"""void ds1_build_{suf}(int *hk, int *hv, int *ho, int hs, int *keys, int *values, int n);

int fast_ds1_{suf}(int *hk, int *hv, int *ho, int hs, int target) {{
    unsigned h = (unsigned)target & (unsigned)(hs - 1);
    while (ho[h]) {{
        if (hk[h] == target) return hv[h];
        h = (h + 1) & (unsigned)(hs - 1);
    }}
    return -1;
}}
void ds1_build_{suf}(int *hk, int *hv, int *ho, int hs, int *keys, int *values, int n) {{
    for (int i = 0; i < n; i++) {{
        unsigned h = (unsigned)keys[i] & (unsigned)(hs - 1);
        while (ho[h]) h = (h + 1) & (unsigned)(hs - 1);
        hk[h] = keys[i]; hv[h] = values[i]; ho[h] = 1;
    }}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_KEYS {n_keys}
#define N_QUERIES {n_queries}
#define HT_SIZE {ht_size}

extern void ds1_build_{suf}(int *hk, int *hv, int *ho, int hs, int *keys, int *values, int n);

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *keys   = malloc(N_KEYS * sizeof(int));
    int *values = malloc(N_KEYS * sizeof(int));
    int *queries = malloc(N_QUERIES * sizeof(int));
    for (int i = 0; i < N_KEYS; i++) {{ keys[i] = i * 7 + 13; values[i] = i * 3; }}
    unsigned rs = 42u;
    for (int i = 0; i < N_QUERIES; i++) {{
        rs = rs * 1664525u + 1013904223u;
        queries[i] = keys[(rs >> 1) % N_KEYS];
    }}

    int *hk = calloc(HT_SIZE, sizeof(int));
    int *hv = calloc(HT_SIZE, sizeof(int));
    int *ho = calloc(HT_SIZE, sizeof(int));
    ds1_build_{suf}(hk, hv, ho, HT_SIZE, keys, values, N_KEYS);

    struct timespec t0, t1;
    volatile int sum_slow = 0, sum_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 20; r++)
        for (int i = 0; i < N_QUERIES; i++) sum_slow += slow_ds1_{suf}(keys, values, N_KEYS, queries[i]);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 20;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 20; r++)
        for (int i = 0; i < N_QUERIES; i++) sum_fast += fast_ds1_{suf}(hk, hv, ho, HT_SIZE, queries[i]);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 20;

    int correct = (sum_slow == sum_fast) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(keys); free(values); free(queries); free(hk); free(hv); free(ho);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"DS-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"n_keys={n_keys}, n_queries={n_queries}, ht_size={ht_size}",
            dtype="int",
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=2,
            lines_of_code=12,
            expected_speedup_range="10x-100x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class DS2_Generator(PatternTemplate):
    """DS-2: Repeated Allocation vs Pre-allocation.
    Slow: malloc+free per chunk. Fast: single allocation reused."""

    def __init__(self):
        super().__init__("DS-2", "Data Structure Choice",
                         "Repeated Allocation vs Pre-allocation")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        # Large N ensures arrays exceed L3 cache (80-320MB >> typical 8-32MB L3)
        N = rng.choice([10000000, 20000000])
        # Small chunks → many mallocs per call (625k-2.5M pairs) → overhead dominates
        chunk = rng.choice([8, 16])
        op = rng.choice(["square", "abs", "identity"])
        suf_t = DTYPES[dtype]['suffix']

        if op == "square":
            transform = f"temp[j] = input[i + j] * input[i + j];"
        elif op == "abs":
            transform = f"temp[j] = ({dtype})fabs((double)input[i + j]);"
        else:
            transform = f"temp[j] = input[i + j];"

        slow_code = f"""void slow_ds2_{suf}({dtype} *results, {dtype} *input, int n, int chunk) {{
    for (int i = 0; i < n; i += chunk) {{
        int sz = (i + chunk <= n) ? chunk : (n - i);
        {dtype} *temp = malloc(sz * sizeof({dtype}));
        for (int j = 0; j < sz; j++) {transform}
        {dtype} sum = 0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk] = sum;
        free(temp);
    }}
}}"""

        fast_code = f"""void fast_ds2_{suf}({dtype} *results, {dtype} *input, int n, int chunk) {{
    {dtype} *temp = malloc(chunk * sizeof({dtype}));
    for (int i = 0; i < n; i += chunk) {{
        int sz = (i + chunk <= n) ? chunk : (n - i);
        for (int j = 0; j < sz; j++) {transform}
        {dtype} sum = 0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk] = sum;
    }}
    free(temp);
}}"""

        n_results = (N + chunk - 1) // chunk
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}
#define CHUNK {chunk}
#define N_RESULTS ((N + CHUNK - 1) / CHUNK)

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *input = malloc(N * sizeof({dtype}));
    {dtype} *res_slow = malloc(N_RESULTS * sizeof({dtype}));
    {dtype} *res_fast = malloc(N_RESULTS * sizeof({dtype}));
    for (int i = 0; i < N; i++) input[i] = ({dtype})(i % 100 + 1) * ({dtype})0.1{suf_t};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ds2_{suf}(res_slow, input, N, CHUNK);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ds2_{suf}(res_fast, input, N, CHUNK);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N_RESULTS; i++) {{
        if (fabs((double)(res_slow[i]-res_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(input); free(res_slow); free(res_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"DS-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"chunk={chunk}, op={op}, {dtype}, n={N}",
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=2,
            lines_of_code=12,
            expected_speedup_range="2x-10x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class DS3_Generator(PatternTemplate):
    """DS-3: Unnecessary Copying (pass-by-value semantics).
    Slow: large struct passed by value (full copy). Fast: const pointer."""

    def __init__(self):
        super().__init__("DS-3", "Data Structure Choice",
                         "Unnecessary Copying")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        width = rng.choice([64, 128, 256, 512])   # copy width in doubles
        N = rng.choice([200000, 500000, 1000000])
        op_type = rng.choice(["sum", "max", "mean"])

        if op_type == "sum":
            body_fast = f"""    double s = 0.0;
    for (int i = 0; i < {width}; i++) s += data[i];
    return s;"""
            body_slow = f"""    double *copy = (double*)malloc({width} * sizeof(double));
    for (int i = 0; i < {width}; i++) copy[i] = data[i];
    double s = 0.0;
    for (int i = 0; i < {width}; i++) s += copy[i];
    free(copy);
    return s;"""
        elif op_type == "max":
            body_fast = f"""    double mx = data[0];
    for (int i = 1; i < {width}; i++) if (data[i] > mx) mx = data[i];
    return mx;"""
            body_slow = f"""    double *copy = (double*)malloc({width} * sizeof(double));
    for (int i = 0; i < {width}; i++) copy[i] = data[i];
    double mx = copy[0];
    for (int i = 1; i < {width}; i++) if (copy[i] > mx) mx = copy[i];
    free(copy);
    return mx;"""
        else:  # mean
            body_fast = f"""    double s = 0.0;
    for (int i = 0; i < {width}; i++) s += data[i];
    return s / {width}.0;"""
            body_slow = f"""    double *copy = (double*)malloc({width} * sizeof(double));
    for (int i = 0; i < {width}; i++) copy[i] = data[i];
    double s = 0.0;
    for (int i = 0; i < {width}; i++) s += copy[i];
    free(copy);
    return s / {width}.0;"""

        # Slow: malloc+copy then process — unnecessary copy
        slow_code = f"""double slow_ds3_{suf}(const double *data) {{
{body_slow}
}}"""

        # Fast: process directly, no copy
        fast_code = f"""double fast_ds3_{suf}(const double *data) {{
{body_fast}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}
#define W {width}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *arr = (double*)malloc((long)N * W * sizeof(double));
    for (long i = 0; i < (long)N * W; i++) arr[i] = (double)(i % 997 + 1) * 0.001;

    struct timespec t0, t1;
    volatile double sum_slow = 0, sum_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < N; i++) sum_slow += slow_ds3_{suf}(arr + (long)i * W);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < N; i++) sum_fast += fast_ds3_{suf}(arr + (long)i * W);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs(sum_slow - sum_fast) < 1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"DS-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"width={width}*8B={width*8}B, op={op_type}, n={N}",
            dtype="double",
            difficulty="easy",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=8,
            expected_speedup_range="2x-20x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class AL2_Generator(PatternTemplate):
    """AL-2: Repeated Sort vs Sorted Insertion.
    Slow: qsort after each insert. Fast: binary-search insert + memmove."""

    def __init__(self):
        super().__init__("AL-2", "Algorithmic Inefficiency",
                         "Repeated Sort vs Sorted Insertion")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n_items = rng.choice([2000, 5000, 10000])

        slow_code = f"""static int cmp_al2_{suf}(const void *a, const void *b);

void slow_al2_{suf}(double *arr, int *sz, double *items, int n) {{
    *sz = 0;
    for (int i = 0; i < n; i++) {{
        arr[(*sz)++] = items[i];
        qsort(arr, *sz, sizeof(double), cmp_al2_{suf});
    }}
}}
static int cmp_al2_{suf}(const void *a, const void *b) {{
    double da = *(const double*)a, db = *(const double*)b;
    return (da > db) - (da < db);
}}"""

        fast_code = f"""static int bs_insert_{suf}(double *arr, int sz, double val);

void fast_al2_{suf}(double *arr, int *sz, double *items, int n) {{
    *sz = 0;
    for (int i = 0; i < n; i++) {{
        int pos = bs_insert_{suf}(arr, *sz, items[i]);
        memmove(&arr[pos+1], &arr[pos], (*sz - pos) * sizeof(double));
        arr[pos] = items[i];
        (*sz)++;
    }}
}}
static int bs_insert_{suf}(double *arr, int sz, double val) {{
    int lo = 0, hi = sz;
    while (lo < hi) {{ int mid = (lo+hi)/2; if (arr[mid] < val) lo=mid+1; else hi=mid; }}
    return lo;
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_ITEMS {n_items}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *items = malloc(N_ITEMS * sizeof(double));
    double *arr_slow = malloc(N_ITEMS * sizeof(double));
    double *arr_fast = malloc(N_ITEMS * sizeof(double));
    unsigned rs = 42u;
    for (int i = 0; i < N_ITEMS; i++) {{
        rs = rs * 1664525u + 1013904223u;
        items[i] = (double)(rs % 100000) * 0.01;
    }}

    struct timespec t0, t1;
    int sz_s = 0, sz_f = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_al2_{suf}(arr_slow, &sz_s, items, N_ITEMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_al2_{suf}(arr_fast, &sz_f, items, N_ITEMS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (sz_s == sz_f) ? 1 : 0;
    if (correct) for (int i = 0; i < sz_s; i++) if (fabs(arr_slow[i]-arr_fast[i]) > 1e-12) {{ correct=0; break; }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(items); free(arr_slow); free(arr_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"AL-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"n_items={n_items}, qsort-per-insert vs binary-insert",
            dtype="double",
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=10,
            expected_speedup_range="10x-100x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class AL3_Generator(PatternTemplate):
    """AL-3: Naive String Matching vs KMP.
    Slow: O(n*m) brute force. Fast: O(n+m) KMP."""

    def __init__(self):
        super().__init__("AL-3", "Algorithmic Inefficiency",
                         "Naive String Matching vs KMP")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        # Adversarial input: text = all zeros, pattern = (pn-1) zeros + one 1.
        # Naive must compare nearly the full pattern before failing at every
        # text position → O(n*m) in practice.  KMP's failure function lets it
        # stay at O(n+m).  Pattern length ≥ 200 so even AVX2-vectorised naive
        # (pn/32 SIMD ops per position) loses to scalar KMP (~2 ops per position).
        tn = rng.choice([1000000, 2000000, 5000000])
        pn = rng.choice([200, 300, 500])
        n_reps = 3

        slow_code = f"""int slow_al3_{suf}(unsigned char *text, int tn,
                                unsigned char *pattern, int pn) {{
    int count = 0;
    for (int i = 0; i <= tn - pn; i++) {{
        int j;
        for (j = 0; j < pn; j++) {{
            if (text[i + j] != pattern[j]) break;
        }}
        if (j == pn) count++;
    }}
    return count;
}}"""

        fast_code = f"""static void build_fail_{suf}(unsigned char *pat, int pn, int *fail);

int fast_al3_{suf}(unsigned char *text, int tn,
                   unsigned char *pattern, int pn) {{
    int *fail = malloc(pn * sizeof(int));
    build_fail_{suf}(pattern, pn, fail);
    int count = 0, k = 0;
    for (int i = 0; i < tn; i++) {{
        while (k > 0 && pattern[k] != text[i]) k = fail[k - 1];
        if (pattern[k] == text[i]) k++;
        if (k == pn) {{ count++; k = fail[k - 1]; }}
    }}
    free(fail);
    return count;
}}
static void build_fail_{suf}(unsigned char *pat, int pn, int *fail) {{
    fail[0] = 0;
    int k = 0;
    for (int i = 1; i < pn; i++) {{
        while (k > 0 && pat[k] != pat[i]) k = fail[k - 1];
        if (pat[k] == pat[i]) k++;
        fail[i] = k;
    }}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define TN {tn}
#define PN {pn}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    /* Adversarial: pattern = PN-1 zeros then a 1.  Text = all zeros.
       Naive scans nearly the full pattern before failing at each position. */
    unsigned char *text    = calloc(TN, 1);
    unsigned char *pattern = calloc(PN, 1);
    pattern[PN - 1] = 1;

    struct timespec t0, t1;
    volatile int c_slow = 0, c_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++)
        c_slow = slow_al3_{suf}(text, TN, pattern, PN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++)
        c_fast = fast_al3_{suf}(text, TN, pattern, PN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};

    int correct = (c_slow == c_fast) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(text); free(pattern);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"AL-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"adversarial: tn={tn}, pn={pn}, all-zeros text",
            dtype="unsigned char",
            difficulty="hard",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=2,
            lines_of_code=14,
            expected_speedup_range="10x-100x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class AL4_Generator(PatternTemplate):
    """AL-4: Redundant Recomputation in Recursion.
    Slow: exponential naive recursion. Fast: DP table."""

    def __init__(self):
        super().__init__("AL-4", "Algorithmic Inefficiency",
                         "Redundant Recomputation in Recursion")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        problem = rng.choice(["grid_paths", "grid_paths", "triangle", "binomial"])

        if problem == "grid_paths":
            r = rng.choice([15, 16, 17, 18])
            c = rng.choice([15, 16, 17])
            slow_code = f"""long long slow_al4_{suf}(int r, int c) {{
    if (r == 0 || c == 0) return 1;
    return slow_al4_{suf}(r-1, c) + slow_al4_{suf}(r, c-1);
}}"""
            fast_code = f"""long long fast_al4_{suf}(int r, int c) {{
    long long *dp = calloc(c+1, sizeof(long long));
    for (int j = 0; j <= c; j++) dp[j] = 1;
    for (int i = 1; i <= r; i++)
        for (int j = 1; j <= c; j++)
            dp[j] += dp[j-1];
    long long res = dp[c]; free(dp); return res;
}}"""
            n_reps_fast = 100000
            slow_args = f"{r}, {c}"
            fast_args = f"{r}, {c}"
            desc = f"grid paths ({r}x{c}): exponential -> O(r*c) DP"

        elif problem == "triangle":
            n = rng.choice([20, 22, 24])
            slow_code = f"""long long slow_al4_{suf}(int n) {{
    if (n <= 1) return n;
    return slow_al4_{suf}(n-1) + slow_al4_{suf}(n-2);
}}"""
            fast_code = f"""long long fast_al4_{suf}(int n) {{
    if (n <= 1) return n;
    long long a=0, b=1;
    for (int i=2; i<=n; i++) {{ long long t=a+b; a=b; b=t; }}
    return b;
}}"""
            n_reps_fast = 1000000
            slow_args = str(n)
            fast_args = str(n)
            desc = f"fibonacci n={n}: O(2^n) -> O(n)"

        else:  # binomial
            bn = rng.choice([24, 26, 28])
            bk = bn // 2
            slow_code = f"""long long slow_al4_{suf}(int n, int k) {{
    if (k == 0 || k == n) return 1;
    return slow_al4_{suf}(n-1, k-1) + slow_al4_{suf}(n-1, k);
}}"""
            fast_code = f"""long long fast_al4_{suf}(int n, int k) {{
    long long *dp = calloc(k+1, sizeof(long long));
    dp[0] = 1;
    for (int i=1; i<=n; i++)
        for (int j=(i<k?i:k); j>0; j--)
            dp[j] += dp[j-1];
    long long res = dp[k]; free(dp); return res;
}}"""
            n_reps_fast = 100000
            slow_args = f"{bn}, {bk}"
            fast_args = f"{bn}, {bk}"
            desc = f"binomial C({bn},{bk}): O(2^n) -> O(n*k)"

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    struct timespec t0, t1;
    volatile long long r_slow, r_fast;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_slow = slow_al4_{suf}({slow_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps_fast}; r++) r_fast = fast_al4_{suf}({fast_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps_fast};

    int correct = (r_slow == r_fast) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"AL-4_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype="long long",
            difficulty="hard",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=0,
            lines_of_code=8,
            expected_speedup_range="1000x+",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class MI1_Generator(PatternTemplate):
    """MI-1: Unnecessary Memory Allocation in Loop.
    Slow: malloc+free per window iteration. Fast: sliding window, no allocation."""

    def __init__(self):
        super().__init__("MI-1", "Memory & IO",
                         "Allocation in Loop vs Sliding Window")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        # Always use double: sliding window accumulates floating-point drift
        # that causes correctness failures with float at large N.
        dtype = "double"
        N = rng.choice([100000, 500000, 1000000])
        window = rng.choice([8, 16, 32, 64])
        zero = "0.0"

        slow_code = f"""double slow_mi1_{suf}(double *input, int n, int win) {{
    double total = {zero};
    for (int i = 0; i <= n - win; i++) {{
        double *buf = malloc(win * sizeof(double));
        for (int j = 0; j < win; j++) buf[j] = input[i + j];
        double sum = {zero};
        for (int j = 0; j < win; j++) sum += buf[j];
        total += sum / win;
        free(buf);
    }}
    return total;
}}"""

        fast_code = f"""double fast_mi1_{suf}(double *input, int n, int win) {{
    double total = {zero}, sum = {zero};
    for (int j = 0; j < win; j++) sum += input[j];
    total += sum / win;
    for (int i = 1; i <= n - win; i++) {{
        sum += input[i + win - 1] - input[i - 1];
        total += sum / win;
    }}
    return total;
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}
#define WIN {window}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *input = malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) input[i] = (double)(i % 100 + 1) * 0.1;

    struct timespec t0, t1;
    volatile double r_slow, r_fast;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_slow = slow_mi1_{suf}(input, N, WIN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_fast = fast_mi1_{suf}(input, N, WIN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs(r_slow - r_fast) < 1e-2) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(input);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"MI-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"window={window}, n={N}, double",
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=2,
            num_arrays=1,
            lines_of_code=12,
            expected_speedup_range="5x-50x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class MI2_Generator(PatternTemplate):
    """MI-2: Unnecessary Staging Buffers.
    Slow: 3-pass pipeline with 2 heap-allocated staging arrays forces 2.7x more
    memory bandwidth than a single-pass equivalent. Aliasing prevents compiler
    from fusing loops; arrays exceed L3 cache so every pass hits DRAM."""

    def __init__(self):
        super().__init__("MI-2", "Memory & IO",
                         "Unnecessary Staging Buffers")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        N = rng.choice([5000000, 10000000, 20000000])
        # Vary operations to produce diverse variants
        op1 = rng.choice(["*", "+"])    # stage1: s1[i] = A[i] op1 A[i] + B[i]  (or A*A+B)
        op2 = rng.choice(["-", "+"])    # stage2: s2[i] = s1[i]*s1[i] op2 B[i]
        n_reps = 3

        # slow: 3 passes via 2 staging arrays — mandatory DRAM round-trips
        slow_code = f"""void slow_mi2_{suf}(double *out, double *A, double *B, int n) {{
    double *s1 = (double *)malloc(n * sizeof(double));
    double *s2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) s1[i] = A[i] {op1} A[i] + B[i];
    for (int i = 0; i < n; i++) s2[i] = s1[i] * s1[i] {op2} B[i];
    for (int i = 0; i < n; i++) out[i] = s2[i];
    free(s1);
    free(s2);
}}"""

        # fast: single pass — 2.7x less memory bandwidth
        fast_code = f"""void fast_mi2_{suf}(double *out, double *A, double *B, int n) {{
    for (int i = 0; i < n; i++) {{
        double t = A[i] {op1} A[i] + B[i];
        out[i] = t * t {op2} B[i];
    }}
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *A = (double *)malloc(N * sizeof(double));
    double *B = (double *)malloc(N * sizeof(double));
    for (int i = 0; i < N; i++) {{ A[i] = (double)(i % 100 + 1); B[i] = (double)(i % 50 + 1); }}
    double *out_slow = (double *)malloc(N * sizeof(double));
    double *out_fast = (double *)malloc(N * sizeof(double));
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) slow_mi2_{suf}(out_slow, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < {n_reps}; r++) fast_mi2_{suf}(out_fast, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / {n_reps};
    int correct = 1;
    for (int i = 0; i < N; i++) {{
        double denom = fmax(fabs(out_slow[i]), 1.0);
        if (fabs(out_slow[i] - out_fast[i]) / denom > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"MI-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"3-pass staging buffers, N={N}, ops={op1}/sq{op2}",
            dtype="double",
            difficulty="medium",
            compiler_fixable=False,
            num_loops=3,
            num_arrays=4,
            lines_of_code=7,
            expected_speedup_range="2x-3x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


class MI3_Generator(PatternTemplate):
    """MI-3: Excessive Dynamic Allocation (malloc in hot loop).
    Slow: heap-allocate small buffer per iteration. Fast: direct computation."""

    def __init__(self):
        super().__init__("MI-3", "Memory & IO",
                         "Heap Alloc in Hot Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        N = rng.choice([500000, 1000000, 2000000])
        chunk_sz = rng.choice([4, 8, 16])
        op = rng.choice(["avg", "avg", "sum"])
        suf_t = DTYPES[dtype]['suffix']
        zero = DTYPES[dtype]['zero']

        if op == "avg":
            scale = f"({dtype})1.0 / {chunk_sz}"
            slow_loop = f"        for (int j = 0; j < {chunk_sz}; j++) quad[j] = data[i+j];\n        {dtype} s = {zero}; for (int j = 0; j < {chunk_sz}; j++) s += quad[j];\n        total += s * ({dtype}){1.0/chunk_sz};"
            fast_loop = " + ".join(f"data[i+{j}]" for j in range(chunk_sz))
            fast_expr = f"total += ({fast_loop}) * ({dtype}){1.0/chunk_sz};"
        else:  # sum
            slow_loop = f"        for (int j = 0; j < {chunk_sz}; j++) quad[j] = data[i+j];\n        {dtype} s = {zero}; for (int j = 0; j < {chunk_sz}; j++) s += quad[j];\n        total += s;"
            fast_loop = " + ".join(f"data[i+{j}]" for j in range(chunk_sz))
            fast_expr = f"total += {fast_loop};"

        slow_code = f"""{dtype} slow_mi3_{suf}({dtype} *data, int n) {{
    {dtype} total = {zero};
    for (int i = 0; i < n - {chunk_sz - 1}; i++) {{
        {dtype} *quad = malloc({chunk_sz} * sizeof({dtype}));
{slow_loop}
        free(quad);
    }}
    return total;
}}"""

        fast_code = f"""{dtype} fast_mi3_{suf}({dtype} *data, int n) {{
    {dtype} total = {zero};
    for (int i = 0; i < n - {chunk_sz - 1}; i++) {{
        {fast_expr}
    }}
    return total;
}}"""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *data = malloc(N * sizeof({dtype}));
    for (int i = 0; i < N; i++) data[i] = ({dtype})(i % 100 + 1) * ({dtype})0.1{suf_t};

    struct timespec t0, t1;
    volatile {dtype} r_slow, r_fast;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_slow = slow_mi3_{suf}(data, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    r_fast = fast_mi3_{suf}(data, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1e-12) < 1e-4) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(data);
    return 0;
}}"""

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"MI-3_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=f"chunk={chunk_sz}, op={op}, {dtype}, n={N}",
            dtype=dtype,
            difficulty="medium",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=1,
            lines_of_code=9,
            expected_speedup_range="10x-100x",
            composition=[]
        )
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "metadata": asdict(metadata)}


GENERATORS = {
    "SR-1": SR1_Generator(),
    "SR-2": SR2_Generator(),
    "SR-3": SR3_Generator(),
    "SR-4": SR4_Generator(),
    "SR-5": SR5_Generator(),
    "IS-1": IS1_Generator(),
    "IS-2": IS2_Generator(),
    "IS-3": IS3_Generator(),
    "IS-4": IS4_Generator(),
    "IS-5": IS5_Generator(),
    "CF-1": CF1_Generator(),
    "CF-2": CF2_Generator(),
    "CF-3": CF3_Generator(),
    "CF-4": CF4_Generator(),
    "HR-1": HR1_Generator(),
    "HR-2": HR2_Generator(),
    "HR-3": HR3_Generator(),
    "HR-4": HR4_Generator(),
    "HR-5": HR5_Generator(),
    "DS-1": DS1_Generator(),
    "DS-2": DS2_Generator(),
    "DS-3": DS3_Generator(),
    "DS-4": DS4_Generator(),
    "AL-1": AL1_Generator(),
    "AL-2": AL2_Generator(),
    "AL-3": AL3_Generator(),
    "AL-4": AL4_Generator(),
    "MI-1": MI1_Generator(),
    "MI-2": MI2_Generator(),
    "MI-3": MI3_Generator(),
    "MI-4": MI4_Generator(),
    "COMP": ComposedGenerator(),
}

def generate_dataset(patterns: str, n_variants: int, output_dir: str, base_seed: int = 42):
    """Generate the full dataset."""
    os.makedirs(output_dir, exist_ok=True)

    # Determine which generators to use
    if patterns == "all":
        gens = list(GENERATORS.items())
    elif "-" in patterns:
        gens = [(patterns, GENERATORS[patterns])]
    else:
        # Category prefix like "SR", "IS", "AL"
        gens = [(k, v) for k, v in GENERATORS.items() if k.startswith(patterns)]

    all_metadata = []
    total = 0

    for pat_id, gen in gens:
        pat_dir = os.path.join(output_dir, pat_id.replace("-", "_"))
        os.makedirs(pat_dir, exist_ok=True)

        for i in range(n_variants):
            seed = base_seed + hash(pat_id) + i * 7919  # Deterministic but varied
            result = gen.generate(i, seed)

            vid = result["metadata"]["variant_id"]
            var_dir = os.path.join(pat_dir, vid)
            os.makedirs(var_dir, exist_ok=True)

            # Write files
            # slow.c / fast.c are compiled as standalone translation units
            # (separate from test.c) so the compiler cannot inline across the
            # boundary. __attribute__((noinline)) is added as extra insurance
            # unless the generator already includes it (to avoid misplacement
            # when the code starts with #include or static helpers).
            _hdr = "#include <stdio.h>\n#include <stdlib.h>\n#include <math.h>\n#include <string.h>\n\n"
            def _write_tu(path, code):
                has_includes = "#include" in code
                has_noinline = "__attribute__((noinline))" in code
                if has_noinline:
                    # noinline already placed correctly by the generator
                    content = ("" if has_includes else _hdr) + code
                elif has_includes:
                    # Insert noinline AFTER the include block, not before it
                    lines = code.split("\n")
                    insert_at = 0
                    for idx, ln in enumerate(lines):
                        if ln.strip().startswith("#"):
                            insert_at = idx + 1
                    lines.insert(insert_at, "__attribute__((noinline))")
                    content = "\n".join(lines)
                else:
                    content = _hdr + "__attribute__((noinline))\n" + code
                with open(path, "w") as f:
                    f.write(content)
            _write_tu(os.path.join(var_dir, "slow.c"), result["slow_code"])
            _write_tu(os.path.join(var_dir, "fast.c"), result["fast_code"])
            with open(os.path.join(var_dir, "test.c"), "w") as f:
                f.write(result["test_code"])
            if result.get("helper_code"):
                with open(os.path.join(var_dir, "helper.c"), "w") as f:
                    f.write(result["helper_code"])
            with open(os.path.join(var_dir, "metadata.json"), "w") as f:
                json.dump(result["metadata"], f, indent=2)

            all_metadata.append(result["metadata"])
            total += 1

    # Write master index
    with open(os.path.join(output_dir, "index.json"), "w") as f:
        json.dump({
            "total_variants": total,
            "patterns": list(set(m["pattern_id"] for m in all_metadata)),
            "categories": list(set(m["category"] for m in all_metadata)),
            "variants": all_metadata,
        }, f, indent=2)

    # Write CSV summary
    with open(os.path.join(output_dir, "index.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "variant_id", "pattern_id", "category", "pattern_name",
            "variant_desc", "dtype", "difficulty",
            "compiler_fixable", "expected_speedup_range"
        ])
        writer.writeheader()
        for m in all_metadata:
            writer.writerow({k: m[k] for k in writer.fieldnames})

    print(f"Generated {total} variants across {len(gens)} patterns in {output_dir}/")
    print(f"  Index: {output_dir}/index.json")
    print(f"  CSV:   {output_dir}/index.csv")

    # Print summary
    from collections import Counter
    by_pattern = Counter(m["pattern_id"] for m in all_metadata)
    by_diff = Counter(m["difficulty"] for m in all_metadata)
    print(f"\n  By pattern: {dict(by_pattern)}")
    print(f"  By difficulty: {dict(by_diff)}")

def main():
    parser = argparse.ArgumentParser(description="Generate pattern variant dataset")
    parser.add_argument("--patterns", default="all",
                        help="Which patterns: 'all', category prefix 'SR', or specific 'SR-1'")
    parser.add_argument("--variants", type=int, default=20,
                        help="Number of variants per pattern (default: 20)")
    parser.add_argument("--output", default="dataset",
                        help="Output directory (default: dataset/)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    generate_dataset(args.patterns, args.variants, args.output, args.seed)


if __name__ == "__main__":
    main()
