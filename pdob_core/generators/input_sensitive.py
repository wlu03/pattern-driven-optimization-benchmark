"""Input-Sensitive Inefficiency (IS-1..IS-5) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, VariantMetadata


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
        # Only use layouts where zero-skip saves an inner loop's worth of
        # work (quadratic or cubic).  Linear operations (elemwise, dot,
        # saxpy) are too simple: the branch prevents SIMD vectorisation
        # and costs more than the multiply it skips.
        layout = rng.choice(["matmul", "matvec", "outer_product"])
        # Sparsity must be high enough that zero-skip guards are beneficial.
        if layout == "matmul":
            sparsity = rng.choice([0.9, 0.95, 0.99])
        elif layout == "outer_product":
            sparsity = rng.choice([0.95, 0.99])
        else:  # matvec
            sparsity = 0.99
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
            desc = f"Sparse matrix-matrix multiply ({sparsity*100:.1f}% zeros), skip zero elements"

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
            desc = f"Sparse matrix-vector multiply ({sparsity*100:.1f}% zeros), skip zero elements"

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
            desc = f"Sparse element-wise {op} ({sparsity*100:.1f}% zeros)"

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
            desc = f"Sparse dot product ({sparsity*100:.1f}% zeros), skip zero pairs"

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
            desc = f"Sparse SAXPY ({sparsity*100:.1f}% zeros in x), skip zero entries"

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
            desc = f"Sparse outer product ({sparsity*100:.1f}% zeros), skip zero rows/cols"

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
            difficulty="hard" if layout == "matmul" else "medium",
            compiler_fixable=False,
            num_loops=3 if layout == "matmul" else 2,
            num_arrays=3,
            lines_of_code=10,
            expected_speedup_range=f"{1/(1-sparsity):.0f}x",
            composition=[]
        )

        # Build proper test harness based on layout
        if layout == "matmul":
            dim = 300
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define M {dim}
#define K {dim}
#define NN {dim}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A = malloc(M * K * sizeof({dtype}));
    {dtype} *B = malloc(K * NN * sizeof({dtype}));
    {dtype} *C_slow = calloc(M * NN, sizeof({dtype}));
    {dtype} *C_fast = calloc(M * NN, sizeof({dtype}));
    srand(42);
    for (int i = 0; i < M * K; i++) A[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
    for (int i = 0; i < K * NN; i++) B[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_{suf}(C_slow, A, B, M, K, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_{suf}(C_fast, A, B, M, K, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < M * NN; i++) {{
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(C_slow); free(C_fast);
    return 0;
}}"""
        elif layout == "matvec":
            m_dim = 3000
            n_dim = 3000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define M {m_dim}
#define NN {n_dim}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A = malloc(M * NN * sizeof({dtype}));
    {dtype} *x = malloc(NN * sizeof({dtype}));
    {dtype} *y_slow = calloc(M, sizeof({dtype}));
    {dtype} *y_fast = calloc(M, sizeof({dtype}));
    srand(42);
    for (int i = 0; i < M * NN; i++) A[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
    for (int i = 0; i < NN; i++) x[i] = ({dtype})(rand() % 10 + 1) * 0.1{suffix};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_{suf}(y_slow, A, x, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_{suf}(y_fast, A, x, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < M; i++) {{
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(x); free(y_slow); free(y_fast);
    return 0;
}}"""
        elif layout == "elemwise":
            n_elem = 10000000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N {n_elem}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A = malloc(N * sizeof({dtype}));
    {dtype} *B = malloc(N * sizeof({dtype}));
    {dtype} *out_slow = malloc(N * sizeof({dtype}));
    {dtype} *out_fast = malloc(N * sizeof({dtype}));
    srand(42);
    for (int i = 0; i < N; i++) {{
        A[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
        B[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
    }}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_{suf}(out_slow, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_{suf}(out_fast, A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(out_slow[i] - out_fast[i])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(out_slow); free(out_fast);
    return 0;
}}"""
        elif layout == "dot_product":
            n_elem = 10000000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N {n_elem}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *A = malloc(N * sizeof({dtype}));
    {dtype} *B = malloc(N * sizeof({dtype}));
    srand(42);
    for (int i = 0; i < N; i++) {{
        A[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
        B[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
    }}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_slow = slow_is1_{suf}(A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_fast = fast_is1_{suf}(A, B, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)(r_slow - r_fast));
    double mag = fmax(fabs((double)r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B);
    return 0;
}}"""
        elif layout == "saxpy":
            n_elem = 10000000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N {n_elem}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *x = malloc(N * sizeof({dtype}));
    {dtype} *y_slow = malloc(N * sizeof({dtype}));
    {dtype} *y_fast = malloc(N * sizeof({dtype}));
    srand(42);
    for (int i = 0; i < N; i++) {{
        x[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
        y_slow[i] = ({dtype})(i % 50) * 0.01{suffix};
    }}
    memcpy(y_fast, y_slow, N * sizeof({dtype}));
    {dtype} alpha = 2.5{suffix};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_{suf}(y_slow, x, alpha, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_{suf}(y_fast, x, alpha, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < N; i++) {{
        if (fabs((double)(y_slow[i] - y_fast[i])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(x); free(y_slow); free(y_fast);
    return 0;
}}"""
        else:  # outer_product
            m_dim = 3000
            n_dim = 3000
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define M {m_dim}
#define NN {n_dim}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *a = malloc(M * sizeof({dtype}));
    {dtype} *b = malloc(NN * sizeof({dtype}));
    {dtype} *C_slow = calloc(M * NN, sizeof({dtype}));
    {dtype} *C_fast = calloc(M * NN, sizeof({dtype}));
    srand(42);
    for (int i = 0; i < M; i++) a[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};
    for (int i = 0; i < NN; i++) b[i] = (rand() % 1000 < {int(sparsity*1000)}) ? {zero} : ({dtype})(rand() % 10 + 1) * 0.1{suffix};

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_is1_{suf}(C_slow, a, b, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_is1_{suf}(C_fast, a, b, M, NN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int i = 0; i < M * NN; i++) {{
        if (fabs((double)(C_slow[i] - C_fast[i])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(a); free(b); free(C_slow); free(C_fast);
    return 0;
}}"""

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


# ── IS-2 ──────────────────────────────────────────────────────

class IS2_Generator(PatternTemplate):
    """IS-2: Data Distribution Skew.
    Slow: always calls noinline expensive transform for EVERY element.
    Fast: cheap fabs check first; only calls expensive helper for ~1% outliers.

    Compiler-resistance strategy:
    - helper.c contains noinline expensive_transform compiled as a separate TU,
      preventing the compiler from inlining or simplifying the math.
    - volatile inside the helper blocks constant folding and dead code elimination.
    - Slow code calls the expensive helper unconditionally; fast code branches first.
    """

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
            t_body = f"result = sign*((volatile {dtype}){threshold}+({dtype})log(1.0+vabs-(volatile {dtype}){threshold}));"
        elif transform == "sqrt_offset":
            t_body = f"result = sign*((volatile {dtype}){threshold}+({dtype})sqrt((double)(vabs-(volatile {dtype}){threshold})));"
        else:
            t_body = f"result = sign*((volatile {dtype}){threshold}*(1.0+({dtype})exp((double)(vabs-(volatile {dtype}){threshold})-1.0)));"

        # ── helper.c: noinline expensive transform in separate TU ──
        helper_code = (
            f"#include <math.h>\n\n"
            f"__attribute__((noinline))\n"
            f"{dtype} is2_expensive_{suf}({dtype} val, {dtype} thr){{\n"
            f"    volatile {dtype} vval = val;\n"
            f"    volatile {dtype} vthr = thr;\n"
            f"    {dtype} sign = (vval >= 0) ? ({dtype})1.0 : ({dtype})-1.0;\n"
            f"    {dtype} vabs = ({dtype})fabs((double)vval);\n"
            f"    {dtype} result;\n"
            f"    if(vabs > vthr){{\n"
            f"        {t_body}\n"
            f"    }} else {{\n"
            f"        result = vval;\n"
            f"    }}\n"
            f"    volatile {dtype} vresult = result;\n"
            f"    return ({dtype})vresult;\n"
            f"}}\n"
        )

        # ── slow.c: call expensive helper for EVERY element unconditionally ──
        slow_code = (
            f"#include <math.h>\n"
            f"{dtype} is2_expensive_{suf}({dtype} val, {dtype} thr);\n\n"
            f"void slow_is2_{suf}({dtype} *out,{dtype} *in,int n,{dtype} thr){{\n"
            f"    for(int i=0;i<n;i++){{\n"
            f"        out[i]=is2_expensive_{suf}(in[i],thr);\n"
            f"    }}\n}}"
        )
        # ── fast.c: only call expensive helper for outliers (~1%) ──
        fast_code = (
            f"#include <math.h>\n"
            f"{dtype} is2_expensive_{suf}({dtype} val, {dtype} thr);\n\n"
            f"void fast_is2_{suf}({dtype} *out,{dtype} *in,int n,{dtype} thr){{\n"
            f"    for(int i=0;i<n;i++){{\n"
            f"        {dtype} val=in[i];\n"
            f"        if(({dtype})fabs((double)val)<=thr){{out[i]=val;}}\n"
            f"        else{{out[i]=is2_expensive_{suf}(val,thr);}}\n"
            f"    }}\n}}"
        )
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
                "helper_code": helper_code,
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
    Slow: calls noinline kernel WITHOUT restrict from helper.c — compiler
          generates conservative (no-vectorize) code.
    Fast: runtime non-overlap check dispatches to a SEPARATE noinline
          __restrict__-qualified kernel from helper.c.

    Compiler-resistance: both kernels are noinline in helper.c (separate TU),
    so the compiler cannot inline or apply alias analysis across TU boundary."""

    def __init__(self):
        super().__init__("IS-5", "Input-Sensitive Inefficiency",
                         "Runtime Alias Check for Restrict Fast-Path")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        sf = DTYPES[dtype]['suffix']
        n = rng.choice([50000000, 60000000, 80000000])
        n_reps = 3

        # The slow kernel reads back from out[] after each write, creating a
        # true read-after-write dependency that prevents vectorization even
        # when the compiler might otherwise try.  The fast (restrict) kernel
        # does the identical arithmetic but the __restrict__ qualifier tells
        # the compiler A/B never alias out, enabling full SIMD.
        expr_type = rng.choice(["quadratic", "linear_combo", "fused"])

        # Slow body: write out[i], then read it back to create a serial dependency.
        # This forces the compiler to emit scalar code even at -O3.
        if expr_type == "quadratic":
            slow_body = (
                f"out[i] = A[i]*A[i] + B[i]*2.0{sf};\n"
                f"            out[i] = out[i] - A[i]*0.5{sf} + B[i]*B[i] + out[i]*0.001{sf};"
            )
            fast_body = (
                f"{dtype} t = A[i]*A[i] + B[i]*2.0{sf};\n"
                f"            out[i] = t - A[i]*0.5{sf} + B[i]*B[i] + t*0.001{sf};"
            )
        elif expr_type == "linear_combo":
            slow_body = (
                f"out[i] = A[i]*1.5{sf} + B[i]*2.5{sf};\n"
                f"            out[i] = out[i] - A[i]*B[i]*0.1{sf} + out[i]*0.001{sf};"
            )
            fast_body = (
                f"{dtype} t = A[i]*1.5{sf} + B[i]*2.5{sf};\n"
                f"            out[i] = t - A[i]*B[i]*0.1{sf} + t*0.001{sf};"
            )
        else:
            slow_body = (
                f"out[i] = A[i]*A[i] - B[i]*B[i];\n"
                f"            out[i] = out[i] + A[i]*B[i]*0.5{sf} + 1.0{sf} + out[i]*0.001{sf};"
            )
            fast_body = (
                f"{dtype} t = A[i]*A[i] - B[i]*B[i];\n"
                f"            out[i] = t + A[i]*B[i]*0.5{sf} + 1.0{sf} + t*0.001{sf};"
            )

        # ── helper.c: TWO noinline kernels in separate TU ──
        # 1) is5_noalias_kernel — WITHOUT restrict, reads back from out[]
        #    creating a store-load dependency the compiler cannot vectorize
        # 2) is5_restrict_kernel — WITH restrict, uses local temp variable
        #    so the compiler can vectorize freely
        helper_code = (
            f"__attribute__((noinline))\n"
            f"void is5_noalias_kernel_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{\n"
            f"    for (int i = 0; i < n; i++) {{\n"
            f"            {slow_body}\n"
            f"    }}\n"
            f"}}\n\n"
            f"__attribute__((noinline))\n"
            f"void is5_restrict_kernel_{suf}({dtype} * __restrict__ out,\n"
            f"        const {dtype} * __restrict__ A,\n"
            f"        const {dtype} * __restrict__ B, int n) {{\n"
            f"    for (int i = 0; i < n; i++) {{\n"
            f"            {fast_body}\n"
            f"    }}\n"
            f"}}\n"
        )

        # ── slow.c: always calls the non-restrict kernel ──
        slow_code = (
            f"void is5_noalias_kernel_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n);\n\n"
            f"void slow_is5_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{\n"
            f"    is5_noalias_kernel_{suf}(out, A, B, n);\n"
            f"}}"
        )

        # ── fast.c: runtime overlap check, then calls restrict kernel ──
        fast_code = (
            f"void is5_noalias_kernel_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n);\n"
            f"void is5_restrict_kernel_{suf}({dtype} * __restrict__ out,\n"
            f"        const {dtype} * __restrict__ A,\n"
            f"        const {dtype} * __restrict__ B, int n);\n\n"
            f"void fast_is5_{suf}({dtype} *out, {dtype} *A, {dtype} *B, int n) {{\n"
            f"    int ok = (out + n <= A || A + n <= out) &&\n"
            f"            (out + n <= B || B + n <= out);\n"
            f"    if (ok) is5_restrict_kernel_{suf}(out, A, B, n);\n"
            f"    else    is5_noalias_kernel_{suf}(out, A, B, n);\n"
            f"}}"
        )

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
    for(int i=0;i<N;i++){{A[i]=({dtype})((i%100)+1)*0.1{sf};B[i]=({dtype})((i%50)+1)*0.05{sf};}}
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
                "helper_code": helper_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"IS-5_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"{expr_type} expr, {dtype}, n={n}, alias-dep slow",
                    dtype=dtype, difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=2, lines_of_code=10,
                    expected_speedup_range="2x-6x", composition=[]))}
