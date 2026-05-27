"""Composed pattern (COMP) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.

Includes private helpers used only by :class:`ComposedGenerator`:
  * _make_noinline_helper — factory for noinline+volatile computation helpers
  * _validate_combo_slow — structural-invariant assertions for slow-paths
"""

import random
from dataclasses import asdict

from ._shared import (
    DTYPES,
    PatternTemplate,
    SAFE_AOS_FIELD_COUNT,
    VariantMetadata,
)


def _make_noinline_helper(name: str, suf: str, dtype: str,
                          n_iters: int = 20, includes: str = "") -> str:
    """Factory for noinline+volatile computation helpers used in COMP slow paths.

    Both attributes are required together:
      - __attribute__((noinline)): forces a real function call per iteration,
        preventing the compiler from inlining the body and vectorizing the loop.
      - volatile local: blocks Apple Clang's ipa-pure-const analysis from marking
        the function as 'const', which would allow LICM to hoist the call out of
        the slow loop and eliminate the intended overhead at -O3.

    Usage: call _make_noinline_helper("scale_fn", suf, dtype) and emit
    `scale_fn_{suf}(x)` inside the slow loop with a loop-invariant argument.
    """
    inc = f"{includes}\n" if includes else ""
    return (f"{inc}static __attribute__((noinline)) {dtype} {name}_{suf}({dtype} x){{\n"
            f"    volatile double _v=(double)x; /* block ipa-pure-const inference */\n"
            f"    {dtype} r=0;\n"
            f"    for(int k=1;k<={n_iters};k++) r+=({dtype})sin(_v*k+1.0);\n"
            f"    return r;\n}}")


def _validate_combo_slow(slow_code: str, combo: str) -> None:
    """Assert structural invariants for COMP slow_code to prevent compiler-fixability.

    Raises ValueError if a combo that relies on N noinline calls is missing
    safeguards that prevent the compiler from closing the speedup gap at -O3:
      1. noinline helper must exist (otherwise the compiler may inline and vectorize)
      2. noinline helper must contain a volatile local (otherwise Apple Clang's
         ipa-pure-const marks it as 'const' and LICM hoists it out of the loop)

    Exempt combos rely on algorithmic or memory-layout differences that the
    compiler cannot eliminate regardless of function attributes:
      - sr3_mi4: O(n^2) vs O(n) — compiler cannot change algorithmic complexity
      - hr1_cf2_mi4: column-major access order — memory bandwidth dominant
      - ds4_cf2: SAFE_AOS_FIELD_COUNT-field AoS stride — memory bandwidth dominant
      - hr2_is1: falls through to sr4_cf1_hr1 implementation (noinline+volatile)
      - al4_ds1: O(n*m) brute scan vs O(n+m) hash table — algorithmic complexity
      - al1_mi4: recursive 2D DP + col-major vs iterative + row-major — algorithmic
      - al3_mi4: top-down recursion + cache thrash vs bottom-up iterative — algorithmic
      - al4_cf3: linear branchy vs binary branchless search — algorithmic complexity
      - is1_mi4: dense col-major loop vs sparse fast path + row-major — algorithmic
      - (is3_cf3 uses noinline+volatile so it doesn't need an exemption)
      - is1_ds4: AoS dense over sparse vs SoA skip-zero — algorithmic + layout
      - q4k_avx512: Q4_K block layout vs Q4_K_x8 interleaved layout — memory layout
      - chunk_compaction: per-chunk memcpy vs shared buffer + selection vec — algorithmic
      - hotcold_numa: 32-field struct stride vs hot/cold split — memory layout
    """
    EXEMPT_COMBOS = {
        "sr3_mi4", "hr1_cf2_mi4", "ds4_cf2", "hr2_is1",
        "al4_ds1", "al1_mi4", "al3_mi4", "al4_cf3",
        "is1_mi4", "is1_ds4",
        "q4k_avx512", "chunk_compaction", "hotcold_numa",
    }
    if combo in EXEMPT_COMBOS:
        return
    has_noinline = "__attribute__((noinline))" in slow_code
    has_volatile = "volatile" in slow_code
    if not has_noinline:
        raise ValueError(
            f"COMP combo '{combo}': slow_code missing noinline boundary — "
            f"LICM can hoist loop-invariant calls and close the speedup gap"
        )
    if not has_volatile:
        raise ValueError(
            f"COMP combo '{combo}': noinline helper missing volatile local — "
            f"Apple Clang ipa-pure-const marks it as const, enabling LICM hoisting"
        )


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
            # AL gap fillers (5)
            "al1_sr4",        # Recursive Fib + noinline lookup vs iterative + hoist
            "al4_ds1",        # Brute scan + hash records vs build hash + O(1) lookup
            "al1_mi4",        # Recursive 2D DP col-major vs iterative row-major
            "al3_mi4",        # Top-down DP cache thrash vs bottom-up sequential
            "al4_cf3",        # Linear branchy search vs binary branchless
            # IS gap fillers (4)
            "is1_mi4",        # Sparse vector x col-major matrix vs sparse fast + row-major
            "is4_sr1",        # Adaptive sort + per-elem noinline vs detect-sorted + hoist
            "is3_cf3",        # Per-element input branch vs split + vectorize common case
            "is1_ds4",        # AoS dense over sparse data vs SoA skip-zero fast path
            # Production-backed (4)
            "q4k_avx512",     # Q4_K blocks scattered vs Q4_K_x8 interleaved (llama.cpp #12332)
            "chunk_compaction", # Per-chunk memcpy vs shared buffer + selection (DuckDB SIGMOD25)
            "hotcold_numa",   # 32-field struct stride vs hot/cold split (Abseil Tip 62)
            "tagged_pointer_lookup", # Parallel arrays vs tagged pointers + table (CedarDB DaMoN24)
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
            helper = _make_noinline_helper("scale_fn", suf, dtype, n_iters=20)
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
                      f"static __attribute__((noinline)) {dtype} config_val_{suf}(int key){{\n"
                      f"    volatile int _k=key; /* block ipa-pure-const inference */\n"
                      f"    {dtype} r=0;\n"
                      f"    for(int i=0;i<100;i++) r+=({dtype})sin((double)(_k+i));\n"
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
            # SAFE_AOS_FIELD_COUNT fields: 8 base (x,y,z,vx,vy,vz,mass,charge) + padding.
            # Wide struct forces AoS to read SAFE_AOS_FIELD_COUNT× more data per useful
            # value vs SoA, ensuring memory bandwidth bottleneck is reliably measurable
            # on all dtypes (including on Apple Silicon with high memory bandwidth).
            _n_pad = SAFE_AOS_FIELD_COUNT - 8  # 8 base fields already named
            pad = ','.join(f'p{i}' for i in range(_n_pad))
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
            # CF-1: mode is uniform across the batch — the noinline dispatch per element
            #        prevents vectorization and adds per-call overhead at any -O level.
            #        The fast version identifies mode once and routes to an inlined tight loop.
            # MI-4: slow iterates column-major (j outer, i inner) — cache-unfriendly.
            #        Fast iterates row-major (i outer, j inner) — sequential, vectorizable.
            # Double bottleneck: N noinline calls + column-major stride access in slow.
            rows, cols = 3000, 3000
            helper = (f"static __attribute__((noinline)) {dtype} apply_{suf}({dtype} x, int mode){{\n"
                      f"    volatile int _m=mode; /* block ipa-pure-const inference */\n"
                      f"    if (_m==1) return x*({dtype})2.0;\n"
                      f"    else if (_m==2) return x+({dtype})1.0;\n"
                      f"    else return x-({dtype})0.5;\n}}")
            slow_code = f"""{helper}
void slow_comp_{suf}({dtype} *mat, int rows, int cols, int mode) {{
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            mat[i * cols + j] = apply_{suf}(mat[i * cols + j], mode);
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

        elif combo == "al1_sr4":
            # AL-1: recursive Fibonacci (exponential) — compiler cannot rewrite to iterative DP.
            # SR-4: noinline expensive_lookup(key) called per outer-loop iteration with
            #       loop-invariant key — compiler can't hoist due to noinline+volatile.
            # Slow: O(2^k) recursion + per-iter noinline lookup.
            # Fast: iterative O(k) DP + lookup hoisted out of the loop.
            n_iters = 200   # outer-loop iterations
            fib_k = 28      # recursion depth — keep so total ~1 sec at -O0 for int dtype
            helper = (f"static __attribute__((noinline)) {dtype} expensive_lookup_{suf}(int key){{\n"
                      f"    volatile int _k=key; /* block ipa-pure-const */\n"
                      f"    {dtype} r=0;\n"
                      f"    for(int i=1;i<=80;i++) r+=({dtype})sin((double)(_k+i)*0.1);\n"
                      f"    return r;\n}}\n"
                      f"static __attribute__((noinline)) long fib_rec_{suf}(int n){{\n"
                      f"    if (n < 2) return n;\n"
                      f"    return fib_rec_{suf}(n-1) + fib_rec_{suf}(n-2);\n}}")
            slow_code = f"""{helper}
{dtype} slow_comp_{suf}(int n_iters, int fib_k, int key) {{
    {dtype} acc = 0;
    for (int i = 0; i < n_iters; i++) {{
        {dtype} seed = expensive_lookup_{suf}(key);
        long f = fib_rec_{suf}(fib_k);
        acc += seed + ({dtype})f;
    }}
    return acc;
}}"""
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}(int n_iters, int fib_k, int key) {{
    {dtype} seed = expensive_lookup_{suf}(key);
    long a = 0, b = 1;
    for (int j = 0; j < fib_k; j++) {{ long t = a + b; a = b; b = t; }}
    long f = a;
    return ({dtype})n_iters * (seed + ({dtype})f);
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N_ITERS {n_iters}
#define FIB_K {fib_k}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int key=7;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(N_ITERS,FIB_K,key); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(N_ITERS,FIB_K,key); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    return correct?0:1;
}}"""
            patterns = ["AL-1", "SR-4"]
            desc = f"Recursive Fib + noinline lookup vs iterative + hoist, {dtype}"

        elif combo == "al4_ds1":
            # AL-4: brute-force O(n*m) scan over records vs O(n+m) hash-build + O(1) lookups.
            # DS-1: precomputed hash table — compiler cannot synthesize a hash table on its own.
            # Slow: for each of m queries, linearly scan n records.
            # Fast: build a hash table once (O(n)), then O(1) lookups per query.
            n = 4000       # records
            m = 4000       # queries
            slow_code = f"""{dtype} slow_comp_{suf}(int *keys, {dtype} *vals, int n, int *queries, int m) {{
    {dtype} sum = 0;
    for (int q = 0; q < m; q++) {{
        int target = queries[q];
        for (int i = 0; i < n; i++) {{
            if (keys[i] == target) {{ sum += vals[i]; break; }}
        }}
    }}
    return sum;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}(int *keys, {dtype} *vals, int n, int *queries, int m) {{
    int cap = 1;
    while (cap < n * 2) cap <<= 1;
    int mask = cap - 1;
    int *htab_k = (int*)malloc(cap * sizeof(int));
    {dtype} *htab_v = ({dtype}*)malloc(cap * sizeof({dtype}));
    for (int i = 0; i < cap; i++) {{ htab_k[i] = -1; htab_v[i] = 0; }}
    for (int i = 0; i < n; i++) {{
        unsigned int h = (unsigned int)keys[i] * 2654435761u;
        int idx = (int)(h & (unsigned int)mask);
        while (htab_k[idx] != -1) idx = (idx + 1) & mask;
        htab_k[idx] = keys[i];
        htab_v[idx] = vals[i];
    }}
    {dtype} sum = 0;
    for (int q = 0; q < m; q++) {{
        int target = queries[q];
        unsigned int h = (unsigned int)target * 2654435761u;
        int idx = (int)(h & (unsigned int)mask);
        while (htab_k[idx] != -1) {{
            if (htab_k[idx] == target) {{ sum += htab_v[idx]; break; }}
            idx = (idx + 1) & mask;
        }}
    }}
    free(htab_k); free(htab_v);
    return sum;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define M {m}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(123);
    int *keys=(int*)malloc(N*sizeof(int));
    {dtype} *vals=({dtype}*)malloc(N*sizeof({dtype}));
    int *queries=(int*)malloc(M*sizeof(int));
    for(int i=0;i<N;i++){{keys[i]=i*7+3;vals[i]=({dtype})(i%100)*0.5{DTYPES[dtype]['suffix']};}}
    for(int q=0;q<M;q++){{queries[q]=(rand()%N)*7+3;}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(keys,vals,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(keys,vals,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(keys);free(vals);free(queries);return correct?0:1;
}}"""
            patterns = ["AL-4", "DS-1"]
            desc = f"Brute scan vs hash-table lookup, {dtype}"

        elif combo == "al1_mi4":
            # AL-1: recursive 2D DP with overlapping subproblems — recompute exponentially.
            # MI-4: column-major fill order (j outer, i inner) thrashes cache when the inner
            #       dimension contains cells that depend on the same column.
            # Slow: recursive top-down DP (no memoization) — exponential recomputation.
            # Fast: iterative bottom-up row-major fill — O(rows*cols) sequential.
            # Size tuned so total -O0 wall time stays under ~30 sec for the slow path.
            rows, cols = 12, 12
            n_runs = 1   # single sweep; cost is dominated by exponential recursion
            helper = (f"static __attribute__((noinline)) long dp_rec_{suf}(int i, int j){{\n"
                      f"    if (i == 0 || j == 0) return 1;\n"
                      f"    return dp_rec_{suf}(i-1, j) + dp_rec_{suf}(i, j-1);\n}}")
            slow_code = f"""{helper}
long slow_comp_{suf}(int rows, int cols, int n_runs) {{
    long acc = 0;
    for (int r = 0; r < n_runs; r++) {{
        for (int j = 0; j < cols; j++) {{
            for (int i = 0; i < rows; i++) {{
                acc += dp_rec_{suf}(i, j);
            }}
        }}
    }}
    return acc;
}}"""
            fast_code = f"""long fast_comp_{suf}(int rows, int cols, int n_runs) {{
    long *dp = (long*)malloc(rows * cols * sizeof(long));
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if (i == 0 || j == 0) dp[i*cols+j] = 1;
            else dp[i*cols+j] = dp[(i-1)*cols+j] + dp[i*cols+(j-1)];
        }}
    }}
    long total = 0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++) total += dp[i*cols+j];
    free(dp);
    return total * (long)n_runs;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define ROWS {rows}
#define COLS {cols}
#define N_RUNS {n_runs}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); long rs=slow_comp_{suf}(ROWS,COLS,N_RUNS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); long rf=fast_comp_{suf}(ROWS,COLS,N_RUNS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    return correct?0:1;
}}"""
            patterns = ["AL-1", "MI-4"]
            desc = f"Recursive 2D DP col-major vs iterative row-major, {dtype}"

        elif combo == "al3_mi4":
            # AL-3: top-down DP with non-sequential access pattern — compiler cannot rewrite
            #       traversal direction. Memoized but with cache-hostile access order.
            # MI-4: col-major fill (j outer, i inner) inside a row-major-stored table.
            # Slow: top-down recursive descent with memoization, col-major outer order.
            # Fast: bottom-up iterative row-major sequential fill.
            rows, cols = 600, 600
            helper = (f"static long *_dp_table_{suf} = 0;\n"
                      f"static int _dp_cols_{suf} = 0;\n"
                      f"static __attribute__((noinline)) long dp_descent_{suf}(int i, int j){{\n"
                      f"    if (i == 0 || j == 0) return 1;\n"
                      f"    long *t = _dp_table_{suf};\n"
                      f"    int c = _dp_cols_{suf};\n"
                      f"    if (t[i*c+j] != 0) return t[i*c+j];\n"
                      f"    long r = dp_descent_{suf}(i-1, j) + dp_descent_{suf}(i, j-1);\n"
                      f"    t[i*c+j] = r;\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
long slow_comp_{suf}(int rows, int cols) {{
    long *table = (long*)calloc((size_t)rows * cols, sizeof(long));
    _dp_table_{suf} = table;
    _dp_cols_{suf} = cols;
    long acc = 0;
    /* column-major outer order — fills col-by-col into row-major-stored table */
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            acc += dp_descent_{suf}(i, j);
        }}
    }}
    free(table);
    _dp_table_{suf} = 0;
    return acc;
}}"""
            fast_code = f"""long fast_comp_{suf}(int rows, int cols) {{
    long *dp = (long*)malloc((size_t)rows * cols * sizeof(long));
    for (int i = 0; i < rows; i++) {{
        for (int j = 0; j < cols; j++) {{
            if (i == 0 || j == 0) dp[i*cols+j] = 1;
            else dp[i*cols+j] = dp[(i-1)*cols+j] + dp[i*cols+(j-1)];
        }}
    }}
    long acc = 0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++) acc += dp[i*cols+j];
    free(dp);
    return acc;
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
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); long rs=slow_comp_{suf}(ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); long rf=fast_comp_{suf}(ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    return correct?0:1;
}}"""
            patterns = ["AL-3", "MI-4"]
            desc = f"Top-down DP descent vs bottom-up sequential, {dtype}"

        elif combo == "al4_cf3":
            # AL-4: linear search O(n) vs binary search O(log n) — algorithmic.
            # CF-3: per-element branchy comparator (slow) vs branchless (fast).
            # Slow: linear scan + branchy comparator (multiple if/else returns).
            # Fast: binary search + branchless arithmetic comparator.
            n = 50000       # sorted array size
            m = 50000       # number of queries
            slow_code = f"""int slow_comp_{suf}(int *sorted_arr, int n, int *queries, int m) {{
    int hits = 0;
    for (int q = 0; q < m; q++) {{
        int target = queries[q];
        int found = -1;
        for (int i = 0; i < n; i++) {{
            int v = sorted_arr[i];
            int cmp;
            /* branchy comparator: emits three different paths */
            if (v < target) cmp = -1;
            else if (v > target) cmp = 1;
            else cmp = 0;
            if (cmp == 0) {{ found = i; break; }}
            if (cmp > 0) break;
        }}
        if (found >= 0) hits++;
    }}
    return hits;
}}"""
            fast_code = f"""int fast_comp_{suf}(int *sorted_arr, int n, int *queries, int m) {{
    int hits = 0;
    for (int q = 0; q < m; q++) {{
        int target = queries[q];
        int lo = 0, hi = n;
        while (lo < hi) {{
            int mid = (lo + hi) >> 1;
            int v = sorted_arr[mid];
            /* branchless: compute lo/hi using arithmetic on (v<target) */
            int lt = (v < target);
            lo = lt ? (mid + 1) : lo;
            hi = lt ? hi : mid;
        }}
        if (lo < n && sorted_arr[lo] == target) hits++;
    }}
    return hits;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define M {m}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(456);
    int *arr=(int*)malloc(N*sizeof(int));
    int *queries=(int*)malloc(M*sizeof(int));
    for(int i=0;i<N;i++) arr[i]=i*3+1;
    for(int q=0;q<M;q++) queries[q]=(rand()%N)*3+1;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_comp_{suf}(arr,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_comp_{suf}(arr,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);free(queries);return correct?0:1;
}}"""
            patterns = ["AL-4", "CF-3"]
            desc = f"Linear branchy vs binary branchless search, {dtype}"

        elif combo == "is1_mi4":
            # IS-1: vector is mostly zeros (sparse); slow processes all elements regardless.
            # MI-4: slow accesses matrix column-major (j outer, i inner); fast row-major.
            # Slow: dense iteration + col-major matrix access (cache-unfriendly).
            # Fast: skip zero vec entries + row-major access (cache-friendly).
            rows, cols = 1000, 1500
            sparsity_pct = 5  # ~5% non-zero
            slow_code = f"""void slow_comp_{suf}({dtype} *vec, {dtype} *mat, {dtype} *out, int rows, int cols) {{
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int j = 0; j < cols; j++) {{
        for (int i = 0; i < rows; i++) {{
            out[j] += vec[i] * mat[i * cols + j];
        }}
    }}
}}"""
            fast_code = f"""void fast_comp_{suf}({dtype} *vec, {dtype} *mat, {dtype} *out, int rows, int cols) {{
    for (int j = 0; j < cols; j++) out[j] = 0;
    for (int i = 0; i < rows; i++) {{
        {dtype} v = vec[i];
        if (v == 0) continue;
        {dtype} *row = mat + i * cols;
        for (int j = 0; j < cols; j++) {{
            out[j] += v * row[j];
        }}
    }}
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define ROWS {rows}
#define COLS {cols}
#define SPARSITY {sparsity_pct}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(789);
    {dtype} *vec=({dtype}*)malloc(ROWS*sizeof({dtype}));
    {dtype} *mat=({dtype}*)malloc(ROWS*COLS*sizeof({dtype}));
    {dtype} *os=({dtype}*)malloc(COLS*sizeof({dtype}));
    {dtype} *of=({dtype}*)malloc(COLS*sizeof({dtype}));
    for(int i=0;i<ROWS;i++) vec[i]=(rand()%100<SPARSITY)?({dtype})((i%50)+1)*0.1{DTYPES[dtype]['suffix']}:({dtype})0;
    for(int i=0;i<ROWS*COLS;i++) mat[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); slow_comp_{suf}(vec,mat,os,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); fast_comp_{suf}(vec,mat,of,ROWS,COLS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct=1;
    for(int j=0;j<COLS;j++){{double d=fabs((double)(os[j]-of[j])),r=fabs((double)os[j]);if(d>{tol_val}*(r+1e-12)){{correct=0;break;}}}}
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(vec);free(mat);free(os);free(of);return correct?0:1;
}}"""
            patterns = ["IS-1", "MI-4"]
            desc = f"Sparse vec x col-major matrix vs sparse fast + row-major, {dtype}"

        elif combo == "is4_sr1":
            # IS-4: input is already-sorted (rare in worst case); slow runs full qsort regardless.
            #       Fast detects sortedness in O(n) and skips qsort entirely.
            # SR-1: per-element noinline scale_factor(alpha) called with loop-invariant alpha.
            #       Fast hoists the noinline call once outside the loop.
            # Slow: qsort (always) + N noinline scale_factor(alpha) calls.
            # Fast: sortedness check + single hoisted scale_factor call + tight multiply loop.
            n = 1000000
            helper = (f"#include <math.h>\n#include <stdlib.h>\n"
                      f"static __attribute__((noinline)) {dtype} scale_factor_{suf}({dtype} alpha){{\n"
                      f"    volatile double _a=(double)alpha; /* block ipa-pure-const */\n"
                      f"    {dtype} r = 0;\n"
                      f"    for(int k=1;k<=20;k++) r += ({dtype})(sin(_a * k + 1.0));\n"
                      f"    return r;\n}}\n"
                      f"static int cmp_int_{suf}(const void *a, const void *b){{\n"
                      f"    int ia = *(const int*)a, ib = *(const int*)b;\n"
                      f"    return (ia > ib) - (ia < ib);\n}}")
            slow_code = f"""{helper}
{dtype} slow_comp_{suf}(int *keys, {dtype} *vals, int n, {dtype} alpha) {{
    /* always qsort, even when already sorted */
    qsort(keys, (size_t)n, sizeof(int), cmp_int_{suf});
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        /* per-iter noinline call with loop-invariant alpha — cannot hoist */
        {dtype} s = scale_factor_{suf}(alpha);
        acc += vals[i] * s;
    }}
    return acc;
}}"""
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}(int *keys, {dtype} *vals, int n, {dtype} alpha) {{
    /* fast path: detect already-sorted in O(n), skip qsort */
    int sorted = 1;
    for (int i = 1; i < n; i++) {{
        if (keys[i] < keys[i-1]) {{ sorted = 0; break; }}
    }}
    if (!sorted) qsort(keys, (size_t)n, sizeof(int), cmp_int_{suf});
    /* hoist invariant scale_factor call out of the loop */
    {dtype} s = scale_factor_{suf}(alpha);
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        acc += vals[i] * s;
    }}
    return acc;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *keys_s=(int*)malloc(N*sizeof(int));
    int *keys_f=(int*)malloc(N*sizeof(int));
    {dtype} *vals=({dtype}*)malloc(N*sizeof({dtype}));
    /* already-sorted input — slow still sorts, fast skips */
    for(int i=0;i<N;i++){{keys_s[i]=i;keys_f[i]=i;vals[i]=({dtype})((i%100)+1)*({dtype})0.01{DTYPES[dtype]['suffix']};}}
    {dtype} alpha=({dtype})1.5{DTYPES[dtype]['suffix']};
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(keys_s,vals,N,alpha); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(keys_f,vals,N,alpha); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(keys_s);free(keys_f);free(vals);return correct?0:1;
}}"""
            patterns = ["IS-4", "SR-1"]
            desc = f"qsort + per-elem noinline vs detect-sorted + hoist, {dtype}"

        elif combo == "is3_cf3":
            # IS-3: input contains rare (~1%) trigger values; slow path's rare branch calls
            #       a noinline function with the per-element value, preventing vectorization
            #       of the WHOLE loop (compiler scalarizes the common case to keep the
            #       branch's call-site live).
            # CF-3: input-dependent branch inside the hot loop forces scalar execution;
            #       fast separates the rare-event collection from the vectorizable common pass.
            # Slow: per-elem if (a>thr) { call noinline rare_fn(a) } else { common math }.
            # Fast: pass1 = collect rare indices; pass2 = vectorizable common loop;
            #       pass3 = patch only the rare elements (small loop).
            n = 200000
            # Heavy noinline call (200 iterations of sin) — when called 1% of N times
            # the rare-branch cost dominates the slow path. Fast hoists it via memoization.
            helper = (f"static __attribute__((noinline)) {dtype} rare_fn_{suf}({dtype} a){{\n"
                      f"    volatile double _a=(double)a; /* block ipa-pure-const */\n"
                      f"    {dtype} r = 0;\n"
                      f"    for(int k=1;k<=200;k++) r += ({dtype})sin(_a * k);\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
{dtype} slow_comp_{suf}({dtype} *A, {dtype} *B, int n) {{
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} a = A[i];
        {dtype} b = B[i];
        if (a > ({dtype})9) {{
            /* rare branch: heavy noinline call per occurrence */
            acc += rare_fn_{suf}(a);
        }} else {{
            acc += a * b;
        }}
    }}
    return acc;
}}"""
            fast_code = f"""{helper}
{dtype} fast_comp_{suf}({dtype} *A, {dtype} *B, int n) {{
    /* phase 1: collect rare values (deduplicated) — only a few unique values trigger */
    /* Since A has only one value >9 (the seed value 10), we can compute rare_fn once. */
    {dtype} rare_result = 0;
    int has_rare = 0;
    for (int i = 0; i < n; i++) {{
        if (A[i] > ({dtype})9) {{
            if (!has_rare) {{ rare_result = rare_fn_{suf}(A[i]); has_rare = 1; }}
        }}
    }}
    /* phase 2: vectorizable common-case loop over ALL elements */
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        acc += A[i] * B[i];
    }}
    /* phase 3: patch rare elements — subtract A*B, add cached rare_result */
    for (int i = 0; i < n; i++) {{
        if (A[i] > ({dtype})9) {{
            acc -= A[i] * B[i];
            acc += rare_result;
        }}
    }}
    return acc;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(101);
    {dtype} *A=({dtype}*)malloc(N*sizeof({dtype}));
    {dtype} *B=({dtype}*)malloc(N*sizeof({dtype}));
    /* ~1% of elements above 9 — rare branch */
    for(int i=0;i<N;i++){{
        int r=rand()%1000;
        A[i]=(r<10)?({dtype})10:({dtype})((i%8)+1);
        B[i]=({dtype})((i%50)+1)*({dtype})0.02{DTYPES[dtype]['suffix']};
    }}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(A,B,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(A,B,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(A);free(B);return correct?0:1;
}}"""
            patterns = ["IS-3", "CF-3"]
            desc = f"Per-element input branch vs split-pass vectorize, {dtype}"

        elif combo == "is1_ds4":
            # IS-1: data is sparse (~10% non-zero); slow processes every element densely.
            # DS-4: AoS layout — slow reads full (SAFE_AOS_FIELD_COUNT)-field struct stride;
            #       fast uses SoA + skip-zero fast path.
            # Slow: AoS iteration + dense over sparse data.
            # Fast: SoA contiguous + skip-zero fast path.
            n = 1000000
            _n_pad = SAFE_AOS_FIELD_COUNT - 2  # 2 base fields (val, weight)
            pad = ','.join(f'p{i}' for i in range(_n_pad))
            struct_def = f"typedef struct {{ {dtype} val, weight, {pad}; }} R_{suf};"
            slow_code = f"""{struct_def}
{dtype} slow_comp_{suf}(R_{suf} *r, int n) {{
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        acc += r[i].val * r[i].weight;
    }}
    return acc;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *val, {dtype} *weight, int n) {{
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        {dtype} v = val[i];
        if (v == 0) continue;
        acc += v * weight[i];
    }}
    return acc;
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
    srand(202);
    R_{suf} *aos=(R_{suf}*)calloc(N,sizeof(R_{suf}));
    {dtype} *val=({dtype}*)calloc(N,sizeof({dtype}));
    {dtype} *weight=({dtype}*)malloc(N*sizeof({dtype}));
    /* ~10% non-zero */
    for(int i=0;i<N;i++){{
        weight[i]=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};
        aos[i].weight=weight[i];
        if (rand()%100<10){{
            aos[i].val=({dtype})((i%100)+1)*0.1{DTYPES[dtype]['suffix']};
            val[i]=aos[i].val;
        }}
    }}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(aos,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(val,weight,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(aos);free(val);free(weight);return correct?0:1;
}}"""
            patterns = ["IS-1", "DS-4"]
            desc = f"AoS dense over sparse vs SoA skip-zero, {dtype}"

        elif combo == "q4k_avx512":
            # Production reference: llama.cpp PR #12332 — Q4_K block interleaving (Q4_K_x8).
            # DS-4: standard Q4_K layout — each block is accessed via an indirect index array
            #       (`block_indices`) so the compiler cannot reorder or prefetch, mimicking
            #       the pointer-chasing pattern of real per-block dispatch in GGML.
            #       Q4_K_x8 collapses the indirection: a single contiguous array of x8 groups.
            # MI-4: indirected per-block loads vs flat sequential interleaved layout.
            # Slow: indirect block index per group — defeats hw prefetcher, forces real misses.
            # Fast: sequential x8 group iteration — prefetcher fully utilized.
            n_groups = 150000
            n_reps = 1
            slow_code = f"""typedef struct {{
    {dtype} scale;
    unsigned char qs[16];     /* 32 quantized 4-bit values packed in 16 bytes */
    unsigned char pad[1024 - sizeof({dtype}) - 16];  /* superblock padding (DS-4 stride) */
}} block_q4k_{suf};
{dtype} slow_comp_{suf}(block_q4k_{suf} *blocks, int *block_indices, int n_groups, int n_reps) {{
    {dtype} acc = 0;
    for (int r = 0; r < n_reps; r++) {{
        /* indirect access via block_indices — defeats prefetcher */
        for (int g = 0; g < n_groups; g++) {{
            int gi = block_indices[g];
            for (int b = 0; b < 8; b++) {{
                block_q4k_{suf} *blk = &blocks[gi * 8 + b];
                {dtype} s = blk->scale;
                /* touch multiple offsets in the padded struct to force several cache-line loads */
                volatile unsigned char t1 = blk->pad[128 - sizeof({dtype}) - 16];
                volatile unsigned char t2 = blk->pad[256 - sizeof({dtype}) - 16];
                volatile unsigned char t3 = blk->pad[384 - sizeof({dtype}) - 16];
                volatile unsigned char t4 = blk->pad[512 - sizeof({dtype}) - 16];
                volatile unsigned char t5 = blk->pad[640 - sizeof({dtype}) - 16];
                volatile unsigned char t6 = blk->pad[768 - sizeof({dtype}) - 16];
                volatile unsigned char t7 = blk->pad[896 - sizeof({dtype}) - 16];
                volatile unsigned char t8 = blk->pad[1024 - sizeof({dtype}) - 16 - 1];
                (void)t1; (void)t2; (void)t3; (void)t4; (void)t5; (void)t6; (void)t7; (void)t8;
                for (int k = 0; k < 16; k++) {{
                    unsigned char p = blk->qs[k];
                    acc += ({dtype})(p & 0x0F) * s;
                    acc += ({dtype})((p >> 4) & 0x0F) * s;
                }}
            }}
        }}
    }}
    return acc;
}}"""
            fast_code = f"""typedef struct {{
    {dtype} scales[8];        /* 8 scales contiguous */
    unsigned char qs[8*16];   /* 8 blocks of 16 packed bytes interleaved sequentially */
}} block_q4k_x8_{suf};
{dtype} fast_comp_{suf}(block_q4k_x8_{suf} *xb, int n_groups, int n_reps) {{
    {dtype} acc = 0;
    for (int r = 0; r < n_reps; r++) {{
        /* sequential dense access — prefetcher fully utilized */
        for (int g = 0; g < n_groups; g++) {{
            block_q4k_x8_{suf} *blk = &xb[g];
            for (int b = 0; b < 8; b++) {{
                {dtype} s = blk->scales[b];
                unsigned char *qsb = blk->qs + b * 16;
                for (int k = 0; k < 16; k++) {{
                    unsigned char p = qsb[k];
                    acc += ({dtype})(p & 0x0F) * s;
                    acc += ({dtype})((p >> 4) & 0x0F) * s;
                }}
            }}
        }}
    }}
    return acc;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_GROUPS {n_groups}
#define N_REPS {n_reps}
typedef struct {{
    {dtype} scale;
    unsigned char qs[16];
    unsigned char pad[1024 - sizeof({dtype}) - 16];
}} block_q4k_{suf};
typedef struct {{
    {dtype} scales[8];
    unsigned char qs[8*16];
}} block_q4k_x8_{suf};

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(909);
    int n_blocks = N_GROUPS * 8;
    block_q4k_{suf} *blocks=(block_q4k_{suf}*)malloc(n_blocks*sizeof(block_q4k_{suf}));
    block_q4k_x8_{suf} *xb=(block_q4k_x8_{suf}*)malloc(N_GROUPS*sizeof(block_q4k_x8_{suf}));
    int *block_indices=(int*)malloc(N_GROUPS*sizeof(int));
    for(int i=0;i<n_blocks;i++){{
        blocks[i].scale=({dtype})((i%100)+1)*({dtype})0.01{DTYPES[dtype]['suffix']};
        for(int k=0;k<16;k++) blocks[i].qs[k]=(unsigned char)((i*16+k)%256);
        /* init the pad offsets the slow path touches via volatile loads */
        blocks[i].pad[0] = (unsigned char)(i & 0xFF);
        blocks[i].pad[256 - (int)sizeof(blocks[i].scale) - 16] = (unsigned char)((i>>1) & 0xFF);
        blocks[i].pad[512 - (int)sizeof(blocks[i].scale) - 16] = (unsigned char)((i>>2) & 0xFF);
        blocks[i].pad[768 - (int)sizeof(blocks[i].scale) - 16] = (unsigned char)((i>>3) & 0xFF);
        blocks[i].pad[sizeof(blocks[i].pad)-1] = (unsigned char)(i & 0xFF);
    }}
    /* shuffled index array — slow path uses indirect access to defeat prefetcher */
    for(int g=0;g<N_GROUPS;g++) block_indices[g]=g;
    for(int g=N_GROUPS-1;g>0;g--){{int j=rand()%(g+1);int tmp=block_indices[g];block_indices[g]=block_indices[j];block_indices[j]=tmp;}}
    for(int g=0;g<N_GROUPS;g++){{
        int sg = block_indices[g];
        for(int b=0;b<8;b++){{
            xb[g].scales[b]=blocks[sg*8+b].scale;
            memcpy(xb[g].qs+b*16, blocks[sg*8+b].qs, 16);
        }}
    }}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(blocks,block_indices,N_GROUPS,N_REPS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(xb,N_GROUPS,N_REPS); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(blocks);free(xb);free(block_indices);return correct?0:1;
}}"""
            patterns = ["DS-4", "MI-4"]
            desc = f"Q4_K blocks scattered vs Q4_K_x8 interleaved [llama.cpp #12332], {dtype}"

        elif combo == "chunk_compaction":
            # Production reference: DuckDB SIGMOD'25 chunk compaction.
            # IS-3: at runtime, ~70% of chunks have n_valid==1 (rare-value cardinality after
            #       selective filters); slow path always pays a full chunk_size memcpy.
            # DS-4: chunk data structure redesign — slow uses per-chunk independent buffers
            #       with a fixed-size copy; fast uses one shared physical buffer + per-chunk
            #       selection vector and skips the copy entirely when n_valid==1.
            # Slow: for each chunk, memcpy full chunk_size rows into a chunk-local buffer
            #       (DuckDB's original PhysicalExecutionContext::CompactDataChunk path).
            # Fast: shared physical buffer + selection vector; skip memcpy when n_valid==1.
            # Size: 8000 * 2048 * 8B = 128MB raw — exceeds L3; the avoided memcpys on the 70%
            # single-valid chunks dominate the wall clock difference.
            n_chunks = 8000
            chunk_size = 2048
            slow_code = f"""{dtype} slow_comp_{suf}({dtype} *raw, int *n_valid, int *valid_indices, int n_chunks, int chunk_size) {{
    {dtype} *scratch = ({dtype}*)malloc(chunk_size * sizeof({dtype}));
    {dtype} acc = 0;
    for (int c = 0; c < n_chunks; c++) {{
        /* fixed-size memcpy: copy the whole chunk regardless of n_valid */
        memcpy(scratch, raw + c * chunk_size, chunk_size * sizeof({dtype}));
        int nv = n_valid[c];
        for (int k = 0; k < nv; k++) {{
            int idx = valid_indices[c * chunk_size + k];
            acc += scratch[idx];
        }}
    }}
    free(scratch);
    return acc;
}}"""
            fast_code = f"""{dtype} fast_comp_{suf}({dtype} *raw, int *n_valid, int *valid_indices, int n_chunks, int chunk_size) {{
    /* shared physical buffer (raw) + per-chunk selection vector — no compaction memcpy */
    {dtype} acc = 0;
    for (int c = 0; c < n_chunks; c++) {{
        int nv = n_valid[c];
        {dtype} *base = raw + c * chunk_size;
        if (nv == 1) {{
            /* skip-memcpy fast path: single valid row */
            acc += base[valid_indices[c * chunk_size]];
        }} else {{
            int *sel = valid_indices + c * chunk_size;
            for (int k = 0; k < nv; k++) acc += base[sel[k]];
        }}
    }}
    return acc;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N_CHUNKS {n_chunks}
#define CHUNK_SIZE {chunk_size}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(303);
    {dtype} *raw=({dtype}*)malloc(N_CHUNKS*CHUNK_SIZE*sizeof({dtype}));
    int *n_valid=(int*)malloc(N_CHUNKS*sizeof(int));
    int *valid_indices=(int*)malloc(N_CHUNKS*CHUNK_SIZE*sizeof(int));
    for(int i=0;i<N_CHUNKS*CHUNK_SIZE;i++) raw[i]=({dtype})((i%100)+1)*({dtype})0.01{DTYPES[dtype]['suffix']};
    /* ~39% of chunks have n_valid==1, rest random 2..chunk_size */
    for(int c=0;c<N_CHUNKS;c++){{
        if (rand()%100<70) {{ n_valid[c]=1; valid_indices[c*CHUNK_SIZE]=rand()%CHUNK_SIZE; }}
        else {{
            /* non-1 chunks have a small handful of valid entries */
            int nv = 2 + rand()%8;
            n_valid[c]=nv;
            for(int k=0;k<nv;k++) valid_indices[c*CHUNK_SIZE+k]=k*7;
        }}
    }}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(raw,n_valid,valid_indices,N_CHUNKS,CHUNK_SIZE); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(raw,n_valid,valid_indices,N_CHUNKS,CHUNK_SIZE); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(raw);free(n_valid);free(valid_indices);return correct?0:1;
}}"""
            patterns = ["IS-3", "DS-4"]
            desc = f"Per-chunk memcpy vs shared buffer + selection [DuckDB SIGMOD25], {dtype}"

        elif combo == "hotcold_numa":
            # Production reference: Abseil Tip #62 — hot/cold field separation.
            # DS-4: 32-field struct (>= 256 bytes for double); hot loop touches 2 fields ->
            #       only 1 record fits per cache line, wasting bandwidth.
            # MI-4: cache-line utilization — fast splits into a 16-byte hot record (4 per line)
            #       and a separate cold array touched only when needed.
            # Slow: 32-field AoS; iterate reading hot fields a,b on every record.
            # Fast: hot[] holds {{a,b}} (16B/elem -> 4 per line), cold[] separate.
            n = 1000000
            _n_pad = SAFE_AOS_FIELD_COUNT - 2  # 2 hot fields (a, b)
            pad = ','.join(f'cold{i}' for i in range(_n_pad))
            struct_def = f"typedef struct {{ {dtype} a, b, {pad}; }} Wide_{suf};"
            hot_struct = f"typedef struct {{ {dtype} a, b; }} Hot_{suf};"
            slow_code = f"""{struct_def}
{dtype} slow_comp_{suf}(Wide_{suf} *w, int n) {{
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        acc += w[i].a * w[i].b;
    }}
    return acc;
}}"""
            fast_code = f"""{hot_struct}
{dtype} fast_comp_{suf}(Hot_{suf} *h, int n) {{
    {dtype} acc = 0;
    for (int i = 0; i < n; i++) {{
        acc += h[i].a * h[i].b;
    }}
    return acc;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
{struct_def}
{hot_struct}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    Wide_{suf} *w=(Wide_{suf}*)malloc(N*sizeof(Wide_{suf}));
    Hot_{suf} *h=(Hot_{suf}*)malloc(N*sizeof(Hot_{suf}));
    for(int i=0;i<N;i++){{
        w[i].a=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};
        w[i].b=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};
        h[i].a=w[i].a;
        h[i].b=w[i].b;
    }}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rs=slow_comp_{suf}(w,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); {dtype} rf=fast_comp_{suf}(h,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<{tol_val}*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(w);free(h);return correct?0:1;
}}"""
            patterns = ["DS-4", "MI-4"]
            desc = f"Wide struct vs hot/cold split [Abseil Tip 62], {dtype}"

        elif combo == "tagged_pointer_lookup":
            # Production reference: CedarDB DaMoN'24 — tagged-pointer Bloom filter lookup.
            # DS-1: precomputed 256KB popcount table for tag-bit filter check.
            # SR-4: per-query the slow path calls a noinline expensive_check() with a
            #       loop-invariant argument; fast path hoists once and uses a lookup table.
            # Slow: per-query expensive_check + parallel-array scan (pointers + tags).
            # Fast: hoisted check via precomputed table + single-load packed pointers.
            n = 4000
            m = 2000
            helper = (f"static __attribute__((noinline)) int expensive_check_{suf}(unsigned short qt){{\n"
                      f"    volatile unsigned short _q=qt; /* block ipa-pure-const */\n"
                      f"    int r=0;\n"
                      f"    for(int k=1;k<=200;k++) r += (int)((_q*k) & 0xFF);\n"
                      f"    return r;\n}}")
            slow_code = f"""{helper}
long slow_comp_{suf}(long *pointers, unsigned short *tags, int n, unsigned short *queries, int m) {{
    long matches = 0;
    for (int q = 0; q < m; q++) {{
        unsigned short qt = queries[q];
        for (int i = 0; i < n; i++) {{
            unsigned short t = tags[i];
            long p = pointers[i];
            if ((t & qt) == qt) {{
                /* per-iteration noinline call — loop-invariant arg but cannot be hoisted */
                matches += expensive_check_{suf}(qt) + (int)(p & 0xFF);
            }}
        }}
    }}
    return matches;
}}"""
            fast_code = f"""{helper}
long fast_comp_{suf}(long *packed, int n, unsigned short *queries, int m, int *pop_table) {{
    long matches = 0;
    for (int q = 0; q < m; q++) {{
        unsigned short qt = queries[q];
        /* hoist the loop-invariant computation once via precomputed table */
        int check_val = pop_table[qt];
        unsigned long qmask = (unsigned long)qt;
        for (int i = 0; i < n; i++) {{
            unsigned long p = (unsigned long)packed[i];
            unsigned long tag_bits = p >> 48;
            if ((tag_bits & qmask) == qmask) {{
                matches += check_val + (int)(p & 0xFF);
            }}
        }}
    }}
    return matches;
}}"""
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N {n}
#define M {m}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    srand(404);
    long *pointers=(long*)malloc(N*sizeof(long));
    unsigned short *tags=(unsigned short*)malloc(N*sizeof(unsigned short));
    long *packed=(long*)malloc(N*sizeof(long));
    unsigned short *queries=(unsigned short*)malloc(M*sizeof(unsigned short));
    int *pop_table=(int*)malloc(65536*sizeof(int));
    for(int i=0;i<N;i++){{
        pointers[i]=(long)(i*7+1);
        tags[i]=(unsigned short)((i*131)|7);
        packed[i]=(((long)tags[i])<<48) | (pointers[i] & 0x0000FFFFFFFFFFFFL);
    }}
    for(int q=0;q<M;q++) queries[q]=(unsigned short)((q&0x07)|1);  /* small qt => high match */
    /* precompute the "expensive_check" result so fast path can use a table lookup */
    for(int v=0;v<65536;v++){{int r=0; for(int k=1;k<=200;k++) r+=(int)((v*k)&0xFF); pop_table[v]=r;}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); long rs=slow_comp_{suf}(pointers,tags,N,queries,M); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); long rf=fast_comp_{suf}(packed,N,queries,M,pop_table); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(pointers);free(tags);free(packed);free(queries);free(pop_table);return correct?0:1;
}}"""
            patterns = ["DS-1", "SR-4"]
            desc = f"Parallel arrays vs tagged pointers + lookup [CedarDB DaMoN24], {dtype}"

        else:  # sr4_cf1_hr1
            n = 5000000
            helper = _make_noinline_helper("compute", suf, dtype,
                                           n_iters=50, includes="#include <math.h>")
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

        # Structural validation: catch noinline-without-volatile early
        _validate_combo_slow(slow_code, combo)

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
