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
    """SR-1: Loop-Invariant Semantic Computation
    Varies: array count, invariant count, dtype, binary operation,
    unary math wrapping, loop style (for/while), dimensionality (1D/2D),
    reduction operator
    """

    def __init__(self):
        super().__init__("SR-1", "Semantic Redundancy",
                         "Loop-Invariant Semantic Computation")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        dtype = rng.choice(["int", "float", "double"])
        n_arrays = rng.randint(2, 6)           # 2-6 input arrays
        n_invariants = rng.randint(1, 4)       # 1-4 loop-invariant terms
        use_2d = rng.choice([False, False, True])  # sometimes 2D
        loop_style = rng.choice(["for", "while", "for"])  # bias toward for
        # Pick a binary op for combining invariant with array element
        bin_op, bin_op_name = rng.choice(BINARY_OPS)
        # Sometimes wrap array access in a unary math fn
        use_unary = rng.choice([False, False, True])
        unary_fn = rng.choice(UNARY_MATH_FNS)[0] if use_unary else None
        # Reduction operator
        red_op, red_name = rng.choice([("+=", "sum"), ("+=", "sum"), ("*=", "product")])
        if red_op == "*=" and dtype == "int":
            red_op, red_name = "+=", "sum"  # avoid overflow

        arr_names = [chr(65 + i) for i in range(n_arrays)]  # A, B, C, ...
        inv_names = [f"k{i}" for i in range(n_invariants)]

        fn_name = f"{self.pattern_id.lower().replace('-','_')}_v{variant_num:03d}"

        # Expression building
        def arr_access(arr):
            acc = f"{arr}[i]" if not use_2d else f"{arr}[row * cols + col]"
            if unary_fn and dtype != "int":
                acc = f"{unary_fn}({acc})"
            return acc

        slow_terms = []
        fast_accumulators = []
        fast_combine = []

        for idx, arr in enumerate(arr_names):
            acc = arr_access(arr)
            if idx < n_invariants:
                inv = inv_names[idx]
                slow_terms.append(f"({inv} {bin_op} {acc})")
                fast_accumulators.append(f"    {dtype} sum_{arr} = {DTYPES[dtype]['zero']};")
                fast_combine.append(f"({inv} {bin_op} sum_{arr})")
            else:
                slow_terms.append(acc)
                fast_accumulators.append(f"    {dtype} sum_{arr} = {DTYPES[dtype]['zero']};")
                fast_combine.append(f"sum_{arr}")

        joiner = " + " if red_name == "sum" else " * "
        slow_expr = joiner.join(slow_terms)

        # Parameter declarations
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)
        inv_params = ", ".join(f"{dtype} {k}" for k in inv_names)
        if use_2d:
            size_params = "int rows, int cols"
            all_params = f"{arr_params}, {size_params}, {inv_params}"
        else:
            all_params = f"{arr_params}, int n, {inv_params}"

        # Loop scaffolding
        if use_2d:
            slow_loop_open = "    for (int row = 0; row < rows; row++) {\n        for (int col = 0; col < cols; col++) {"
            slow_loop_close = "        }\n    }"
            fast_loop_open = slow_loop_open
            fast_loop_close = slow_loop_close
            total_init = f"    {dtype} total = " + ("1" if red_name == "product" else DTYPES[dtype]['zero']) + ";"
        elif loop_style == "while":
            slow_loop_open = "    int i = 0;\n    while (i < n) {"
            slow_loop_close = "        i++;\n    }"
            fast_loop_open = slow_loop_open
            fast_loop_close = slow_loop_close
            total_init = f"    {dtype} total = " + ("1" if red_name == "product" else DTYPES[dtype]['zero']) + ";"
        else:
            slow_loop_open = "    for (int i = 0; i < n; i++) {"
            slow_loop_close = "    }"
            fast_loop_open = slow_loop_open
            fast_loop_close = slow_loop_close
            total_init = f"    {dtype} total = " + ("1" if red_name == "product" else DTYPES[dtype]['zero']) + ";"

        loop_var = "row * cols + col" if use_2d else "i"

        slow_code = f"""{dtype} slow_{fn_name}({all_params}) {{
{total_init}
{slow_loop_open}
        total {red_op} {slow_expr};
{slow_loop_close}
    return total;
}}"""

        # Fast version: separate accumulators, single combine at end
        acc_loop_body = "\n".join(
            f"        sum_{a} {red_op} {arr_access(a)};" for a in arr_names
        )
        combine_expr = joiner.join(fast_combine)

        fast_code = f"""{dtype} fast_{fn_name}({all_params}) {{
{chr(10).join(fast_accumulators)}
{fast_loop_open}
{acc_loop_body}
{fast_loop_close}
    return {combine_expr};
}}"""

        # Test harness
        n_val = "5000000"
        if use_2d:
            n_val_total = "ROWS * COLS"
            size_def = "#define ROWS 2000\n#define COLS 2500"
            size_args = "ROWS, COLS"
        else:
            n_val_total = "N"
            size_def = f"#define N {n_val}"
            size_args = "N"

        arr_allocs = "\n".join(
            f"    {dtype} *{a} = malloc({n_val_total} * sizeof({dtype}));\n"
            f"    for (int i = 0; i < {n_val_total}; i++) {a}[i] = ({dtype})(i % 100) * 0.01{DTYPES[dtype]['suffix']};"
            for a in arr_names
        )
        arr_args = ", ".join(arr_names)
        inv_args = ", ".join(f"2.{i}{DTYPES[dtype]['suffix']}" for i in range(n_invariants))
        arr_frees = "\n".join(f"    free({a});" for a in arr_names)
        needs_math = use_unary or dtype != "int"

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
{"#include <math.h>" if needs_math else ""}
#include <time.h>

{size_def}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
{arr_allocs}

    struct timespec t0, t1;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_slow = slow_{fn_name}({arr_args}, {size_args}, {inv_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_fast = fast_{fn_name}({arr_args}, {size_args}, {inv_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec)*1000.0 + (t1.tv_nsec - t0.tv_nsec)/1e6;

    double err = fabs((double)(r_slow - r_fast)) / fmax(fabs((double)r_slow), 1e-12);
    double tol = {"1e-2" if dtype == "float" else "1e-4"};
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, err < tol, ms_slow / fmax(ms_fast, 0.001));

{arr_frees}
    return 0;
}}"""

        desc_parts = [f"{n_arrays} arrays", f"{n_invariants} invariants", dtype, f"{bin_op_name} op"]
        if use_unary:
            desc_parts.append(f"{unary_fn}() wrapping")
        if use_2d:
            desc_parts.append("2D layout")
        if loop_style == "while":
            desc_parts.append("while-loop")
        if red_name != "sum":
            desc_parts.append(f"{red_name} reduction")

        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"{self.pattern_id}_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=", ".join(desc_parts),
            dtype=dtype,
            difficulty="easy" if n_invariants <= 1 and not use_2d else ("hard" if n_invariants >= 3 or use_unary else "medium"),
            compiler_fixable=False,
            num_loops=2 if use_2d else 1,
            num_arrays=n_arrays,
            lines_of_code=6 + n_arrays + (2 if use_2d else 0),
            expected_speedup_range="1.1x-2x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
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
            fast_body = f"""    {dtype} sum = {DTYPES[dtype]['zero']};
    {dtype} sum_sq = {DTYPES[dtype]['zero']};
{loop_open}
        sum += data[i];
        sum_sq += data[i] * data[i];
        {dtype} mean = sum / (i + 1);
        result[i] = sum_sq / (i + 1) - mean * mean;
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
        double err = fabs((double)(res_slow[i] - res_fast[i]));
        if (err > 1e-4) {{ correct = 0; break; }}
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

        slow_code = f"""{fn_code}

void slow_sr4_{suf}({dtype} *arr, int n, {key_params}) {{
{loop_open_slow}
{chr(10).join(call_lines_slow)}
        arr[i] {arr_op} {combine_expr};
{loop_close_slow}
}}"""

        fast_code = f"""void fast_sr4_{suf}({dtype} *arr, int n, {key_params}) {{
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

        test_code = f"// Test harness for IS-1 variant {variant_num} ({layout})\n// (auto-generated)\n"

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

        struct_templates = {
            "particles": [("x","double"), ("y","double"), ("z","double"),
                          ("vx","double"), ("vy","double"), ("vz","double"),
                          ("mass","double"), ("charge","double")],
            "pixels": [("r","int"), ("g","int"), ("b","int"), ("a","int"),
                       ("x","int"), ("y","int"), ("depth","float"), ("normal_x","float")],
            "vertices": [("px","float"), ("py","float"), ("pz","float"),
                         ("nx","float"), ("ny","float"), ("nz","float"),
                         ("u","float"), ("v","float")],
            "records": [("id","int"), ("timestamp","double"), ("value","double"),
                        ("weight","float"), ("category","int"), ("flags","int"),
                        ("score","double"), ("rank","int")],
            "sensors": [("temp","float"), ("humidity","float"), ("pressure","double"),
                        ("wind_speed","float"), ("wind_dir","float"),
                        ("light","int"), ("noise","int"), ("co2","float")],
            "events": [("time","double"), ("x","double"), ("y","double"),
                       ("energy","float"), ("channel","int"), ("quality","int"),
                       ("amplitude","double"), ("phase","float")],
        }

        template_name = rng.choice(list(struct_templates.keys()))
        all_fields = struct_templates[template_name]

        # Optionally vary field count (drop some trailing fields)
        n_fields_to_use = rng.choice([len(all_fields), len(all_fields),
                                       max(4, len(all_fields) - 2),
                                       max(6, len(all_fields) - 1)])
        fields = all_fields[:n_fields_to_use]

        # Choose a random subset of fields to access (1-4 fields)
        n_accessed = rng.randint(1, min(4, len(fields)))
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

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": "// Auto-generated test harness\n",
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

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": "// Auto-generated\n",
            "metadata": asdict(metadata)
        }

class SR2_Generator(PatternTemplate):
    """SR-2: Recomputable Expression Decomposition.
    Complex expression inside a loop can be algebraically decomposed
    into independent accumulators multiplied by constants at the end."""

    def __init__(self):
        super().__init__("SR-2", "Semantic Redundancy",
                         "Recomputable Expression Decomposition")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n_arrays = rng.choice([2, 3, 4])
        n_terms = rng.choice([2, 3, 4, 5])
        n_consts = rng.choice([1, 2, 3])
        loop_style = rng.choice(["for", "while"])
        N = rng.choice([5000000, 10000000, 20000000])

        arr_names = ["X", "Y", "Z", "W"][:n_arrays]
        const_names = ["alpha", "beta", "gamma"][:n_consts]

        # Build terms: e.g. "alpha * X[i] * X[i]", "beta * Y[i]", "alpha * beta"
        term_types = [
            ("sq", lambda a, c: f"{c} * {a}[i] * {a}[i]"),
            ("lin", lambda a, c: f"{c} * {a}[i]"),
            ("cube", lambda a, c: f"{c} * {a}[i] * {a}[i] * {a}[i]"),
            ("cross", lambda a, c: f"{c} * {a}[i]"),
            ("const", lambda a, c: f"{c}"),
        ]

        terms = []
        accum_fast_lines = []
        final_parts = []
        accum_decls = []

        for t_idx in range(n_terms):
            arr = rng.choice(arr_names)
            cst = rng.choice(const_names)
            kind = rng.choice(["sq", "lin", "cube", "const"])

            if kind == "sq":
                terms.append(f"{cst} * {arr}[i] * {arr}[i]")
                acc_name = f"sum{arr}sq"
                if acc_name not in [a[0] for a in accum_decls]:
                    accum_decls.append((acc_name, f"{acc_name} += {arr}[i] * {arr}[i];"))
                final_parts.append(f"{cst} * {acc_name}")
            elif kind == "lin":
                terms.append(f"{cst} * {arr}[i]")
                acc_name = f"sum{arr}"
                if acc_name not in [a[0] for a in accum_decls]:
                    accum_decls.append((acc_name, f"{acc_name} += {arr}[i];"))
                final_parts.append(f"{cst} * {acc_name}")
            elif kind == "cube":
                terms.append(f"{cst} * {arr}[i] * {arr}[i] * {arr}[i]")
                acc_name = f"sum{arr}cb"
                if acc_name not in [a[0] for a in accum_decls]:
                    accum_decls.append((acc_name, f"{acc_name} += {arr}[i] * {arr}[i] * {arr}[i];"))
                final_parts.append(f"{cst} * {acc_name}")
            else:
                terms.append(f"{cst}")
                final_parts.append(f"({dtype})n * {cst}")

        slow_expr = " + ".join(terms)
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)
        const_params = ", ".join(f"{dtype} {c}" for c in const_names)
        all_params = f"{arr_params}, int n, {const_params}"

        if loop_style == "for":
            slow_loop = f"for (int i = 0; i < n; i++)"
            fast_loop = f"for (int i = 0; i < n; i++)"
        else:
            slow_loop = f"int i = 0;\n    while (i < n)"
            fast_loop = f"int i = 0;\n    while (i < n)"

        # Deduplicate accumulators
        seen_acc = {}
        unique_accums = []
        for name, line in accum_decls:
            if name not in seen_acc:
                seen_acc[name] = True
                unique_accums.append((name, line))

        acc_init = "\n    ".join(f"{dtype} {name} = 0.0;" for name, _ in unique_accums)
        acc_body = "\n        ".join(line for _, line in unique_accums)
        if loop_style == "while":
            acc_body += "\n        i++;"
        final_expr = " + ".join(final_parts)

        slow_code = f"""{dtype} slow_sr2_{suf}({all_params}) {{
    {dtype} result = 0.0;
    {slow_loop} {{
        result += {slow_expr};
    {"    i++;" if loop_style == "while" else ""}
    }}
    return result;
}}"""

        fast_code = f"""{dtype} fast_sr2_{suf}({all_params}) {{
    {acc_init}
    {fast_loop} {{
        {acc_body}
    }}
    return {final_expr};
}}"""

        # Test harness
        arr_allocs = "\n    ".join(f'{dtype} *{a} = malloc({N} * sizeof({dtype})); for (int k = 0; k < {N}; k++) {a}[k] = ({dtype})(k % 100) * 0.01f;' for a in arr_names)
        const_vals = ", ".join("2.5" if i == 0 else "1.7" if i == 1 else "0.3" for i in range(n_consts))
        arr_args = ", ".join(arr_names)
        arr_frees = "\n    ".join(f"free({a});" for a in arr_names)

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
{dtype} slow_sr2_{suf}({all_params});
{dtype} fast_sr2_{suf}({all_params});
int main() {{
    int n = {N};
    {arr_allocs}
    {dtype} r_slow = slow_sr2_{suf}({arr_args}, n, {const_vals});
    {dtype} r_fast = fast_sr2_{suf}({arr_args}, n, {const_vals});
    double diff = fabs((double)(r_slow - r_fast));
    double rel = (fabs((double)r_slow) > 1e-15) ? diff / fabs((double)r_slow) : diff;
    printf("slow=%g fast=%g rel_err=%g %s\\n", (double)r_slow, (double)r_fast, rel, rel < 1e-4 ? "PASS" : "FAIL");
    {arr_frees}
    return rel < 1e-4 ? 0 : 1;
}}
"""

        desc = f"{n_terms}-term expression decomposition, {n_arrays} arrays, {n_consts} constants, {dtype}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty=rng.choice(["easy", "medium"]),
            compiler_fixable=False,
            num_loops=1,
            num_arrays=n_arrays,
            lines_of_code=6 + n_terms,
            expected_speedup_range="1.5x-5x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class CF1_Generator(PatternTemplate):
    """CF-1: Loop-Invariant Conditional (Hoistable Branch).
    A branch on a loop-invariant value checked every iteration.
    Optimization: hoist the branch outside the loop."""

    def __init__(self):
        super().__init__("CF-1", "Control Flow",
                         "Loop-Invariant Conditional")

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

        # Build slow: branch inside loop
        slow_branches = []
        fast_loops = []
        for m_idx in range(n_modes):
            op = ops[m_idx]
            if n_arrays == 2:
                expr = f"{arr_names[0]}[i] {op} {arr_names[1]}[i]"
            else:
                expr = f"({arr_names[0]}[i] {op} {arr_names[1]}[i]) {rng.choice(['+', '-'])} {arr_names[2]}[i]"

            cond = f"mode == {m_idx + 1}" if m_idx < n_modes - 1 else None
            if cond:
                prefix = "if" if m_idx == 0 else "} else if"
                slow_branches.append(f"        {prefix} ({cond}) {{\n            out[i] = {expr};")
            else:
                slow_branches.append(f"        }} else {{\n            out[i] = {expr};")

            if_kw = "if" if m_idx == 0 else "} else if" if m_idx < n_modes - 1 else "} else"
            cond_str = f" (mode == {m_idx + 1})" if m_idx < n_modes - 1 else ""
            fast_loops.append(f"    {if_kw}{cond_str} {{\n        for (int i = 0; i < n; i++) out[i] = {expr};")

        slow_branch_code = "\n".join(slow_branches) + "\n        }"
        fast_branch_code = "\n".join(fast_loops) + "\n    }"

        if loop_style == "for":
            slow_loop_head = "for (int i = 0; i < n; i++)"
        else:
            slow_loop_head = "int i = 0;\n    while (i < n)"

        slow_code = f"""void slow_cf1_{suf}({dtype} *out, {arr_params}, int n, int mode) {{
    {slow_loop_head} {{
{slow_branch_code}
{"        i++;" if loop_style == "while" else ""}
    }}
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
void slow_cf1_{suf}({dtype} *out, {arr_params}, int n, int mode);
void fast_cf1_{suf}({dtype} *out, {arr_params}, int n, int mode);
int main() {{
    int n = {N};
    {arr_allocs}
    {dtype} *out_s = malloc(n * sizeof({dtype}));
    {dtype} *out_f = malloc(n * sizeof({dtype}));
    slow_cf1_{suf}(out_s, {arr_args}, n, {mode_val});
    fast_cf1_{suf}(out_f, {arr_args}, n, {mode_val});
    int pass = 1;
    for (int i = 0; i < n; i++) {{
        if (fabs{suf_t}(out_s[i] - out_f[i]) > 1e-6{suf_t}) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    {arr_frees}
    free(out_s); free(out_f);
    return pass ? 0 : 1;
}}
"""

        desc = f"{n_modes} modes, {n_arrays} arrays, {dtype}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"CF-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=True,
            num_loops=1,
            num_arrays=n_arrays + 1,
            lines_of_code=6 + n_modes * 2,
            expected_speedup_range="1.2x-3x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class CF2_Generator(PatternTemplate):
    """CF-2: Redundant Bounds Checking.
    Defensive bounds checks inside hot inner loops that are
    guaranteed by the outer loop structure."""

    def __init__(self):
        super().__init__("CF-2", "Control Flow",
                         "Redundant Bounds Checking")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(list(DTYPES.keys()))
        layout = rng.choice(["row_sum", "col_sum", "scale", "transpose_sum"])
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

        if layout == "row_sum":
            slow_code = f"""void slow_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *row_sums) {{
    for (int i = 0; i < rows; i++) {{
        row_sums[i] = 0;
        {"int j = 0;" if loop_style == "while" else ""}
        {f"while (j < cols)" if loop_style == "while" else "for (int j = 0; j < cols; j++)"} {{
            if ({check_cond}) {{
                row_sums[i] += matrix[i * cols + j];
            }}
            {"j++;" if loop_style == "while" else ""}
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
void slow_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *row_sums);
void fast_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *row_sums);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.1;
    {dtype} *s_slow = malloc(rows * sizeof({dtype}));
    {dtype} *s_fast = malloc(rows * sizeof({dtype}));
    slow_cf2_{suf}(mat, rows, cols, s_slow);
    fast_cf2_{suf}(mat, rows, cols, s_fast);
    int pass = 1;
    for (int i = 0; i < rows; i++) {{
        if (fabs((double)(s_slow[i] - s_fast[i])) > 1e-4) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(mat); free(s_slow); free(s_fast);
    return pass ? 0 : 1;
}}
"""
        elif layout == "col_sum":
            slow_code = f"""void slow_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *col_sums) {{
    for (int j = 0; j < cols; j++) {{
        col_sums[j] = 0;
        for (int i = 0; i < rows; i++) {{
            if ({check_cond}) {{
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
void slow_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *col_sums);
void fast_cf2_{suf}({dtype} *matrix, int rows, int cols, {dtype} *col_sums);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.1;
    {dtype} *s_slow = malloc(cols * sizeof({dtype}));
    {dtype} *s_fast = malloc(cols * sizeof({dtype}));
    slow_cf2_{suf}(mat, rows, cols, s_slow);
    fast_cf2_{suf}(mat, rows, cols, s_fast);
    int pass = 1;
    for (int j = 0; j < cols; j++) {{
        if (fabs((double)(s_slow[j] - s_fast[j])) > 1e-4) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(mat); free(s_slow); free(s_fast);
    return pass ? 0 : 1;
}}
"""
        elif layout == "scale":
            scalar_val = rng.choice(["2.0", "0.5", "3.14"])
            slow_code = f"""void slow_cf2_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if ({check_cond}) {{
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
void slow_cf2_{suf}({dtype} *matrix, int rows, int cols);
void fast_cf2_{suf}({dtype} *matrix, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) slow[k] = ({dtype})(k % 100) * 0.1;
    memcpy(fast, slow, rows * cols * sizeof({dtype}));
    slow_cf2_{suf}(slow, rows, cols);
    fast_cf2_{suf}(fast, rows, cols);
    int pass = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(slow[k] - fast[k])) > 1e-4) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(slow); free(fast);
    return pass ? 0 : 1;
}}
"""
        else:  # transpose_sum
            slow_code = f"""{dtype} slow_cf2_{suf}({dtype} *A, {dtype} *B, int rows, int cols) {{
    {dtype} total = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if ({check_cond}) {{
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
{dtype} slow_cf2_{suf}({dtype} *A, {dtype} *B, int rows, int cols);
{dtype} fast_cf2_{suf}({dtype} *A, {dtype} *B, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *A = malloc(rows * cols * sizeof({dtype}));
    {dtype} *B = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) {{ A[k] = ({dtype})(k % 100) * 0.1; B[k] = ({dtype})(k % 50) * 0.2; }}
    {dtype} s = slow_cf2_{suf}(A, B, rows, cols);
    {dtype} f = fast_cf2_{suf}(A, B, rows, cols);
    double diff = fabs((double)(s - f));
    printf("slow=%g fast=%g %s\\n", (double)s, (double)f, diff < 1e-2 ? "PASS" : "FAIL");
    free(A); free(B);
    return diff < 1e-2 ? 0 : 1;
}}
"""

        desc = f"{layout} with {n_checks} redundant checks, {dtype}, {rows}x{cols}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"CF-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=True,
            num_loops=2,
            num_arrays=1,
            lines_of_code=10,
            expected_speedup_range="1.1x-2x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


class HR1_Generator(PatternTemplate):
    """HR-1: Redundant Temporary Variables.
    Unnecessary intermediate variables that force extra memory writes
    and prevent register optimization."""

    def __init__(self):
        super().__init__("HR-1", "Human Readability Style",
                         "Redundant Temporary Variables")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(list(DTYPES.keys()))
        n_temps = rng.choice([2, 3, 4, 5, 6])
        n_input_arrays = rng.choice([2, 3, 4])
        loop_style = rng.choice(["for", "while"])
        N = rng.choice([5000000, 10000000, 20000000])
        use_math = rng.random() < 0.3

        arr_names = ["A", "B", "C", "D"][:n_input_arrays]
        ops = rng.choices(["+", "-", "*"], k=n_temps)
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)

        # Build the chain of temporaries (slow)
        temp_lines = []
        expr_parts = []
        for t_idx in range(n_temps):
            arr = arr_names[t_idx % n_input_arrays]
            op = ops[t_idx]
            if t_idx == 0:
                prev = f"{arr}[i]"
                next_arr = arr_names[(t_idx + 1) % n_input_arrays]
                if use_math and t_idx == 0:
                    expr = f"sqrt({prev} * {prev} + {next_arr}[i] * {next_arr}[i])"
                else:
                    expr = f"{prev} {op} {next_arr}[i]"
                temp_lines.append(f"        {dtype} temp{t_idx + 1} = {expr};")
                expr_parts.append(expr)
            else:
                next_arr = arr_names[(t_idx + 1) % n_input_arrays] if t_idx < n_temps - 1 else arr_names[0]
                expr = f"temp{t_idx} {op} {next_arr}[i]"
                temp_lines.append(f"        {dtype} temp{t_idx + 1} = {expr};")
                expr_parts.append(f"{op} {next_arr}[i]")

        temp_lines.append(f"        {dtype} result = temp{n_temps};")
        temp_lines.append(f"        out[i] = result;")

        # Build the single expression (fast)
        # Reconstruct the nested expression
        fast_expr = expr_parts[0]
        for i in range(1, len(expr_parts)):
            part = expr_parts[i]
            fast_expr = f"({fast_expr}) {part}"

        if loop_style == "for":
            loop_head_slow = "for (int i = 0; i < n; i++)"
            loop_head_fast = "for (int i = 0; i < n; i++)"
            loop_inc = ""
        else:
            loop_head_slow = "int i = 0;\n    while (i < n)"
            loop_head_fast = "int i = 0;\n    while (i < n)"
            loop_inc = "\n        i++;"

        math_inc = "#include <math.h>\n" if use_math else ""

        slow_code = f"""{math_inc}void slow_hr1_{suf}({dtype} *out, {arr_params}, int n) {{
    {loop_head_slow} {{
{chr(10).join(temp_lines)}{loop_inc}
    }}
}}"""

        fast_code = f"""{math_inc}void fast_hr1_{suf}({dtype} *out, {arr_params}, int n) {{
    {loop_head_fast} {{
        out[i] = {fast_expr};{loop_inc}
    }}
}}"""

        arr_allocs = "\n    ".join(f'{dtype} *{a} = malloc({N} * sizeof({dtype})); for (int k = 0; k < {N}; k++) {a}[k] = ({dtype})((k % 100) + 1) * 0.1;' for a in arr_names)
        arr_args = ", ".join(arr_names)
        arr_frees = "\n    ".join(f"free({a});" for a in arr_names)
        suf_t = "f" if dtype == "float" else ""

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
void slow_hr1_{suf}({dtype} *out, {arr_params}, int n);
void fast_hr1_{suf}({dtype} *out, {arr_params}, int n);
int main() {{
    int n = {N};
    {arr_allocs}
    {dtype} *out_s = malloc(n * sizeof({dtype}));
    {dtype} *out_f = malloc(n * sizeof({dtype}));
    slow_hr1_{suf}(out_s, {arr_args}, n);
    fast_hr1_{suf}(out_f, {arr_args}, n);
    int pass = 1;
    for (int i = 0; i < n; i++) {{
        if (fabs{suf_t}(out_s[i] - out_f[i]) > 1e-4{suf_t}) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    {arr_frees}
    free(out_s); free(out_f);
    return pass ? 0 : 1;
}}
"""

        desc = f"{n_temps} temporaries, {n_input_arrays} arrays, {dtype}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"HR-1_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="easy",
            compiler_fixable=True,
            num_loops=1,
            num_arrays=n_input_arrays + 1,
            lines_of_code=6 + n_temps,
            expected_speedup_range="1.1x-2x",
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
void slow_mi4_{suf}({dtype} *matrix, int rows, int cols);
void fast_mi4_{suf}({dtype} *matrix, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) slow[k] = ({dtype})(k % 100) * 0.1;
    memcpy(fast, slow, rows * cols * sizeof({dtype}));
    slow_mi4_{suf}(slow, rows, cols);
    fast_mi4_{suf}(fast, rows, cols);
    int pass = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(slow[k] - fast[k])) > 1e-4) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(slow); free(fast);
    return pass ? 0 : 1;
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
void slow_mi4_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int rows, int cols);
void fast_mi4_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols}, total = rows * cols;
    {dtype} *A = malloc(total * sizeof({dtype}));
    {dtype} *B = malloc(total * sizeof({dtype}));
    {dtype} *s = malloc(total * sizeof({dtype}));
    {dtype} *f = malloc(total * sizeof({dtype}));
    for (int k = 0; k < total; k++) {{ A[k] = ({dtype})(k % 100) * 0.1; B[k] = ({dtype})(k % 50) * 0.2; }}
    slow_mi4_{suf}(s, A, B, rows, cols);
    fast_mi4_{suf}(f, A, B, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-4) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(A); free(B); free(s); free(f);
    return pass ? 0 : 1;
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
{dtype} slow_mi4_{suf}({dtype} *matrix, int rows, int cols);
{dtype} fast_mi4_{suf}({dtype} *matrix, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *mat = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) mat[k] = ({dtype})(k % 100) * 0.01;
    {dtype} s = slow_mi4_{suf}(mat, rows, cols);
    {dtype} f = fast_mi4_{suf}(mat, rows, cols);
    double diff = fabs((double)(s - f));
    printf("slow=%g fast=%g %s\\n", (double)s, (double)f, diff < 1e-2 ? "PASS" : "FAIL");
    free(mat);
    return diff < 1e-2 ? 0 : 1;
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
void slow_mi4_{suf}({dtype} *dst, {dtype} *src, int rows, int cols);
void fast_mi4_{suf}({dtype} *dst, {dtype} *src, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols}, total = rows * cols;
    {dtype} *src = malloc(total * sizeof({dtype}));
    {dtype} *s = malloc(total * sizeof({dtype}));
    {dtype} *f = malloc(total * sizeof({dtype}));
    for (int k = 0; k < total; k++) src[k] = ({dtype})(k % 100) * 0.1;
    slow_mi4_{suf}(s, src, rows, cols);
    fast_mi4_{suf}(f, src, rows, cols);
    int pass = 1;
    for (int k = 0; k < total; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-9) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(src); free(s); free(f);
    return pass ? 0 : 1;
}}
"""

        else:  # transform
            fn = rng.choice(UNARY_MATH_FNS)
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
void slow_mi4_{suf}({dtype} *matrix, int rows, int cols);
void fast_mi4_{suf}({dtype} *matrix, int rows, int cols);
int main() {{
    int rows = {rows}, cols = {cols};
    {dtype} *slow = malloc(rows * cols * sizeof({dtype}));
    {dtype} *fast = malloc(rows * cols * sizeof({dtype}));
    for (int k = 0; k < rows * cols; k++) slow[k] = ({dtype})((k % 100) + 1) * 0.01;
    memcpy(fast, slow, rows * cols * sizeof({dtype}));
    slow_mi4_{suf}(slow, rows, cols);
    fast_mi4_{suf}(fast, rows, cols);
    int pass = 1;
    for (int k = 0; k < rows * cols; k++) {{
        if (fabs((double)(slow[k] - fast[k])) > 1e-6) {{ pass = 0; break; }}
    }}
    printf("%s\\n", pass ? "PASS" : "FAIL");
    free(slow); free(fast);
    return pass ? 0 : 1;
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
{dtype} config_val_{suf}(int key) {{
    {dtype} r = 0;
    for (int i = 0; i < 100; i++) r += ({dtype})sin((double)(key+i));
    return r;
}}
{dtype} slow_comp_{suf}({dtype} *arr, int n, int key) {{
    {dtype} sum = 0;
    for (int i = 0; i < n; i++) {{
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        {dtype} factor = config_val_{suf}(key);
        sum += arr[i] * factor;
    }}
    return sum;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *arr, int n, int key) {{
    if (arr == NULL || n <= 0) return 0;
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
{dtype} compute_{suf}(int key) {{
    {dtype} r = 0;
    for (int i = 0; i < 50; i++) r += ({dtype})sin((double)(key+i));
    return r;
}}
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
}}"""
            fast_code = f"""void fast_comp_{suf}({dtype} *out, {dtype} *A, int n, int key, int mode) {{
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

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": "// Auto-generated\n",
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


GENERATORS = {
    "SR-1": SR1_Generator(),
    "SR-2": SR2_Generator(),
    "SR-3": SR3_Generator(),
    "SR-4": SR4_Generator(),
    "IS-1": IS1_Generator(),
    "IS-5": IS5_Generator(),
    "CF-1": CF1_Generator(),
    "CF-2": CF2_Generator(),
    "HR-1": HR1_Generator(),
    "DS-4": DS4_Generator(),
    "AL-1": AL1_Generator(),
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
            # boundary. __attribute__((noinline)) is added as extra insurance.
            _hdr = "#include <stdio.h>\n#include <stdlib.h>\n#include <math.h>\n#include <string.h>\n\n"
            with open(os.path.join(var_dir, "slow.c"), "w") as f:
                f.write(_hdr + "__attribute__((noinline))\n" + result["slow_code"])
            with open(os.path.join(var_dir, "fast.c"), "w") as f:
                f.write(_hdr + "__attribute__((noinline))\n" + result["fast_code"])
            with open(os.path.join(var_dir, "test.c"), "w") as f:
                f.write(result["test_code"])
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
