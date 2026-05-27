"""Semantic Redundancy (SR-1..SR-5) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, VariantMetadata


class SR1_Generator(PatternTemplate):
    """SR-1: Loop-Invariant Semantic Computation (Form A — noinline hoist)
    Slow: calls an expensive noinline function (in helper.c) with loop-invariant
          arguments INSIDE the loop — the call happens every iteration.
    Fast: hoists the invariant call outside the loop, calls it once.

    Compiler-resistance: the expensive function lives in helper.c (separate TU)
    and is __attribute__((noinline)), so the compiler cannot inline or
    constant-fold it away.

    Varies: function complexity, number of invariant calls,
    function type (trig, hash, polynomial, sqrt, exp_chain, power_tower, log_sum),
    work amount, dtype, loop style, array operation (+= vs *=)
    """

    def __init__(self):
        super().__init__("SR-1", "Semantic Redundancy",
                         "Loop-Invariant Semantic Computation")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        dtype = rng.choice(["float", "double"])
        fn_type = rng.choice(["trig_combo", "polynomial", "hash_chain", "nested_sqrt",
                               "exp_chain", "power_tower", "log_sum"])
        n_calls = rng.randint(1, 4)  # 1-4 invariant function calls
        loop_style = rng.choice(["for", "while", "for"])
        arr_op = rng.choice(["*=", "+=", "*="])

        fn_bodies = {
            "trig_combo": """{dtype} expensive_sr1_{suf}(int key) {{
    {dtype} r = {zero};
    for (int i = 0; i < {work}; i++)
        r += sin(({dtype})(key + i)) * cos(({dtype})(key - i));
    return r;
}}""",
            "polynomial": """{dtype} expensive_sr1_{suf}(int key) {{
    {dtype} x = ({dtype})key * 0.001{suffix};
    {dtype} r = {zero};
    for (int i = 0; i < {work}; i++) {{
        r += x * x * x - 3.0{suffix} * x * x + 2.0{suffix} * x - 1.0{suffix};
        x += 0.0001{suffix};
    }}
    return r;
}}""",
            "hash_chain": """{dtype} expensive_sr1_{suf}(int key) {{
    unsigned int h = (unsigned int)key;
    {dtype} r = {zero};
    for (int i = 0; i < {work}; i++) {{
        h = h * 2654435761u;
        r += ({dtype})(h & 0xFFFF) / 65536.0{suffix};
    }}
    return r / {work};
}}""",
            "nested_sqrt": """{dtype} expensive_sr1_{suf}(int key) {{
    {dtype} r = fabs(({dtype})key) + 1.0{suffix};
    for (int i = 0; i < {work}; i++) r = sqrt(r + ({dtype})i);
    return r;
}}""",
            "exp_chain": """{dtype} expensive_sr1_{suf}(int key) {{
    {dtype} r = 1.0{suffix};
    for (int i = 0; i < {work}; i++) {{
        r = exp(-fabs(r * 0.01{suffix})) + ({dtype})(key % (i+1));
    }}
    return r;
}}""",
            "power_tower": """{dtype} expensive_sr1_{suf}(int key) {{
    {dtype} base = 1.0{suffix} + ({dtype})(key % 10) * 0.01{suffix};
    {dtype} r = base;
    for (int i = 0; i < {work}; i++) r = pow(base, r * 0.01{suffix});
    return r;
}}""",
            "log_sum": """{dtype} expensive_sr1_{suf}(int key) {{
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

        # ── helper.c: noinline expensive function in separate TU ──
        helper_code = f"""#include <math.h>

__attribute__((noinline))
{fn_code}
"""

        # Build slow: call(s) inside loop
        call_lines_slow = []
        call_lines_fast = []
        combine_terms = []
        for c in range(n_calls):
            key_param = f"key{c}" if n_calls > 1 else "key"
            call_lines_slow.append(
                f"        {dtype} f{c} = expensive_sr1_{suf}({key_param});"
            )
            call_lines_fast.append(
                f"    {dtype} f{c} = expensive_sr1_{suf}({key_param});"
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

        # Declare the external helper function
        fn_decl = f"{dtype} expensive_sr1_{suf}(int key);"

        slow_code = f"""{fn_decl}

void slow_sr1_{suf}({dtype} *arr, int n, {key_params}) {{
{loop_open_slow}
{chr(10).join(call_lines_slow)}
        arr[i] {arr_op} {combine_expr};
{loop_close_slow}
}}"""

        fast_code = f"""{fn_decl}

void fast_sr1_{suf}({dtype} *arr, int n, {key_params}) {{
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
    slow_sr1_{suf}(arr_slow, N, {key_args});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_sr1_{suf}(arr_fast, N, {key_args});
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
            variant_id=f"{self.pattern_id}_v{variant_num:03d}",
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


class SR2_Generator(PatternTemplate):
    """SR-2: Loop-Invariant Penalty/Weight in Compound Expression.
    An expensive noinline function with loop-invariant args is called every iteration
    inside a compound expression. The fix hoists the call outside the loop."""

    def __init__(self):
        super().__init__("SR-2", "Semantic Redundancy",
                         "Loop-Invariant Penalty in Compound Expression")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n_arrays = rng.choice([2, 3])
        N = rng.choice([5000000, 10000000])
        loop_style = rng.choice(["for", "while"])
        zero = DTYPES[dtype]['zero']
        suffix = DTYPES[dtype]['suffix']

        # Expensive function type
        fn_type = rng.choice(["trig_sum", "polynomial", "log_chain", "sqrt_chain"])
        if fn_type == "trig_sum":
            fn_body = f"""    volatile {dtype} _a=({dtype})a, _b=({dtype})b;
    {dtype} r = {zero};
    for(int k=1;k<=30;k++) r+=({dtype})sin(_a*({dtype})k)+({dtype})cos(_b*({dtype})k);
    return r/30.0{suffix};"""
        elif fn_type == "polynomial":
            fn_body = f"""    volatile {dtype} _a=({dtype})a, _b=({dtype})b;
    {dtype} r = {zero};
    for(int k=0;k<40;k++) {{ r = r*_a*0.1{suffix} + _b; r = r*_b*0.1{suffix} + _a; }}
    return r;"""
        elif fn_type == "log_chain":
            fn_body = f"""    volatile {dtype} _a=({dtype})a, _b=({dtype})b;
    {dtype} r = ({dtype})fabs(_a) + 1.0{suffix};
    for(int k=0;k<20;k++) r = ({dtype})log(r + ({dtype})fabs(_b) + 1.0{suffix});
    return r;"""
        else:
            fn_body = f"""    volatile {dtype} _a=({dtype})a, _b=({dtype})b;
    {dtype} r = ({dtype})fabs(_a) + ({dtype})fabs(_b) + 1.0{suffix};
    for(int k=0;k<25;k++) r = ({dtype})sqrt(r) + 0.5{suffix};
    return r;"""

        helper_code = f"""#include <math.h>
__attribute__((noinline))
{dtype} penalty_sr2_{suf}({dtype} a, {dtype} b) {{
{fn_body}
}}
"""

        arr_names = ["X", "Y", "Z"][:n_arrays]
        arr_params = ", ".join(f"{dtype} *{a}" for a in arr_names)
        all_params = f"{arr_params}, int n, {dtype} alpha, {dtype} beta"

        # Build the per-element expression using arrays
        data_terms = []
        for arr in arr_names:
            data_terms.append(f"alpha * {arr}[i]")
        data_expr = " + ".join(data_terms)

        loop_open = "for (int i = 0; i < n; i++)" if loop_style == "for" else "int i = 0;\n    while (i < n)"
        loop_inc = "" if loop_style == "for" else "\n        i++;"

        slow_code = f"""{dtype} penalty_sr2_{suf}({dtype} a, {dtype} b);

{dtype} slow_sr2_{suf}({all_params}) {{
    {dtype} result = {zero};
    {loop_open} {{
        result += {data_expr} + penalty_sr2_{suf}(alpha, beta);{loop_inc}
    }}
    return result;
}}"""

        fast_code = f"""{dtype} penalty_sr2_{suf}({dtype} a, {dtype} b);

{dtype} fast_sr2_{suf}({all_params}) {{
    {dtype} p = penalty_sr2_{suf}(alpha, beta);
    {dtype} result = {zero};
    {loop_open} {{
        result += {data_expr};{loop_inc}
    }}
    return result + ({dtype})n * p;
}}"""

        arr_args = ", ".join(arr_names)
        arr_allocs = "\n".join(
            f"    {dtype} *{a} = malloc(N * sizeof({dtype}));\n"
            f"    for (int k = 0; k < N; k++) {a}[k] = ({dtype})(k % 100) * 0.01{suffix};"
            for a in arr_names
        )
        arr_frees = "\n".join(f"    free({a});" for a in arr_names)

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N {N}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
{arr_allocs}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_slow = slow_sr2_{suf}({arr_args}, N, 2.5{suffix}, 1.7{suffix});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_fast = fast_sr2_{suf}({arr_args}, N, 2.5{suffix}, 1.7{suffix});
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)(r_slow - r_fast));
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < {"1e-2" if dtype == "float" else "1e-4"}) || (diff < 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

{arr_frees}
    return 0;
}}"""

        desc = f"{n_arrays} arrays, penalty ({fn_type}), {dtype}, {loop_style}-loop"
        metadata = VariantMetadata(
            pattern_id=self.pattern_id,
            variant_id=f"SR-2_v{variant_num:03d}",
            category=self.category,
            pattern_name=self.name,
            variant_desc=desc,
            dtype=dtype,
            difficulty="medium" if fn_type in ("trig_sum", "polynomial") else "easy",
            compiler_fixable=False,
            num_loops=1,
            num_arrays=n_arrays,
            lines_of_code=8,
            expected_speedup_range="10x-1000x",
            composition=[]
        )

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "helper_code": helper_code,
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
