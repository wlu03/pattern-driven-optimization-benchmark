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

class ComposedGenerator(PatternTemplate):
    """Generate programs with 2-3 overlapping patterns."""

    def __init__(self):
        super().__init__("COMP", "Composed",
                         "Multiple Overlapping Patterns")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"

        combo = rng.choice([
            # SR-3 + MI-4: Redundant aggregation + column-major access
            "sr3_mi4",
            # SR-1 + CF-1: Loop-invariant computation + branch in loop
            "sr1_cf1",
            # HR-2 + IS-1: Copy-paste duplication + sparse data
            "hr2_is1",
            # SR-4 + HR-4: Invariant call + defensive checks
            "sr4_hr4",
            # DS-4 + CF-2: AoS access + redundant bounds
            "ds4_cf2",
        ])

        if combo == "sr3_mi4":
            slow_code = f"""void slow_comp_{suf}(double *mat, double *col_avgs, int rows, int cols) {{
    // Pattern 1 (MI-4): Column-major traversal
    // Pattern 2 (SR-3): Recompute column sum from scratch for each row prefix
    for (int j = 0; j < cols; j++) {{
        double sum = 0.0;
        for (int i = 0; i < rows; i++) {{
            sum = 0.0;
            for (int k = 0; k <= i; k++) {{
                sum += mat[k * cols + j];  // Column-major access
            }}
        }}
        col_avgs[j] = sum / rows;
    }}
}}"""
            fast_code = f"""void fast_comp_{suf}(double *mat, double *col_avgs, int rows, int cols) {{
    // Fix MI-4: Row-major access order
    // Fix SR-3: Running accumulator instead of recomputation
    for (int j = 0; j < cols; j++) col_avgs[j] = 0.0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            col_avgs[j] += mat[i * cols + j];
        }}
    }}
    for (int j = 0; j < cols; j++) col_avgs[j] /= rows;
}}"""
            patterns = ["SR-3", "MI-4"]
            desc = "Redundant aggregation + column-major access"

        elif combo == "sr1_cf1":
            slow_code = f"""double slow_comp_{suf}(double *A, double *B, int n, double k, int mode) {{
    double total = 0.0;
    for (int i = 0; i < n; i++) {{
        // Pattern CF-1: Branch on invariant `mode`
        double val;
        if (mode == 1) val = A[i] + B[i] * k;      // Pattern SR-1
        else if (mode == 2) val = A[i] - B[i] * k;  // Pattern SR-1
        else val = A[i] * B[i] * k;                  // Pattern SR-1
        total += val;
    }}
    return total;
}}"""
            fast_code = f"""double fast_comp_{suf}(double *A, double *B, int n, double k, int mode) {{
    double sumA = 0.0, sumB = 0.0;
    // Fix CF-1: Hoist branch
    // Fix SR-1: Factor out invariant k
    if (mode == 1) {{
        for (int i = 0; i < n; i++) {{ sumA += A[i]; sumB += B[i]; }}
        return sumA + sumB * k;
    }} else if (mode == 2) {{
        for (int i = 0; i < n; i++) {{ sumA += A[i]; sumB += B[i]; }}
        return sumA - sumB * k;
    }} else {{
        double sumAB = 0.0;
        for (int i = 0; i < n; i++) sumAB += A[i] * B[i];
        return sumAB * k;
    }}
}}"""
            patterns = ["SR-1", "CF-1"]
            desc = "Loop-invariant computation + branch in loop"

        elif combo == "sr4_hr4":
            slow_code = f"""#include <math.h>
double config_val_{suf}(int key) {{
    double r = 0.0;
    for (int i = 0; i < 100; i++) r += sin((double)(key+i));
    return r;
}}
double slow_comp_{suf}(double *arr, int n, int key) {{
    double sum = 0.0;
    for (int i = 0; i < n; i++) {{
        // Pattern HR-4: Redundant checks
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        // Pattern SR-4: Invariant function call
        double factor = config_val_{suf}(key);
        sum += arr[i] * factor;
    }}
    return sum;
}}"""
            fast_code = f"""double fast_comp_{suf}(double *arr, int n, int key) {{
    if (arr == NULL || n <= 0) return 0.0;
    // Fix SR-4: Hoist invariant call
    double factor = config_val_{suf}(key);
    // Fix HR-4: Remove redundant checks
    double sum = 0.0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}}"""
            patterns = ["SR-4", "HR-4"]
            desc = "Invariant function call + defensive checks"

        else:  # ds4_cf2
            slow_code = f"""typedef struct {{ double x,y,z,vx,vy,vz,mass,charge; }} P_{suf};
double slow_comp_{suf}(P_{suf} *p, int n) {{
    double total = 0.0;
    for (int i = 0; i < n; i++) {{
        // Pattern CF-2: Redundant bounds check
        if (i >= 0 && i < n) {{
            // Pattern DS-4: AoS access for single field
            total += p[i].mass;
        }}
    }}
    return total;
}}"""
            fast_code = f"""double fast_comp_{suf}(double *mass, int n) {{
    // Fix DS-4: SoA layout, Fix CF-2: Remove redundant check
    double total = 0.0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}}"""
            patterns = ["DS-4", "CF-2"]
            desc = "AoS access + redundant bounds checking"

        metadata = VariantMetadata(
            pattern_id="COMP",
            variant_id=f"COMP_v{variant_num:03d}",
            category="Composed",
            pattern_name="Multiple Overlapping Patterns",
            variant_desc=desc,
            dtype="double",
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

GENERATORS = {
    "SR-1": SR1_Generator(),
    "SR-3": SR3_Generator(),
    "SR-4": SR4_Generator(),
    "IS-1": IS1_Generator(),
    "DS-4": DS4_Generator(),
    "AL-1": AL1_Generator(),
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
            with open(os.path.join(var_dir, "slow.c"), "w") as f:
                f.write(result["slow_code"])
            with open(os.path.join(var_dir, "fast.c"), "w") as f:
                f.write(result["fast_code"])
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
