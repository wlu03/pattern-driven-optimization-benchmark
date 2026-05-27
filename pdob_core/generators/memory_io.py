"""Memory & IO (MI-1..MI-4) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.

MI-4 also imports UNARY_MATH_FNS.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, UNARY_MATH_FNS, VariantMetadata


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
    Slow: memset to zero via noinline helper in separate TU, then overwrite.
    Fast: direct write without zeroing.

    Compiler-resistance strategy:
    - helper.c contains a noinline zero_buffer function compiled as a separate
      TU, preventing the compiler from performing dead store elimination across
      the TU boundary (it cannot see that the memset is followed by a full
      overwrite).
    - The slow function calls zero_buffer then overwrites — the compiler in
      slow.c's TU sees a function call whose side effects it cannot analyse.
    """

    def __init__(self):
        super().__init__("MI-2", "Memory & IO",
                         "Redundant Memory Zeroing")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([5000000, 10000000, 20000000])
        n_reps = 5
        op_type = rng.choice(["add", "mul", "fused"])
        if op_type == "add":
            expr = "A[i]+B[i]"
        elif op_type == "mul":
            expr = f"A[i]*B[i]+({dtype})1.0{DTYPES[dtype]['suffix']}"
        else:
            expr = f"A[i]*({dtype})2.0{DTYPES[dtype]['suffix']}+B[i]*({dtype})0.5{DTYPES[dtype]['suffix']}"

        # ── helper.c: noinline zero_buffer in separate TU ──
        helper_code = (
            f"#include <string.h>\n\n"
            f"__attribute__((noinline))\n"
            f"void mi2_zero_{suf}(void *p, int n){{\n"
            f"    volatile char *vp = (volatile char*)p;\n"
            f"    memset((void*)vp, 0, n);\n"
            f"}}\n"
        )

        # ── slow.c: 3-pass staging with 2 intermediate buffers ──
        # Pass 1: zero out + compute into tmp1
        # Pass 2: zero out + copy from tmp1 into tmp2 with scaling
        # Pass 3: zero out + write final result from tmp2
        # This creates ~3× more DRAM bandwidth than the single-pass fast version.
        slow_code = (
            f"#include <stdlib.h>\n"
            f"void mi2_zero_{suf}(void *p, int n);\n\n"
            f"void slow_mi2_{suf}({dtype} *out,{dtype} *A,{dtype} *B,int n){{\n"
            f"    {dtype} *s1=({dtype}*)malloc(n*sizeof({dtype}));\n"
            f"    {dtype} *s2=({dtype}*)malloc(n*sizeof({dtype}));\n"
            f"    mi2_zero_{suf}(s1, n*(int)sizeof({dtype}));\n"
            f"    for(int i=0;i<n;i++) s1[i]={expr};\n"
            f"    mi2_zero_{suf}(s2, n*(int)sizeof({dtype}));\n"
            f"    for(int i=0;i<n;i++) s2[i]=s1[i];\n"
            f"    mi2_zero_{suf}(out, n*(int)sizeof({dtype}));\n"
            f"    for(int i=0;i<n;i++) out[i]=s2[i];\n"
            f"    free(s1); free(s2);\n"
            f"}}\n"
        )

        fast_code = (f"void fast_mi2_{suf}({dtype} *out,{dtype} *A,{dtype} *B,int n){{\n"
                     f"    for(int i=0;i<n;i++) out[i]={expr};\n}}\n")
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
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "helper_code": helper_code,
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
    Slow: calls noinline alloc/free helpers per iteration.
    Fast: compute directly without any allocation.

    Compiler-resistance strategy:
    - helper.c contains noinline alloc/free functions compiled as a separate TU,
      preventing the compiler from converting malloc to stack alloc.
    - volatile pointers inside helpers block dead store elimination.
    - Same approach as DS-2.
    """

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

        # ── helper.c: noinline alloc/free in separate TU ──
        helper_code = (
            f"#include <stdlib.h>\n\n"
            f"__attribute__((noinline))\n"
            f"void* mi3_alloc_{suf}(int n){{\n"
            f"    volatile void *p = malloc(n);\n"
            f"    return (void*)p;\n"
            f"}}\n\n"
            f"__attribute__((noinline))\n"
            f"void mi3_free_{suf}(void *p){{\n"
            f"    volatile void *vp = p;\n"
            f"    free((void*)vp);\n"
            f"}}\n"
        )

        # ── slow.c: declare extern helpers, malloc/free per iteration ──
        slow_code = (
            f"#include <stdlib.h>\n"
            f"void* mi3_alloc_{suf}(int n);\n"
            f"void mi3_free_{suf}(void *p);\n\n"
            f"double slow_mi3_{suf}(double *data,int n){{\n"
            f"    double total=0.0;\n"
            f"    for(int i=0;i<n-{quad-1};i++){{\n"
            f"        double *buf=(double*)mi3_alloc_{suf}({quad}*(int)sizeof(double));\n"
            f"        {slow_items}\n"
            f"        double sum=0.0; for(int j=0;j<{quad};j++) sum+=buf[j];\n"
            f"        total+=sum*{scale};\n"
            f"        mi3_free_{suf}(buf);\n"
            f"    }}\n"
            f"    return total;\n}}"
        )
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
                "helper_code": helper_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"MI-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"quad={quad}, scale={scale}, n={n}",
                    dtype="double", difficulty="hard", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=10,
                    expected_speedup_range="5x-50x", composition=[]))}


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

#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *s = malloc(ROWS * COLS * sizeof({dtype}));
    {dtype} *f = malloc(ROWS * COLS * sizeof({dtype}));
    for (int k = 0; k < ROWS * COLS; k++) s[k] = ({dtype})(k % 100) * 0.1;
    memcpy(f, s, ROWS * COLS * sizeof({dtype}));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_mi4_{suf}(s, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_mi4_{suf}(f, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int k = 0; k < ROWS * COLS; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(s); free(f);
    return 0;
}}"""

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

#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int total = ROWS * COLS;
    {dtype} *A = malloc(total * sizeof({dtype}));
    {dtype} *B = malloc(total * sizeof({dtype}));
    {dtype} *s = malloc(total * sizeof({dtype}));
    {dtype} *f = malloc(total * sizeof({dtype}));
    for (int k = 0; k < total; k++) {{ A[k] = ({dtype})(k % 100) * 0.1; B[k] = ({dtype})(k % 50) * 0.2; }}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_mi4_{suf}(s, A, B, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_mi4_{suf}(f, A, B, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int k = 0; k < total; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-4) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(A); free(B); free(s); free(f);
    return 0;
}}"""

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

#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *mat = malloc(ROWS * COLS * sizeof({dtype}));
    for (int k = 0; k < ROWS * COLS; k++) mat[k] = ({dtype})(k % 100) * 0.01;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_slow = slow_mi4_{suf}(mat, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    {dtype} r_fast = fast_mi4_{suf}(mat, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs((double)(r_slow - r_fast));
    double mag = fabs((double)r_slow) + fabs((double)r_fast);
    int correct = (mag == 0) ? (diff == 0) : (diff / mag < 1e-2);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(mat);
    return 0;
}}"""

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

#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int total = ROWS * COLS;
    {dtype} *src = malloc(total * sizeof({dtype}));
    {dtype} *s = malloc(total * sizeof({dtype}));
    {dtype} *f = malloc(total * sizeof({dtype}));
    for (int k = 0; k < total; k++) src[k] = ({dtype})(k % 100) * 0.1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_mi4_{suf}(s, src, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_mi4_{suf}(f, src, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int k = 0; k < total; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-9) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(src); free(s); free(f);
    return 0;
}}"""

        else:  # transform
            fn_name, _ = rng.choice(UNARY_MATH_FNS)
            slow_code = f"""#include <math.h>
void slow_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            matrix[i * cols + j] = ({dtype}){fn_name}((double)matrix[i * cols + j]);
        }}
    }}
}}"""
            fast_code = f"""#include <math.h>
void fast_mi4_{suf}({dtype} *matrix, int rows, int cols) {{
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            matrix[i * cols + j] = ({dtype}){fn_name}((double)matrix[i * cols + j]);
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

#define ROWS {rows}
#define COLS {cols}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {dtype} *s = malloc(ROWS * COLS * sizeof({dtype}));
    {dtype} *f = malloc(ROWS * COLS * sizeof({dtype}));
    for (int k = 0; k < ROWS * COLS; k++) s[k] = ({dtype})((k % 100) + 1) * 0.01;
    memcpy(f, s, ROWS * COLS * sizeof({dtype}));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_mi4_{suf}(s, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_mi4_{suf}(f, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int k = 0; k < ROWS * COLS; k++) {{
        if (fabs((double)(s[k] - f[k])) > 1e-6) {{ correct = 0; break; }}
    }}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(s); free(f);
    return 0;
}}"""

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
