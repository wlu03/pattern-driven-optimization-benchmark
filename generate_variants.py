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
        fast_acc_exprs = []   # what each accumulator accumulates each iteration

        size_expr = "rows * cols" if use_2d else "n"
        acc_init = "1" if red_name == "product" else DTYPES[dtype]['zero']
        for idx, arr in enumerate(arr_names):
            acc = arr_access(arr)
            if idx < n_invariants:
                inv = inv_names[idx]
                full_term = f"({inv} {bin_op} {acc})"
                slow_terms.append(full_term)
                fast_accumulators.append(f"    {dtype} sum_{arr} = {acc_init};")
                if red_name == "product":
                    # Product reduction: each accumulator carries the full term
                    # product_i(k op A[i]) cannot be simplified → keep full expression
                    fast_acc_exprs.append(full_term)
                    fast_combine.append(f"sum_{arr}")
                else:
                    # Sum reduction: accumulate only array part, hoist invariant
                    # sum_i(k * A[i]) = k * sum_A
                    # sum_i(k + A[i]) = N*k + sum_A
                    # sum_i(k - A[i]) = N*k - sum_A
                    fast_acc_exprs.append(acc)
                    if bin_op == "*":
                        fast_combine.append(f"({inv} * sum_{arr})")
                    elif bin_op == "+":
                        fast_combine.append(f"(({dtype}){size_expr} * {inv} + sum_{arr})")
                    else:  # "-"
                        fast_combine.append(f"(({dtype}){size_expr} * {inv} - sum_{arr})")
            else:
                slow_terms.append(acc)
                fast_accumulators.append(f"    {dtype} sum_{arr} = {acc_init};")
                fast_acc_exprs.append(acc)
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
            f"        sum_{a} {red_op} {expr};"
            for a, expr in zip(arr_names, fast_acc_exprs)
        )
        combine_expr = joiner.join(fast_combine)

        fast_code = f"""{dtype} fast_{fn_name}({all_params}) {{
{chr(10).join(fast_accumulators)}
{fast_loop_open}
{acc_loop_body}
{fast_loop_close}
    return {combine_expr};
}}"""

        # Test harness — product reduction overflows with large N;
        # float accumulates rounding error faster than double
        if red_name == "product":
            n_val = "200"
            n_rows, n_cols = "10", "20"
        elif dtype == "float":
            n_val = "500000"
            n_rows, n_cols = "500", "1000"
        else:
            n_val = "5000000"
            n_rows, n_cols = "2000", "2500"
        if use_2d:
            n_val_total = "ROWS * COLS"
            size_def = f"#define ROWS {n_rows}\n#define COLS {n_cols}"
            size_args = "ROWS, COLS"
        else:
            n_val_total = "N"
            size_def = f"#define N {n_val}"
            size_args = "N"

        # Use offset+1 for log variants to avoid log(0) = -inf;
        # Product reduction needs values near 1.0 to avoid overflow
        data_offset = "1.0" if (unary_fn == "log" and dtype != "int") else "0.0"
        data_scale = "0.001" if red_name == "product" else "0.01"
        data_suffix = DTYPES[dtype]['suffix']
        arr_allocs = "\n".join(
            f"    {dtype} *{a} = malloc({n_val_total} * sizeof({dtype}));\n"
            f"    for (int i = 0; i < {n_val_total}; i++) {a}[i] = ({dtype})(i % 100) * {data_scale}{data_suffix} + {data_offset}{data_suffix};"
            for a in arr_names
        )
        arr_args = ", ".join(arr_names)
        if dtype == "int":
            inv_args = ", ".join(str(2 + i) for i in range(n_invariants))
        else:
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
        # Cumulative variants are O(n²) in slow — cap at 30000 to avoid timeout
        if agg_type.startswith("cumulative"):
            n_scale = rng.choice([10000, 20000, 30000])
        else:
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
        double diff = fabs((double)(res_slow[i] - res_fast[i]));
        double mag  = fmax(fabs((double)res_slow[i]), 1e-12);
        if (diff > mag * {"1e-4" if dtype != "float" else "1e-3"} && diff > {"1e-6" if dtype != "float" else "1e-2"}) {{ correct = 0; break; }}
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


# ── SR-5 ──────────────────────────────────────────────────────

class SR5_Generator(PatternTemplate):
    """SR-5: Repeated Division by Loop-Invariant Denominator.
    compute_norm is called every iteration; compiler cannot hoist because
    out[] could alias w[]. Optimization: hoist once, use reciprocal multiply."""

    def __init__(self):
        super().__init__("SR-5", "Semantic Redundancy",
                         "Repeated Division by Loop-Invariant Denominator")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([1000000, 2000000, 5000000])
        m = rng.choice([64, 128, 256])
        nt = rng.choice(["l2", "l1", "rms"])
        if nt == "l2":
            nb = f"    {dtype} s=0;\n    for(int j=0;j<m;j++) s+=w[j]*w[j];\n    return ({dtype})sqrt((double)s);"
        elif nt == "l1":
            nb = f"    {dtype} s=0;\n    for(int j=0;j<m;j++) s+=({dtype})fabs((double)w[j]);\n    return s;"
        else:
            nb = f"    {dtype} s=0;\n    for(int j=0;j<m;j++) s+=w[j]*w[j];\n    return ({dtype})sqrt((double)s/m);"
        helper = f"#include <math.h>\nstatic {dtype} norm_{suf}({dtype} *w,int m){{\n{nb}\n}}"
        slow_code = (f"{helper}\n\n"
                     f"void slow_sr5_{suf}({dtype} *out,{dtype} *data,int n,{dtype} *w,int m){{\n"
                     f"    for(int i=0;i<n;i++) out[i]=data[i]/norm_{suf}(w,m);\n}}")
        fast_code = (f"{helper}\n\n"
                     f"void fast_sr5_{suf}({dtype} *out,{dtype} *data,int n,{dtype} *w,int m){{\n"
                     f"    {dtype} inv=({dtype})1.0/norm_{suf}(w,m);\n"
                     f"    for(int i=0;i<n;i++) out[i]=data[i]*inv;\n}}")
        tol = "1e-3" if dtype == "float" else "1e-7"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define M {m}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *data=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype})),*w=malloc(M*sizeof({dtype}));
    for(int i=0;i<N;i++) data[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
    for(int i=0;i<M;i++) w[i]=({dtype})((i%10)+1)*0.1{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_sr5_{suf}(os,data,N,w,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_sr5_{suf}(of,data,N,w,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i])),r=fabs((double)os[i]);if(d>{tol}*(r+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(data);free(os);free(of);free(w);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"SR-5_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{nt} norm, {dtype}, n={n}, m={m}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=2, lines_of_code=10,
                    expected_speedup_range="10x-100x", composition=[]))}


# ── IS-2 ──────────────────────────────────────────────────────

class IS2_Generator(PatternTemplate):
    """IS-2: Data Distribution Skew.
    Slow: always computes sign+fabs before deciding path.
    Fast: cheap fabs check first; only computes sign for rare outliers."""

    def __init__(self):
        super().__init__("IS-2", "Input-Sensitive Inefficiency",
                         "Unconditional Expensive Call on Skewed Data")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        threshold = rng.choice(["1.0", "2.0", "0.5"])
        outlier_pct = rng.choice([1, 2, 5])   # % of data that are outliers
        # vary the expensive transform in the else branch
        transform = rng.choice(["log", "sqrt_offset", "exp_clamp"])
        if transform == "log":
            t_expr = f"sign*(({dtype}){threshold}+({dtype})log(1.0+abs_val-({dtype}){threshold}))"
        elif transform == "sqrt_offset":
            t_expr = f"sign*(({dtype}){threshold}+({dtype})sqrt((double)(abs_val-({dtype}){threshold})))"
        else:
            t_expr = f"sign*(({dtype}){threshold}*(1.0{DTYPES[dtype]['suffix']}+({dtype})exp((double)(abs_val-({dtype}){threshold})-1.0)))"

        slow_code = (f"#include <math.h>\n"
                     f"void slow_is2_{suf}({dtype} *out,{dtype} *in,int n,{dtype} thr){{\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        {dtype} val=in[i],sign=(val>=0)?1.0{DTYPES[dtype]['suffix']}:-1.0{DTYPES[dtype]['suffix']},abs_val=({dtype})fabs((double)val);\n"
                     f"        out[i]=(abs_val>thr)?{t_expr}:val;\n"
                     f"    }}\n}}")
        fast_code = (f"#include <math.h>\n"
                     f"void fast_is2_{suf}({dtype} *out,{dtype} *in,int n,{dtype} thr){{\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        {dtype} val=in[i];\n"
                     f"        if(({dtype})fabs((double)val)<=thr){{out[i]=val;}}\n"
                     f"        else{{\n"
                     f"            {dtype} sign=(val>=0)?1.0{DTYPES[dtype]['suffix']}:-1.0{DTYPES[dtype]['suffix']},abs_val=({dtype})fabs((double)val);\n"
                     f"            out[i]={t_expr};\n"
                     f"        }}\n"
                     f"    }}\n}}")
        tol = "1e-4" if dtype == "float" else "1e-9"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    srand(42);
    for(int i=0;i<N;i++) in[i]=(rand()%100<{outlier_pct})?(({dtype})(rand()%40+20)):((({dtype})(rand()%200)-100)*0.01{DTYPES[dtype]['suffix']});
    {dtype} thr=({dtype}){threshold};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_is2_{suf}(os,in,N,thr); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_is2_{suf}(of,in,N,thr); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i])),r=fabs((double)os[i]);if(d>{tol}*(r+1e-9)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(in);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"IS-2_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{transform} transform, {outlier_pct}% outliers, {dtype}, n={n}",
                    dtype=dtype, difficulty="medium", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=8,
                    expected_speedup_range="1.1x-2x", composition=[]))}


# ── IS-3 ──────────────────────────────────────────────────────

class IS3_Generator(PatternTemplate):
    """IS-3: Early Termination Opportunity.
    Slow: counts all violations (O(n)). Fast: returns on first violation."""

    def __init__(self):
        super().__init__("IS-3", "Input-Sensitive Inefficiency",
                         "Early Termination Opportunity")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        viol_pos = rng.choice([5, 10, 50, 100, 500])
        threshold_val = rng.choice(["100.0", "1000.0", "500.0"])
        n_reps = 20

        slow_code = (f"int slow_is3_{suf}({dtype} *arr,int n,{dtype} thr){{\n"
                     f"    int cnt=0;\n"
                     f"    for(int i=0;i<n;i++) if(arr[i]>thr) cnt++;\n"
                     f"    return cnt==0;\n}}")
        fast_code = (f"int fast_is3_{suf}({dtype} *arr,int n,{dtype} thr){{\n"
                     f"    for(int i=0;i<n;i++) if(arr[i]>thr) return 0;\n"
                     f"    return 1;\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *arr=malloc(N*sizeof({dtype}));
    srand(42);
    for(int i=0;i<N;i++) arr[i]=({dtype})(rand()%100)*0.1{DTYPES[dtype]['suffix']};
    arr[{viol_pos}]=({dtype}){threshold_val}+1.0{DTYPES[dtype]['suffix']};
    {dtype} thr=({dtype}){threshold_val};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    volatile int rs=0; for(int r=0;r<REPS;r++) rs=slow_is3_{suf}(arr,N,thr);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    volatile int rf=0; for(int r=0;r<REPS;r++) rf=fast_is3_{suf}(arr,N,thr);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=(slow_is3_{suf}(arr,N,thr)==fast_is3_{suf}(arr,N,thr));
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr); return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"IS-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"violation at pos {viol_pos}, {dtype}, n={n}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=6,
                    expected_speedup_range="100x-10000x", composition=[]))}


# ── IS-4 ──────────────────────────────────────────────────────

class IS4_Generator(PatternTemplate):
    """IS-4: Adaptive Sort (Nearly-Sorted Detection).
    Slow: always qsort O(n log n). Fast: samples 64 pairs; uses insertion sort
    for nearly-sorted input which is O(n). For random input both use qsort."""

    def __init__(self):
        super().__init__("IS-4", "Input-Sensitive Inefficiency",
                         "Adaptive Sort (Nearly-Sorted Detection)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n = rng.choice([500000, 1000000, 5000000])
        swap_pct = rng.choice([1, 2])   # % of elements swapped (keeps nearly sorted)
        sample_k = rng.choice([32, 64, 128])
        thresh = rng.choice([2, 4, 8])

        slow_code = (f"static int cmp_is4_{suf}(const void *a,const void *b){{return (*(int*)a-*(int*)b);}}\n\n"
                     f"void slow_is4_{suf}(int *arr,int n){{\n"
                     f"    qsort(arr,n,sizeof(int),cmp_is4_{suf});\n}}")
        fast_code = (f"static int cmp_is4_{suf}(const void *a,const void *b){{return (*(int*)a-*(int*)b);}}\n\n"
                     f"void fast_is4_{suf}(int *arr,int n){{\n"
                     f"    int inv=0; unsigned seed=12345u;\n"
                     f"    for(int s=0;s<{sample_k};s++){{\n"
                     f"        seed=seed*1664525u+1013904223u;\n"
                     f"        int i=(int)((seed>>1)%(unsigned)(n-1));\n"
                     f"        if(arr[i]>arr[i+1]) inv++;\n"
                     f"    }}\n"
                     f"    if(inv<={thresh}){{\n"
                     f"        for(int i=1;i<n;i++){{\n"
                     f"            int key=arr[i],j=i-1;\n"
                     f"            while(j>=0&&arr[j]>key){{arr[j+1]=arr[j];j--;}}\n"
                     f"            arr[j+1]=key;\n"
                     f"        }}\n"
                     f"    }}else{{\n"
                     f"        qsort(arr,n,sizeof(int),cmp_is4_{suf});\n"
                     f"    }}\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *base=malloc(N*sizeof(int)),*as=malloc(N*sizeof(int)),*af=malloc(N*sizeof(int));
    for(int i=0;i<N;i++) base[i]=i;
    srand(99);
    int swaps=N/{100//swap_pct};
    for(int s=0;s<swaps;s++){{int i=rand()%(N-1);int t=base[i];base[i]=base[i+1];base[i+1]=t;}}
    memcpy(as,base,N*sizeof(int)); memcpy(af,base,N*sizeof(int));
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_is4_{suf}(as,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_is4_{suf}(af,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++) if(as[i]!=af[i]){{correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(base);free(as);free(af);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"IS-4_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{swap_pct}% swaps, n={n}, sample_k={sample_k}",
                    dtype="int", difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=15,
                    expected_speedup_range="5x-20x", composition=[]))}


# ── IS-5 ──────────────────────────────────────────────────────

class IS5_Generator(PatternTemplate):
    """IS-5: Runtime Alias Check for Restrict Fast-Path.
    Slow: noinline without restrict — compiler generates conservative code.
    Fast: runtime non-overlap check dispatches to __restrict__ kernel."""

    def __init__(self):
        super().__init__("IS-5", "Input-Sensitive Inefficiency",
                         "Runtime Alias Check for Restrict Fast-Path")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 5
        # vary the computation expression
        expr_type = rng.choice(["quadratic", "linear_combo", "fused"])
        if expr_type == "quadratic":
            body = f"out[i]=A[i]*A[i]+B[i]*2.0{DTYPES[dtype]['suffix']}-A[i]*0.5{DTYPES[dtype]['suffix']}+B[i]*B[i];"
        elif expr_type == "linear_combo":
            body = f"out[i]=A[i]*1.5{DTYPES[dtype]['suffix']}+B[i]*2.5{DTYPES[dtype]['suffix']}-A[i]*B[i]*0.1{DTYPES[dtype]['suffix']};"
        else:
            body = f"out[i]=A[i]*A[i]-B[i]*B[i]+A[i]*B[i]*0.5{DTYPES[dtype]['suffix']}+1.0{DTYPES[dtype]['suffix']};"

        slow_code = (f"__attribute__((noinline))\n"
                     f"void slow_is5_{suf}({dtype} *out,{dtype} *A,{dtype} *B,int n){{\n"
                     f"    for(int i=0;i<n;i++) {body}\n}}")
        fast_code = (f"static void __attribute__((noinline))\n"
                     f"is5_kernel_{suf}({dtype} * __restrict__ out,const {dtype} * __restrict__ A,const {dtype} * __restrict__ B,int n){{\n"
                     f"    for(int i=0;i<n;i++) {body}\n}}\n\n"
                     f"void fast_is5_{suf}({dtype} *out,{dtype} *A,{dtype} *B,int n){{\n"
                     f"    int ok=(out+n<=A||A+n<=out)&&(out+n<=B||B+n<=out);\n"
                     f"    if(ok) is5_kernel_{suf}(out,A,B,n);\n"
                     f"    else for(int i=0;i<n;i++) {body}\n}}")
        tol = "1e-3" if dtype == "float" else "1e-9"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A=malloc(N*sizeof({dtype})),*B=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++){{A[i]=({dtype})((i%100)+1)*0.1{DTYPES[dtype]['suffix']};B[i]=({dtype})((i%50)+1)*0.05{DTYPES[dtype]['suffix']};}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_is5_{suf}(os,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_is5_{suf}(of,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i])),r=fabs((double)os[i]);if(d>{tol}*(r+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"IS-5_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{expr_type} expr, {dtype}, n={n}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=2, lines_of_code=8,
                    expected_speedup_range="1.5x-4x", composition=[]))}


# ── CF-3 ──────────────────────────────────────────────────────

class CF3_Generator(PatternTemplate):
    """CF-3: Vectorization-Hostile Redundant Conditional.
    Slow: per-element noinline guarded call (N calls, no SIMD).
    Fast: caller guarantees all-positive; inline branchless loop."""

    def __init__(self):
        super().__init__("CF-3", "Control Flow",
                         "Vectorization-Hostile Redundant Conditional")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 5
        op_type = rng.choice(["quadratic", "cubic", "poly"])
        if op_type == "quadratic":
            guarded_body = f"return x>0.0{DTYPES[dtype]['suffix']}?x*x+x*0.5{DTYPES[dtype]['suffix']}:0.0{DTYPES[dtype]['suffix']};"
            fast_body = f"out[i]=in[i]*in[i]+in[i]*0.5{DTYPES[dtype]['suffix']};"
        elif op_type == "cubic":
            guarded_body = f"return x>0.0{DTYPES[dtype]['suffix']}?x*x*x+x*x+x:0.0{DTYPES[dtype]['suffix']};"
            fast_body = f"out[i]=in[i]*in[i]*in[i]+in[i]*in[i]+in[i];"
        else:
            guarded_body = f"return x>0.0{DTYPES[dtype]['suffix']}?x*x+x*0.25{DTYPES[dtype]['suffix']}+1.0{DTYPES[dtype]['suffix']}:0.0{DTYPES[dtype]['suffix']};"
            fast_body = f"out[i]=in[i]*in[i]+in[i]*0.25{DTYPES[dtype]['suffix']}+1.0{DTYPES[dtype]['suffix']};"

        slow_code = (f"static {dtype} __attribute__((noinline)) cf3_guard_{suf}({dtype} x){{\n"
                     f"    {guarded_body}\n}}\n\n"
                     f"void slow_cf3_{suf}({dtype} *out,{dtype} *in,int n){{\n"
                     f"    for(int i=0;i<n;i++) out[i]=cf3_guard_{suf}(in[i]);\n}}")
        fast_code = (f"void fast_cf3_{suf}({dtype} *out,{dtype} *in,int n){{\n"
                     f"    for(int i=0;i<n;i++) {fast_body}\n}}")
        tol = "1e-3" if dtype == "float" else "1e-9"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++) in[i]=({dtype})((i%100)+1)*0.1{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_cf3_{suf}(os,in,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_cf3_{suf}(of,in,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i])),r=fabs((double)os[i]);if(d>{tol}*(r+1e-9)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(in);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"CF-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{op_type} op, {dtype}, n={n}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=8,
                    expected_speedup_range="2x-8x", composition=[]))}


# ── CF-4 ──────────────────────────────────────────────────────

class CF4_Generator(PatternTemplate):
    """CF-4: Dispatch in Hot Loop.
    Slow: per-element noinline dispatch via integer tag (N indirect calls).
    Fast: single tag check at entry; dispatches to inlined vectorizable loop."""

    def __init__(self):
        super().__init__("CF-4", "Control Flow",
                         "Function Dispatch in Hot Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 5
        tag_used = rng.choice([0, 1, 2])
        ops = [
            (f"return x>0.0{DTYPES[dtype]['suffix']}?x:0.0{DTYPES[dtype]['suffix']};",
             f"out[i]=in[i]>0.0{DTYPES[dtype]['suffix']}?in[i]:0.0{DTYPES[dtype]['suffix']};"),
            (f"return x*x;",
             f"out[i]=in[i]*in[i];"),
            (f"return x*1.5{DTYPES[dtype]['suffix']};",
             f"out[i]=in[i]*1.5{DTYPES[dtype]['suffix']};"),
        ]
        fn_bodies = [op[0] for op in ops]
        inline_bodies = [op[1] for op in ops]

        slow_code = (f"static {dtype} __attribute__((noinline)) cf4_fn0_{suf}({dtype} x){{{fn_bodies[0]}}}\n"
                     f"static {dtype} __attribute__((noinline)) cf4_fn1_{suf}({dtype} x){{{fn_bodies[1]}}}\n"
                     f"static {dtype} __attribute__((noinline)) cf4_fn2_{suf}({dtype} x){{{fn_bodies[2]}}}\n\n"
                     f"void slow_cf4_{suf}({dtype} *out,{dtype} *in,int n,int tag){{\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        if(tag==0) out[i]=cf4_fn0_{suf}(in[i]);\n"
                     f"        else if(tag==1) out[i]=cf4_fn1_{suf}(in[i]);\n"
                     f"        else out[i]=cf4_fn2_{suf}(in[i]);\n"
                     f"    }}\n}}")
        fast_code = (f"void fast_cf4_{suf}({dtype} *out,{dtype} *in,int n,int tag){{\n"
                     f"    if(tag==0){{for(int i=0;i<n;i++) {inline_bodies[0]}}}\n"
                     f"    else if(tag==1){{for(int i=0;i<n;i++) {inline_bodies[1]}}}\n"
                     f"    else{{for(int i=0;i<n;i++) {inline_bodies[2]}}}\n}}")
        tol = "1e-6" if dtype == "float" else "1e-12"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++) in[i]=({dtype})((i%200)-100)*0.05{DTYPES[dtype]['suffix']};
    int tag={tag_used};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_cf4_{suf}(os,in,N,tag);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_cf4_{suf}(of,in,N,tag);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i]));if(d>{tol}){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(in);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"CF-4_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"tag={tag_used}, {dtype}, n={n}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=10,
                    expected_speedup_range="2x-6x", composition=[]))}


# ── HR-2 ──────────────────────────────────────────────────────

class HR2_Generator(PatternTemplate):
    """HR-2: Copy-Paste Loop Duplication.
    Slow: 4 separate passes (mean X, mean Y, var X, var Y).
    Fast: 2 fused passes."""

    def __init__(self):
        super().__init__("HR-2", "Human-Style Antipatterns",
                         "Copy-Paste Loop Duplication")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 3
        tol = "1e-3" if dtype == "float" else "1e-7"

        slow_code = (f"void slow_hr2_{suf}({dtype} *X,{dtype} *Y,int n,\n"
                     f"    {dtype} *mx,{dtype} *my,{dtype} *vx,{dtype} *vy){{\n"
                     f"    {dtype} sx=0;\n"
                     f"    for(int i=0;i<n;i++) sx+=X[i];\n"
                     f"    *mx=sx/n;\n"
                     f"    {dtype} sy=0;\n"
                     f"    for(int i=0;i<n;i++) sy+=Y[i];\n"
                     f"    *my=sy/n;\n"
                     f"    {dtype} vs=0;\n"
                     f"    for(int i=0;i<n;i++){{{dtype} d=X[i]-*mx;vs+=d*d;}}\n"
                     f"    *vx=vs/n;\n"
                     f"    {dtype} vy2=0;\n"
                     f"    for(int i=0;i<n;i++){{{dtype} d=Y[i]-*my;vy2+=d*d;}}\n"
                     f"    *vy=vy2/n;\n}}")
        fast_code = (f"void fast_hr2_{suf}({dtype} *X,{dtype} *Y,int n,\n"
                     f"    {dtype} *mx,{dtype} *my,{dtype} *vx,{dtype} *vy){{\n"
                     f"    {dtype} sx=0,sy=0;\n"
                     f"    for(int i=0;i<n;i++){{sx+=X[i];sy+=Y[i];}}\n"
                     f"    *mx=sx/n; *my=sy/n;\n"
                     f"    {dtype} mvx=*mx,mvy=*my,vsx=0,vsy=0;\n"
                     f"    for(int i=0;i<n;i++){{{dtype} dx=X[i]-mvx,dy=Y[i]-mvy;vsx+=dx*dx;vsy+=dy*dy;}}\n"
                     f"    *vx=vsx/n; *vy=vsy/n;\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *X=malloc(N*sizeof({dtype})),*Y=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++){{X[i]=({dtype})((i%200)-100)*0.05{DTYPES[dtype]['suffix']};Y[i]=({dtype})((i%150)-75)*0.03{DTYPES[dtype]['suffix']};}}
    {dtype} mxs,mys,vxs,vys,mxf,myf,vxf,vyf;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_hr2_{suf}(X,Y,N,&mxs,&mys,&vxs,&vys);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_hr2_{suf}(X,Y,N,&mxf,&myf,&vxf,&vyf);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    double ref=fabs((double)mxs)+1e-12;
    int correct=fabs((double)(mxs-mxf))<{tol}*ref&&fabs((double)(mys-myf))<{tol}*(fabs((double)mys)+1e-12)
        &&fabs((double)(vxs-vxf))<{tol}*(fabs((double)vxs)+1e-12)&&fabs((double)(vys-vyf))<{tol}*(fabs((double)vys)+1e-12);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(X);free(Y);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"HR-2_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{dtype}, n={n}",
                    dtype=dtype, difficulty="medium", compiler_fixable=False,
                    num_loops=4, num_arrays=2, lines_of_code=18,
                    expected_speedup_range="1.5x-3x", composition=[]))}


# ── HR-3 ──────────────────────────────────────────────────────

class HR3_Generator(PatternTemplate):
    """HR-3: Dead / Debug Code Left in Hot Loop.
    Slow: volatile counter + NaN/overflow checks per element.
    Fast: clean loop without debug overhead."""

    def __init__(self):
        super().__init__("HR-3", "Human-Style Antipatterns",
                         "Dead / Debug Code in Hot Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 3
        # vary the actual computation
        op_type = rng.choice(["scale_add", "quadratic", "linear_combo"])
        scalar_a = rng.choice(["2.0", "1.5", "3.0"])
        scalar_b = rng.choice(["1.0", "0.5", "2.5"])
        if op_type == "scale_add":
            expr = f"in[i]*({dtype}){scalar_a}+({dtype}){scalar_b}"
        elif op_type == "quadratic":
            expr = f"in[i]*in[i]*({dtype}){scalar_a}+({dtype}){scalar_b}"
        else:
            expr = f"in[i]*({dtype}){scalar_a}-in[i]*({dtype}){scalar_b}+({dtype})1.0{DTYPES[dtype]['suffix']}"

        slow_code = (f"void slow_hr3_{suf}({dtype} *out,{dtype} *in,int n){{\n"
                     f"    static volatile int debug_ctr_{suf}=0;\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        debug_ctr_{suf}++;\n"
                     f"        if(in[i]!=in[i]){{;}}\n"
                     f"        out[i]={expr};\n"
                     f"        if(out[i]<-1e15||out[i]>1e15){{;}}\n"
                     f"    }}\n}}")
        fast_code = (f"void fast_hr3_{suf}({dtype} *out,{dtype} *in,int n){{\n"
                     f"    for(int i=0;i<n;i++) out[i]={expr};\n}}")
        tol = "1e-3" if dtype == "float" else "1e-9"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *in=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++) in[i]=({dtype})((i%200)-100)*0.1{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_hr3_{suf}(os,in,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_hr3_{suf}(of,in,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i])),r2=fabs((double)os[i]);if(d>{tol}*(r2+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(in);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"HR-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{op_type}, {dtype}, n={n}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=10,
                    expected_speedup_range="1.5x-4x", composition=[]))}


# ── HR-4 ──────────────────────────────────────────────────────

class HR4_Generator(PatternTemplate):
    """HR-4: Overly Defensive Checks Inside Hot Loop.
    Slow: redundant NULL/bounds/NaN checks inside the loop body.
    Fast: hoist checks before the loop, clean inner loop."""

    def __init__(self):
        super().__init__("HR-4", "Human-Style Antipatterns",
                         "Overly Defensive Checks in Hot Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 10
        op_type = rng.choice(["sum", "dot", "scale_sum"])
        if op_type == "sum":
            slow_inner = f"if(arr==NULL)continue;if(n<=0)break;if(i<0||i>=n)continue;if(arr[i]!=arr[i])continue;sum+=arr[i];"
            fast_inner = "sum+=arr[i];"
            sig = f"{dtype} *arr,int n"
            call_args = "arr,N"
            ret = f"{dtype}"
            setup = f"{dtype} *arr=malloc(N*sizeof({dtype}));for(int i=0;i<N;i++) arr[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};"
            free_s = "free(arr);"
        elif op_type == "dot":
            slow_inner = f"if(A==NULL||B==NULL)continue;if(i<0||i>=n)continue;if(A[i]!=A[i]||B[i]!=B[i])continue;sum+=A[i]*B[i];"
            fast_inner = "sum+=A[i]*B[i];"
            sig = f"{dtype} *A,{dtype} *B,int n"
            call_args = "A,B,N"
            ret = f"{dtype}"
            setup = (f"{dtype} *A=malloc(N*sizeof({dtype})),*B=malloc(N*sizeof({dtype}));\n"
                     f"    for(int i=0;i<N;i++){{A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};B[i]=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};}}")
            free_s = "free(A);free(B);"
        else:
            slow_inner = f"if(arr==NULL)continue;if(n<=0)break;if(i<0||i>=n)continue;if(arr[i]!=arr[i])continue;sum+=arr[i]*({dtype})2.0{DTYPES[dtype]['suffix']}+({dtype})1.0{DTYPES[dtype]['suffix']};"
            fast_inner = f"sum+=arr[i]*({dtype})2.0{DTYPES[dtype]['suffix']}+({dtype})1.0{DTYPES[dtype]['suffix']};"
            sig = f"{dtype} *arr,int n"
            call_args = "arr,N"
            ret = f"{dtype}"
            setup = f"{dtype} *arr=malloc(N*sizeof({dtype}));for(int i=0;i<N;i++) arr[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};"
            free_s = "free(arr);"

        slow_code = (f"{ret} slow_hr4_{suf}({sig}){{\n"
                     f"    {dtype} sum=0;\n"
                     f"    for(int i=0;i<n;i++){{{slow_inner}}}\n"
                     f"    return sum;\n}}")
        fast_code = (f"{ret} fast_hr4_{suf}({sig}){{\n"
                     f"    {dtype} sum=0;\n"
                     f"    for(int i=0;i<n;i++){{{fast_inner}}}\n"
                     f"    return sum;\n}}")
        tol = "1e-3" if dtype == "float" else "1e-7"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {setup}
    struct timespec t0,t1;
    {dtype} rs=0,rf=0;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) rs=slow_hr4_{suf}({call_args});
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) rf=fast_hr4_{suf}({call_args});
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    double diff=fabs((double)(rs-rf)),ref2=fabs((double)rs)+1e-12;
    int correct=diff<{tol}*ref2;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    {free_s} return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"HR-4_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{op_type}, {dtype}, n={n}",
                    dtype=dtype, difficulty="medium", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=8,
                    expected_speedup_range="1.5x-4x", composition=[]))}


# ── HR-5 ──────────────────────────────────────────────────────

class HR5_Generator(PatternTemplate):
    """HR-5: Append Anti-Pattern with Redundant Guards.
    Slow: guarded append with capacity/sign checks that are always true.
    Fast: direct indexed write."""

    def __init__(self):
        super().__init__("HR-5", "Human-Style Antipatterns",
                         "Append Anti-Pattern with Redundant Guards")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 5
        op_type = rng.choice(["add", "mul_add", "shift_add"])
        if op_type == "add":
            expr = "A[i]+B[i]"
        elif op_type == "mul_add":
            expr = "A[i]*2+B[i]"
        else:
            expr = "A[i]+B[i]+1"

        slow_code = (f"void slow_hr5_{suf}(int *out,int *A,int *B,int n){{\n"
                     f"    int pos=0;\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        if(pos<n){{\n"
                     f"            int val={expr};\n"
                     f"            if(val>=0){{out[pos]=val;pos=pos+1;}}\n"
                     f"        }}\n"
                     f"    }}\n}}")
        fast_code = (f"void fast_hr5_{suf}(int *out,int *A,int *B,int n){{\n"
                     f"    for(int i=0;i<n;i++) out[i]={expr};\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *A=malloc(N*sizeof(int)),*B=malloc(N*sizeof(int)),*os=malloc(N*sizeof(int)),*of=malloc(N*sizeof(int));
    for(int i=0;i<N;i++){{A[i]=(i%1000);B[i]=(i%500);}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_hr5_{suf}(os,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_hr5_{suf}(of,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++) if(os[i]!=of[i]){{correct=0;break;}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"HR-5_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{op_type} op, n={n}",
                    dtype="int", difficulty="low", compiler_fixable=True,
                    num_loops=1, num_arrays=2, lines_of_code=8,
                    expected_speedup_range="1.5x-4x", composition=[]))}


# ── DS-1 ──────────────────────────────────────────────────────

class DS1_Generator(PatternTemplate):
    """DS-1: Linear Search vs Hash Lookup.
    Slow: O(n_keys) linear scan per query.
    Fast: build open-addressing hash table once, O(1) per query."""

    def __init__(self):
        super().__init__("DS-1", "Data Structure",
                         "Linear Search vs Hash Lookup")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n_keys = rng.choice([1000, 2000, 5000])
        n_q = rng.choice([5000, 10000, 20000])
        ht_size = 65536    # power-of-2, mask = ht_size - 1

        slow_code = (f"int slow_ds1_{suf}(int *keys,int *vals,int n_keys,int *queries,int n_q){{\n"
                     f"    int total=0;\n"
                     f"    for(int q=0;q<n_q;q++){{\n"
                     f"        for(int i=0;i<n_keys;i++) if(keys[i]==queries[q]){{total+=vals[i];break;}}\n"
                     f"    }}\n"
                     f"    return total;\n}}")
        fast_code = (f"typedef struct{{int key,val,occ;}} HTE_{suf};\n\n"
                     f"int fast_ds1_{suf}(int *keys,int *vals,int n_keys,int *queries,int n_q){{\n"
                     f"    HTE_{suf} *ht=(HTE_{suf}*)calloc({ht_size},sizeof(HTE_{suf}));\n"
                     f"    for(int i=0;i<n_keys;i++){{\n"
                     f"        int h=(unsigned int)keys[i]&{ht_size-1};\n"
                     f"        while(ht[h].occ) h=(h+1)&{ht_size-1};\n"
                     f"        ht[h].key=keys[i];ht[h].val=vals[i];ht[h].occ=1;\n"
                     f"    }}\n"
                     f"    int total=0;\n"
                     f"    for(int q=0;q<n_q;q++){{\n"
                     f"        int h=(unsigned int)queries[q]&{ht_size-1};\n"
                     f"        while(ht[h].occ){{if(ht[h].key==queries[q]){{total+=ht[h].val;break;}}h=(h+1)&{ht_size-1};}}\n"
                     f"    }}\n"
                     f"    free(ht);\n"
                     f"    return total;\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N_KEYS {n_keys}
#define N_Q {n_q}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *keys=malloc(N_KEYS*sizeof(int)),*vals=malloc(N_KEYS*sizeof(int)),*queries=malloc(N_Q*sizeof(int));
    for(int i=0;i<N_KEYS;i++){{keys[i]=i*7+13;vals[i]=i*3+1;}}
    srand(42);
    for(int i=0;i<N_Q;i++) queries[i]=keys[rand()%N_KEYS];
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_ds1_{suf}(keys,vals,N_KEYS,queries,N_Q); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_ds1_{suf}(keys,vals,N_KEYS,queries,N_Q); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=(rs==rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(keys);free(vals);free(queries);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"DS-1_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"n_keys={n_keys}, n_q={n_q}",
                    dtype="int", difficulty="hard", compiler_fixable=False,
                    num_loops=2, num_arrays=2, lines_of_code=12,
                    expected_speedup_range="10x-1000x", composition=[]))}


# ── DS-2 ──────────────────────────────────────────────────────

class DS2_Generator(PatternTemplate):
    """DS-2: Repeated Allocation vs Pre-allocation.
    Slow: malloc/free inside loop per chunk.
    Fast: allocate once, reuse."""

    def __init__(self):
        super().__init__("DS-2", "Data Structure",
                         "Repeated Allocation vs Pre-allocation")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([1000000, 2000000, 5000000])
        chunk = rng.choice([64, 256, 1024])
        n_results = n // chunk + 1

        slow_code = (f"void slow_ds2_{suf}({dtype} *results,{dtype} *input,int n,int chunk){{\n"
                     f"    for(int i=0;i<n;i+=chunk){{\n"
                     f"        int sz=(i+chunk<=n)?chunk:(n-i);\n"
                     f"        {dtype} *tmp=({dtype}*)malloc(sz*sizeof({dtype}));\n"
                     f"        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];\n"
                     f"        {dtype} sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];\n"
                     f"        results[i/chunk]=sum;\n"
                     f"        free(tmp);\n"
                     f"    }}\n}}")
        fast_code = (f"void fast_ds2_{suf}({dtype} *results,{dtype} *input,int n,int chunk){{\n"
                     f"    {dtype} *tmp=({dtype}*)malloc(chunk*sizeof({dtype}));\n"
                     f"    for(int i=0;i<n;i+=chunk){{\n"
                     f"        int sz=(i+chunk<=n)?chunk:(n-i);\n"
                     f"        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];\n"
                     f"        {dtype} sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];\n"
                     f"        results[i/chunk]=sum;\n"
                     f"    }}\n"
                     f"    free(tmp);\n}}")
        tol = "1e-3" if dtype == "float" else "1e-8"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define CHUNK {chunk}
#define N_RES {n_results}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *input=malloc(N*sizeof({dtype})),*rs=malloc(N_RES*sizeof({dtype})),*rf=malloc(N_RES*sizeof({dtype}));
    for(int i=0;i<N;i++) input[i]=({dtype})((i%100)+1)*0.1{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_ds2_{suf}(rs,input,N,CHUNK); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_ds2_{suf}(rf,input,N,CHUNK); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N_RES;i++){{double d=fabs((double)(rs[i]-rf[i])),r=fabs((double)rs[i]);if(d>{tol}*(r+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(input);free(rs);free(rf);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"DS-2_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{dtype}, n={n}, chunk={chunk}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=2, num_arrays=1, lines_of_code=12,
                    expected_speedup_range="2x-10x", composition=[]))}


# ── DS-3 ──────────────────────────────────────────────────────

class DS3_Generator(PatternTemplate):
    """DS-3: Unnecessary Struct Copy (Pass-by-Value vs Pass-by-Pointer).
    Slow: large struct copied onto stack for every call.
    Fast: pointer passed, no copy."""

    def __init__(self):
        super().__init__("DS-3", "Data Structure",
                         "Unnecessary Struct Copy (Pass-by-Value)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        data_size = rng.choice([32, 64, 128])
        n_structs = rng.choice([200000, 500000, 1000000])
        op_type = rng.choice(["sum", "dot_self", "max"])

        if op_type == "sum":
            body_val = "double sum=0;for(int i=0;i<s.size;i++) sum+=s.data[i];return sum;"
            body_ptr = "double sum=0;for(int i=0;i<s->size;i++) sum+=s->data[i];return sum;"
        elif op_type == "dot_self":
            body_val = "double sum=0;for(int i=0;i<s.size;i++) sum+=s.data[i]*s.data[i];return sum;"
            body_ptr = "double sum=0;for(int i=0;i<s->size;i++) sum+=s->data[i]*s->data[i];return sum;"
        else:
            body_val = "double mx=s.data[0];for(int i=1;i<s.size;i++) if(s.data[i]>mx) mx=s.data[i];return mx;"
            body_ptr = "double mx=s->data[0];for(int i=1;i<s->size;i++) if(s->data[i]>mx) mx=s->data[i];return mx;"

        slow_code = (f"typedef struct{{double data[{data_size}];int size;}} BS_{suf};\n\n"
                     f"double slow_ds3_{suf}(BS_{suf} s){{{body_val}}}")
        fast_code = (f"typedef struct{{double data[{data_size}];int size;}} BS_{suf};\n\n"
                     f"double fast_ds3_{suf}(const BS_{suf} *s){{{body_ptr}}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define DATA_SIZE {data_size}
#define N_STRUCTS {n_structs}
typedef struct{{double data[DATA_SIZE];int size;}} BS_{suf};

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    BS_{suf} *arr=(BS_{suf}*)malloc(N_STRUCTS*sizeof(BS_{suf}));
    for(int i=0;i<N_STRUCTS;i++){{arr[i].size=DATA_SIZE;for(int j=0;j<DATA_SIZE;j++) arr[i].data[j]=(double)(i+j)*0.001;}}
    struct timespec t0,t1;
    double rs=0,rf=0;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int i=0;i<N_STRUCTS;i++) rs+=slow_ds3_{suf}(arr[i]);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int i=0;i<N_STRUCTS;i++) rf+=fast_ds3_{suf}(&arr[i]);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs(rs-rf),ref=fabs(rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"DS-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{op_type}, data_size={data_size}, n={n_structs}",
                    dtype="double", difficulty="medium", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=6,
                    expected_speedup_range="2x-8x", composition=[]))}


# ── AL-2 ──────────────────────────────────────────────────────

class AL2_Generator(PatternTemplate):
    """AL-2: Repeated Sort vs Sorted Insertion.
    Slow: qsort the whole array after each insertion O(n^2 log n).
    Fast: binary search + memmove to maintain sorted order O(n^2)."""

    def __init__(self):
        super().__init__("AL-2", "Algorithmic",
                         "Repeated Sort vs Sorted Insertion")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n_items = rng.choice([2000, 5000, 10000])

        slow_code = (f"static int cmp_al2_{suf}(const void *a,const void *b){{\n"
                     f"    {dtype} da=*({dtype}*)a,db=*({dtype}*)b;\n"
                     f"    return (da>db)-(da<db);\n}}\n\n"
                     f"void slow_al2_{suf}({dtype} *arr,int *sz,{dtype} *items,int n){{\n"
                     f"    *sz=0;\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        arr[(*sz)++]=items[i];\n"
                     f"        qsort(arr,*sz,sizeof({dtype}),cmp_al2_{suf});\n"
                     f"    }}\n}}")
        fast_code = (f"void fast_al2_{suf}({dtype} *arr,int *sz,{dtype} *items,int n){{\n"
                     f"    *sz=0;\n"
                     f"    for(int i=0;i<n;i++){{\n"
                     f"        {dtype} val=items[i];\n"
                     f"        int lo=0,hi=*sz;\n"
                     f"        while(lo<hi){{int mid=(lo+hi)/2;if(arr[mid]<val) lo=mid+1;else hi=mid;}}\n"
                     f"        memmove(&arr[lo+1],&arr[lo],(*sz-lo)*sizeof({dtype}));\n"
                     f"        arr[lo]=val;\n"
                     f"        (*sz)++;\n"
                     f"    }}\n}}")
        tol = "1e-5" if dtype == "float" else "1e-12"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_ITEMS {n_items}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *items=malloc(N_ITEMS*sizeof({dtype})),*as=malloc(N_ITEMS*sizeof({dtype})),*af=malloc(N_ITEMS*sizeof({dtype}));
    srand(42);
    for(int i=0;i<N_ITEMS;i++) items[i]=({dtype})(rand()%10000)*0.001{DTYPES[dtype]['suffix']};
    int szs=0,szf=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_al2_{suf}(as,&szs,items,N_ITEMS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_al2_{suf}(af,&szf,items,N_ITEMS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=(szs==szf);
    for(int i=0;i<szs&&correct;i++){{double d=fabs((double)(as[i]-af[i]));if(d>{tol}){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(items);free(as);free(af);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"AL-2_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{dtype}, n_items={n_items}",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=12,
                    expected_speedup_range="5x-50x", composition=[]))}


# ── AL-3 ──────────────────────────────────────────────────────

class AL3_Generator(PatternTemplate):
    """AL-3: Naive O(n*m) String Matching vs KMP O(n+m).
    Operates on int arrays to simulate text/pattern matching."""

    def __init__(self):
        super().__init__("AL-3", "Algorithmic",
                         "Naive vs KMP Pattern Matching")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        tn = rng.choice([5000000, 10000000])
        pn = rng.choice([6, 8, 12, 16])
        alpha = rng.choice([8, 10, 16])   # alphabet size; smaller = more matches

        slow_code = (f"int slow_al3_{suf}(int *text,int tn,int *pat,int pn){{\n"
                     f"    int count=0;\n"
                     f"    for(int i=0;i<=tn-pn;i++){{\n"
                     f"        int m=1;\n"
                     f"        for(int j=0;j<pn;j++) if(text[i+j]!=pat[j]){{m=0;break;}}\n"
                     f"        if(m) count++;\n"
                     f"    }}\n"
                     f"    return count;\n}}")
        fast_code = (f"static void build_fail_{suf}(int *pat,int pn,int *fail){{\n"
                     f"    fail[0]=0; int k=0;\n"
                     f"    for(int i=1;i<pn;i++){{\n"
                     f"        while(k>0&&pat[k]!=pat[i]) k=fail[k-1];\n"
                     f"        if(pat[k]==pat[i]) k++;\n"
                     f"        fail[i]=k;\n"
                     f"    }}\n}}\n\n"
                     f"int fast_al3_{suf}(int *text,int tn,int *pat,int pn){{\n"
                     f"    int *fail=(int*)malloc(pn*sizeof(int));\n"
                     f"    build_fail_{suf}(pat,pn,fail);\n"
                     f"    int count=0,k=0;\n"
                     f"    for(int i=0;i<tn;i++){{\n"
                     f"        while(k>0&&pat[k]!=text[i]) k=fail[k-1];\n"
                     f"        if(pat[k]==text[i]) k++;\n"
                     f"        if(k==pn){{count++;k=fail[k-1];}}\n"
                     f"    }}\n"
                     f"    free(fail);\n"
                     f"    return count;\n}}")

        # Generate a fixed pattern array literal
        pat_seed = rng.randint(0, 10000)
        pat_rng = random.Random(pat_seed)
        pat_vals = [pat_rng.randint(0, alpha - 1) for _ in range(pn)]
        pat_literal = "{" + ",".join(str(v) for v in pat_vals) + "}"

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define TN {tn}
#define PN {pn}
#define ALPHA {alpha}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *text=(int*)malloc(TN*sizeof(int));
    srand(42);
    for(int i=0;i<TN;i++) text[i]=rand()%ALPHA;
    int pat[PN]={pat_literal};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int cs=slow_al3_{suf}(text,TN,pat,PN); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int cf=fast_al3_{suf}(text,TN,pat,PN); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=(cs==cf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(text);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"AL-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"tn={tn}, pn={pn}, alpha={alpha}",
                    dtype="int", difficulty="hard", compiler_fixable=False,
                    num_loops=2, num_arrays=1, lines_of_code=14,
                    expected_speedup_range="2x-20x", composition=[]))}


# ── AL-4 ──────────────────────────────────────────────────────

class AL4_Generator(PatternTemplate):
    """AL-4: Recursive Grid Paths vs DP.
    Slow: exponential recursion. Fast: O(r*c) DP.
    Grid sizes capped to r∈[15-18], c∈[15-17] to avoid timeout."""

    def __init__(self):
        super().__init__("AL-4", "Algorithmic",
                         "Recursive vs DP (Grid Paths)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        r = rng.choice([15, 16, 17, 18])
        c = rng.choice([15, 16, 17])
        n_fast_reps = 100000

        slow_code = (f"long long slow_al4_{suf}(int r,int c){{\n"
                     f"    if(r==0||c==0) return 1;\n"
                     f"    return slow_al4_{suf}(r-1,c)+slow_al4_{suf}(r,c-1);\n}}")
        fast_code = (f"long long fast_al4_{suf}(int r,int c){{\n"
                     f"    long long *dp=(long long*)calloc(c+1,sizeof(long long));\n"
                     f"    for(int j=0;j<=c;j++) dp[j]=1;\n"
                     f"    for(int i=1;i<=r;i++) for(int j=1;j<=c;j++) dp[j]+=dp[j-1];\n"
                     f"    long long res=dp[c]; free(dp); return res;\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define GRID_R {r}
#define GRID_C {c}
#define FAST_REPS {n_fast_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); long long rs=slow_al4_{suf}(GRID_R,GRID_C); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    long long rf=0; for(int rep=0;rep<FAST_REPS;rep++) rf=fast_al4_{suf}(GRID_R,GRID_C);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/FAST_REPS;
    int correct=(rs==rf);
    printf("slow_ms=%.4f fast_ms=%.6f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"AL-4_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"grid {r}x{c}",
                    dtype="int", difficulty="hard", compiler_fixable=False,
                    num_loops=2, num_arrays=0, lines_of_code=8,
                    expected_speedup_range="1000x+", composition=[]))}


# ── MI-1 ──────────────────────────────────────────────────────

class MI1_Generator(PatternTemplate):
    """MI-1: Heap Allocation in Loop vs Sliding Window.
    Slow: malloc+free per window position. Fast: O(1) sliding window update.
    Always uses double to avoid floating-point drift."""

    def __init__(self):
        super().__init__("MI-1", "Memory & IO",
                         "Allocation in Loop vs Sliding Window")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n = rng.choice([100000, 200000, 500000])
        window = rng.choice([8, 16, 32, 64])

        slow_code = (f"double slow_mi1_{suf}(double *input,int n,int window){{\n"
                     f"    double total=0.0;\n"
                     f"    for(int i=0;i<=n-window;i++){{\n"
                     f"        double *buf=(double*)malloc(window*sizeof(double));\n"
                     f"        for(int j=0;j<window;j++) buf[j]=input[i+j];\n"
                     f"        double sum=0.0; for(int j=0;j<window;j++) sum+=buf[j];\n"
                     f"        total+=sum/window;\n"
                     f"        free(buf);\n"
                     f"    }}\n"
                     f"    return total;\n}}")
        fast_code = (f"double fast_mi1_{suf}(double *input,int n,int window){{\n"
                     f"    double total=0.0,sum=0.0;\n"
                     f"    for(int j=0;j<window;j++) sum+=input[j];\n"
                     f"    total+=sum/window;\n"
                     f"    for(int i=1;i<=n-window;i++){{\n"
                     f"        sum+=input[i+window-1]-input[i-1];\n"
                     f"        total+=sum/window;\n"
                     f"    }}\n"
                     f"    return total;\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define WINDOW {window}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *input=(double*)malloc(N*sizeof(double));
    for(int i=0;i<N;i++) input[i]=(double)((i%100)+1)*0.1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rs=slow_mi1_{suf}(input,N,WINDOW); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rf=fast_mi1_{suf}(input,N,WINDOW); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs(rs-rf),ref=fabs(rs)+1e-12;
    int correct=diff<1e-4*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(input);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"MI-1_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"n={n}, window={window}",
                    dtype="double", difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=10,
                    expected_speedup_range="5x-50x", composition=[]))}


# ── MI-2 ──────────────────────────────────────────────────────

class MI2_Generator(PatternTemplate):
    """MI-2: Redundant Memory Zeroing Before Full Overwrite.
    Slow: memset to zero then overwrite every element — dead memset.
    Fast: direct write."""

    def __init__(self):
        super().__init__("MI-2", "Memory & IO",
                         "Redundant Memory Zeroing")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([2000000, 5000000, 10000000])
        n_reps = 5
        op_type = rng.choice(["add", "mul", "fused"])
        if op_type == "add":
            expr = "A[i]+B[i]"
        elif op_type == "mul":
            expr = f"A[i]*B[i]+({dtype})1.0{DTYPES[dtype]['suffix']}"
        else:
            expr = f"A[i]*({dtype})2.0{DTYPES[dtype]['suffix']}+B[i]*({dtype})0.5{DTYPES[dtype]['suffix']}"

        slow_code = (f"void slow_mi2_{suf}({dtype} *out,{dtype} *A,{dtype} *B,int n){{\n"
                     f"    memset(out,0,n*sizeof({dtype}));\n"
                     f"    for(int i=0;i<n;i++) out[i]={expr};\n}}")
        fast_code = (f"void fast_mi2_{suf}({dtype} *out,{dtype} *A,{dtype} *B,int n){{\n"
                     f"    for(int i=0;i<n;i++) out[i]={expr};\n}}")
        tol = "1e-5" if dtype == "float" else "1e-12"
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N {n}
#define REPS {n_reps}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A=malloc(N*sizeof({dtype})),*B=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++){{A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};B[i]=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) slow_mi2_{suf}(os,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    for(int r=0;r<REPS;r++) fast_mi2_{suf}(of,A,B,N);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=((t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6)/REPS;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i]));if(d>{tol}){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"MI-2_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{op_type}, {dtype}, n={n}",
                    dtype=dtype, difficulty="medium", compiler_fixable=False,
                    num_loops=1, num_arrays=2, lines_of_code=6,
                    expected_speedup_range="1.5x-3x", composition=[]))}


# ── MI-3 ──────────────────────────────────────────────────────

class MI3_Generator(PatternTemplate):
    """MI-3: Heap Allocation in Hot Loop vs Direct Computation.
    Slow: malloc+free a small scratch buffer per iteration.
    Fast: compute directly without any allocation."""

    def __init__(self):
        super().__init__("MI-3", "Memory & IO",
                         "Heap Alloc in Hot Loop")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([1000000, 2000000, 5000000])
        quad = rng.choice([4, 8])   # scratch buffer size
        scale = rng.choice(["0.25", "0.125", "0.5"])

        slow_items = " ".join(f"buf[{j}]=data[i+{j}];" for j in range(quad))
        fast_items = "+".join(f"data[i+{j}]" for j in range(quad))

        slow_code = (f"double slow_mi3_{suf}(double *data,int n){{\n"
                     f"    double total=0.0;\n"
                     f"    for(int i=0;i<n-{quad-1};i++){{\n"
                     f"        double *buf=(double*)malloc({quad}*sizeof(double));\n"
                     f"        {slow_items}\n"
                     f"        double sum=0.0; for(int j=0;j<{quad};j++) sum+=buf[j];\n"
                     f"        total+=sum*{scale};\n"
                     f"        free(buf);\n"
                     f"    }}\n"
                     f"    return total;\n}}")
        fast_code = (f"double fast_mi3_{suf}(double *data,int n){{\n"
                     f"    double total=0.0;\n"
                     f"    for(int i=0;i<n-{quad-1};i++) total+=({fast_items})*{scale};\n"
                     f"    return total;\n}}")
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    double *data=(double*)malloc(N*sizeof(double));
    for(int i=0;i<N;i++) data[i]=(double)((i%100)+1)*0.1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rs=slow_mi3_{suf}(data,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); double rf=fast_mi3_{suf}(data,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs(rs-rf),ref=fabs(rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(data);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code, "test_code": test_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"MI-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"quad={quad}, scale={scale}, n={n}",
                    dtype="double", difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=10,
                    expected_speedup_range="5x-50x", composition=[]))}


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

        tol_val = "1e-3" if dtype == "float" else "1e-6"

        if combo == "sr3_mi4":
            rows, cols = 100, 500   # slow is O(rows^2 * cols); keep small
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
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *mat=malloc(ROWS*COLS*sizeof({dtype})),*cs=malloc(COLS*sizeof({dtype})),*cf=malloc(COLS*sizeof({dtype}));
    for(int i=0;i<ROWS*COLS;i++) mat[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_{suf}(mat,cs,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_{suf}(mat,cf,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int j=0;j<COLS;j++){{double d=fabs((double)(cs[j]-cf[j])),r=fabs((double)cs[j]);if(d>{tol_val}*(r+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(mat);free(cs);free(cf);return correct?0:1;
}}"""
            patterns = ["SR-3", "MI-4"]
            desc = f"Redundant aggregation + column-major, {dtype}"

        elif combo == "sr1_cf1":
            # SR-1: noinline scale_fn called with loop-invariant arg on every iteration
            # CF-1: batch is homogeneous (all elements share mode=0), branch can be hoisted
            # Slow: N noinline calls + per-element branch → no vectorization, massive overhead
            # Fast: hoist scale_fn once + hoist mode check before loop → SIMD-vectorizable
            n = 1000000
            helper = (f"static __attribute__((noinline)) {dtype} scale_fn_{suf}({dtype} base){{\n"
                      f"    volatile double _b=(double)base; /* block pure/const inference */\n"
                      f"    {dtype} r = 0;\n"
                      f"    for(int k=1;k<=20;k++) r+=({dtype})sin(_b*k+1.0);\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
{dtype} slow_comp_{suf}({dtype} *A, int n, {dtype} base, int mode) {{
    {dtype} total = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} s = scale_fn_{suf}(base);
        if (mode == 0) total += A[i] * s;
        else           total += A[i] * s * ({dtype})2.0{DTYPES[dtype]['suffix']};
    }}
    return total;
}}"""
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}({dtype} *A, int n, {dtype} base, int mode) {{
    {dtype} s = scale_fn_{suf}(base);
    {dtype} w = (mode == 0) ? s : s * ({dtype})2.0{DTYPES[dtype]['suffix']};
    {dtype} total = 0;
    for (int i = 0; i < n; i++) total += A[i] * w;
    return total;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++) A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
    {dtype} base=({dtype})1.5{DTYPES[dtype]['suffix']}; int mode=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(A,N,base,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(A,N,base,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);return correct?0:1;
}}"""
            patterns = ["SR-1", "CF-1"]
            desc = f"Noinline loop-invariant scale + hoistable branch, {dtype}"

        elif combo == "sr4_hr4":
            n = 1000000
            helper = (f"#include <math.h>\n#include <stdlib.h>\n"
                      f"static {dtype} config_val_{suf}(int key){{\n"
                      f"    {dtype} r=0;\n"
                      f"    for(int i=0;i<100;i++) r+=({dtype})sin((double)(key+i));\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
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
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}({dtype} *arr, int n, int key) {{
    if (arr == NULL || n <= 0) return 0;
    {dtype} factor = config_val_{suf}(key);
    {dtype} sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *arr=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++) arr[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
    int key=42;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(arr,N,key); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(arr,N,key); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);return correct?0:1;
}}"""
            patterns = ["SR-4", "HR-4"]
            desc = f"Invariant function call + defensive checks, {dtype}"

        elif combo == "ds4_cf2":
            # DS-4: AoS layout forces stride access — 16 fields * sizeof(dtype) bytes per element
            #        read to access only the 'mass' field. SoA reads only 1 field per element.
            # CF-2: always-true bounds check (i >= 0 && i < n) adds redundant work per element.
            # 16-field struct forces 2x more data per cache line than 8-field, making the
            # AoS memory bandwidth penalty reliably measurable even on Apple Silicon.
            n = 2000000
            # 32 fields: x,y,z,vx,vy,vz,mass,charge + 24 padding fields
            # Wide struct forces AoS to read 32x more data per useful value vs SoA,
            # ensuring memory bandwidth bottleneck is reliably measurable on all dtypes.
            pad = ','.join(f'p{i}' for i in range(24))
            struct_def = f"typedef struct {{ {dtype} x,y,z,vx,vy,vz,mass,charge,{pad}; }} P_{suf};"
            slow_code = f"""{struct_def}
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
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
{struct_def}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    P_{suf} *aos=(P_{suf}*)malloc(N*sizeof(P_{suf}));
    {dtype} *mass=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++){{aos[i].mass=({dtype})(i%100)*0.1{DTYPES[dtype]['suffix']};mass[i]=aos[i].mass;}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(aos,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(mass,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(aos);free(mass);return correct?0:1;
}}"""
            patterns = ["DS-4", "CF-2"]
            desc = f"Wide AoS stride access + redundant bounds, {dtype}"

        elif combo == "sr2_hr1":
            # SR-2: penalty(alpha,beta) is loop-invariant but noinline — compiler can't hoist
            # HR-1: redundant temp decomposition (t1..t4) in slow — trivially removed by compiler,
            #        but the N penalty() calls dominate and are the real bottleneck
            # Slow: N noinline sin*exp calls + decomposed temps
            # Fast: hoist penalty once, separate accumulators, direct loop
            n = 200000 if dtype == "float" else 1000000
            helper = (f"static __attribute__((noinline)) double penalty_{suf}(double a, double b){{\n"
                      f"    volatile double _a=a,_b=b; /* block pure/const inference */\n"
                      f"    double r = 0.0;\n"
                      f"    for(int k=1;k<=20;k++) r+=sin(_a*k)*exp(-_b*k*0.05);\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
{dtype} slow_comp_{suf}({dtype} *X, {dtype} *Y, int n, {dtype} alpha, {dtype} beta) {{
    {dtype} result = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} t1 = X[i] * X[i];
        {dtype} t2 = alpha * t1;
        {dtype} t3 = beta * Y[i];
        {dtype} t4 = t2 + t3;
        {dtype} pen = ({dtype})penalty_{suf}((double)alpha, (double)beta);
        result += t4 + pen;
    }}
    return result;
}}"""
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}({dtype} *X, {dtype} *Y, int n, {dtype} alpha, {dtype} beta) {{
    {dtype} pen = ({dtype})penalty_{suf}((double)alpha, (double)beta);
    {dtype} sumXsq = 0, sumY = 0;
    for (int i = 0; i < n; i++) {{
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }}
    return alpha * sumXsq + beta * sumY + ({dtype})n * pen;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *X=malloc(N*sizeof({dtype})),*Y=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++){{X[i]=({dtype})((i%200)-100)*0.01{DTYPES[dtype]['suffix']};Y[i]=({dtype})((i%100)-50)*0.02{DTYPES[dtype]['suffix']};}}
    {dtype} alpha=({dtype})2.5{DTYPES[dtype]['suffix']},beta=({dtype})1.5{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(X,Y,N,alpha,beta); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(X,Y,N,alpha,beta); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(X);free(Y);return correct?0:1;
}}"""
            patterns = ["SR-2", "HR-1"]
            desc = f"Noinline penalty + temp decomposition, {dtype}"

        elif combo == "cf1_mi4":
            rows, cols = 3000, 3000
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
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int total=ROWS*COLS;
    {dtype} *ms=malloc(total*sizeof({dtype})),*mf=malloc(total*sizeof({dtype}));
    for(int k=0;k<total;k++) ms[k]=({dtype})((k%100)+1)*0.1{DTYPES[dtype]['suffix']};
    memcpy(mf,ms,total*sizeof({dtype}));
    int mode=1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_{suf}(ms,ROWS,COLS,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_{suf}(mf,ROWS,COLS,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int k=0;k<total;k++){{double d=fabs((double)(ms[k]-mf[k]));if(d>1e-6){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(ms);free(mf);return correct?0:1;
}}"""
            patterns = ["CF-1", "MI-4"]
            desc = f"Hoistable branch + column-major access, {dtype}"

        elif combo == "sr1_sr2_cf2":
            # SR-1: log_scale(base) is noinline, called per element with loop-invariant arg
            # SR-2: k=log_scale result is a loop-invariant multiplier — factor out of inner ops
            # CF-2: always-true bounds check (i>=0 && i<rows && j>=0 && j<cols) → hoist/remove
            # Slow: N noinline log_scale calls + always-true bounds check + temp decomposition
            # Fast: hoist log_scale once, remove bounds check, separate accumulators
            rows, cols = 500, 1000
            helper = (f"static __attribute__((noinline)) {dtype} log_scale_{suf}({dtype} base){{\n"
                      f"    volatile double _b=(double)base; /* block pure/const inference */\n"
                      f"    {dtype} r = 0;\n"
                      f"    for(int k=1;k<=15;k++) r+=({dtype})(log(_b*k+1.0)/k);\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
{dtype} slow_comp_{suf}({dtype} *A, {dtype} *B, int rows, int cols, {dtype} base) {{
    {dtype} result = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if (i >= 0 && i < rows && j >= 0 && j < cols) {{
                {dtype} scale = log_scale_{suf}(base);
                {dtype} t1 = A[i*cols+j] * A[i*cols+j];
                {dtype} t2 = scale * t1;
                {dtype} t3 = B[i*cols+j] * scale;
                result += t2 + t3;
            }}
        }}
    }}
    return result;
}}"""
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}({dtype} *A, {dtype} *B, int rows, int cols, {dtype} base) {{
    {dtype} scale = log_scale_{suf}(base);
    {dtype} sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }}
    }}
    return scale * sumAsq + scale * sumB;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int total=ROWS*COLS;
    {dtype} *A=malloc(total*sizeof({dtype})),*B=malloc(total*sizeof({dtype}));
    for(int i=0;i<total;i++){{A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};B[i]=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};}}
    {dtype} base=({dtype})2.0{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(A,B,ROWS,COLS,base); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(A,B,ROWS,COLS,base); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);return correct?0:1;
}}"""
            patterns = ["SR-1", "SR-2", "CF-2"]
            desc = f"Noinline log-scale + bounds check + temps, {dtype}"

        elif combo == "hr1_cf2_mi4":
            rows, cols = 2000, 2500
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
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int total=ROWS*COLS;
    {dtype} *A=malloc(total*sizeof({dtype})),*B=malloc(total*sizeof({dtype})),*os=malloc(total*sizeof({dtype})),*of=malloc(total*sizeof({dtype}));
    for(int i=0;i<total;i++){{A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};B[i]=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_{suf}(os,A,B,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_{suf}(of,A,B,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<total;i++){{double d=fabs((double)(os[i]-of[i]));if(d>1e-6){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);free(os);free(of);return correct?0:1;
}}"""
            patterns = ["HR-1", "CF-2", "MI-4"]
            desc = f"Triple: temps + bounds + cache, {dtype}"

        else:  # sr4_cf1_hr1
            n = 5000000
            helper = (f"#include <math.h>\n"
                      f"static __attribute__((noinline)) {dtype} compute_{suf}(int key){{\n"
                      f"    volatile double _k=(double)key; /* block pure/const inference */\n"
                      f"    {dtype} r=0;\n"
                      f"    for(int i=0;i<50;i++) r+=({dtype})sin(_k+(double)i);\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
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
            fast_code = f"""{helper}
void fast_comp_{suf}({dtype} *out, {dtype} *A, int n, int key, int mode) {{
    {dtype} factor = compute_{suf}(key);
    if (mode == 1) {{
        for (int i = 0; i < n; i++) out[i] = A[i] * factor + ({dtype})1.0;
    }} else {{
        for (int i = 0; i < n; i++) out[i] = A[i] + factor + ({dtype})1.0;
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A=malloc(N*sizeof({dtype})),*os=malloc(N*sizeof({dtype})),*of=malloc(N*sizeof({dtype}));
    for(int i=0;i<N;i++) A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
    int key=42,mode=1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_{suf}(os,A,N,key,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_{suf}(of,A,N,key,mode); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int i=0;i<N;i++){{double d=fabs((double)(os[i]-of[i]));if(d>{tol_val}*(fabs((double)os[i])+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(os);free(of);return correct?0:1;
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
            "test_code": test_code,
            "metadata": asdict(metadata)
        }

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
