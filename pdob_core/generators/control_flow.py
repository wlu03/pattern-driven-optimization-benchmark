"""Control Flow (CF-1..CF-4) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, VariantMetadata


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
