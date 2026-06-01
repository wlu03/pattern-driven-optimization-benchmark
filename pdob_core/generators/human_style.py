"""Human-Style Antipatterns (HR-1..HR-5) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, VariantMetadata


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

        # asm volatile("" ::: "memory") = compiler memory barrier. Forces the
        # compiler to flush + reload all memory across the barrier, which
        # prevents loop fusion (mean_X+mean_Y, var_X+var_Y) and partial
        # vectorization across the four passes. Without it, -O3 fuses pairs
        # of loops and closes the gap to ~1.85x — see commit history.
        slow_code = (f"void slow_hr2_{suf}({dtype} *X,{dtype} *Y,int n,\n"
                     f"    {dtype} *mx,{dtype} *my,{dtype} *vx,{dtype} *vy){{\n"
                     f"    {dtype} sx=0;\n"
                     f"    for(int i=0;i<n;i++) sx+=X[i];\n"
                     f"    *mx=sx/n;\n"
                     f"    asm volatile(\"\" ::: \"memory\");\n"
                     f"    {dtype} sy=0;\n"
                     f"    for(int i=0;i<n;i++) sy+=Y[i];\n"
                     f"    *my=sy/n;\n"
                     f"    asm volatile(\"\" ::: \"memory\");\n"
                     f"    {dtype} vs=0;\n"
                     f"    for(int i=0;i<n;i++){{{dtype} d=X[i]-*mx;vs+=d*d;}}\n"
                     f"    *vx=vs/n;\n"
                     f"    asm volatile(\"\" ::: \"memory\");\n"
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
    Slow: calls noinline defensive-check helper per iteration.
    Fast: clean inner loop with no checks.

    Compiler-resistance strategy:
    - helper.c contains noinline check function compiled as a separate TU,
      preventing the compiler from proving checks are redundant.
    - volatile inside the helper blocks dead-code elimination of always-true checks.
    - Slow code calls the helper per iteration; fast code does the work directly.
    """

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
            # Helper checks: NULL, bounds, NaN — returns value or 0
            helper_code = (
                f"#include <math.h>\n\n"
                f"__attribute__((noinline))\n"
                f"{dtype} hr4_check_{suf}({dtype} *arr, int idx, int n){{\n"
                f"    volatile {dtype} *vp = arr;\n"
                f"    volatile int vidx = idx;\n"
                f"    volatile int vn = n;\n"
                f"    if(vp == (void*)0) return 0;\n"
                f"    if(vn <= 0) return 0;\n"
                f"    if(vidx < 0 || vidx >= vn) return 0;\n"
                f"    volatile {dtype} val = arr[vidx];\n"
                f"    if(val != val) return 0;\n"  # NaN check
                f"    return ({dtype})val;\n"
                f"}}\n"
            )
            sig = f"{dtype} *arr,int n"
            call_args = "arr,N"
            ret = f"{dtype}"
            slow_code = (
                f"{dtype} hr4_check_{suf}({dtype} *arr, int idx, int n);\n\n"
                f"{ret} slow_hr4_{suf}({sig}){{\n"
                f"    {dtype} sum=0;\n"
                f"    for(int i=0;i<n;i++) sum+=hr4_check_{suf}(arr,i,n);\n"
                f"    return sum;\n}}"
            )
            fast_code = (
                f"{ret} fast_hr4_{suf}({sig}){{\n"
                f"    {dtype} sum=0;\n"
                f"    for(int i=0;i<n;i++) sum+=arr[i];\n"
                f"    return sum;\n}}"
            )
            setup = f"{dtype} *arr=malloc(N*sizeof({dtype}));for(int i=0;i<N;i++) arr[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};"
            free_s = "free(arr);"

        elif op_type == "dot":
            helper_code = (
                f"#include <math.h>\n\n"
                f"__attribute__((noinline))\n"
                f"{dtype} hr4_check_{suf}({dtype} *A, {dtype} *B, int idx, int n){{\n"
                f"    volatile {dtype} *vA = A;\n"
                f"    volatile {dtype} *vB = B;\n"
                f"    volatile int vidx = idx;\n"
                f"    volatile int vn = n;\n"
                f"    if(vA == (void*)0 || vB == (void*)0) return 0;\n"
                f"    if(vidx < 0 || vidx >= vn) return 0;\n"
                f"    volatile {dtype} a = A[vidx];\n"
                f"    volatile {dtype} b = B[vidx];\n"
                f"    if(a != a || b != b) return 0;\n"
                f"    return ({dtype})(a * b);\n"
                f"}}\n"
            )
            sig = f"{dtype} *A,{dtype} *B,int n"
            call_args = "A,B,N"
            ret = f"{dtype}"
            slow_code = (
                f"{dtype} hr4_check_{suf}({dtype} *A, {dtype} *B, int idx, int n);\n\n"
                f"{ret} slow_hr4_{suf}({sig}){{\n"
                f"    {dtype} sum=0;\n"
                f"    for(int i=0;i<n;i++) sum+=hr4_check_{suf}(A,B,i,n);\n"
                f"    return sum;\n}}"
            )
            fast_code = (
                f"{ret} fast_hr4_{suf}({sig}){{\n"
                f"    {dtype} sum=0;\n"
                f"    for(int i=0;i<n;i++) sum+=A[i]*B[i];\n"
                f"    return sum;\n}}"
            )
            setup = (f"{dtype} *A=malloc(N*sizeof({dtype})),*B=malloc(N*sizeof({dtype}));\n"
                     f"    for(int i=0;i<N;i++){{A[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};B[i]=({dtype})((i%50)+1)*0.02{DTYPES[dtype]['suffix']};}}")
            free_s = "free(A);free(B);"

        else:  # scale_sum
            helper_code = (
                f"#include <math.h>\n\n"
                f"__attribute__((noinline))\n"
                f"{dtype} hr4_check_{suf}({dtype} *arr, int idx, int n){{\n"
                f"    volatile {dtype} *vp = arr;\n"
                f"    volatile int vidx = idx;\n"
                f"    volatile int vn = n;\n"
                f"    if(vp == (void*)0) return 0;\n"
                f"    if(vn <= 0) return 0;\n"
                f"    if(vidx < 0 || vidx >= vn) return 0;\n"
                f"    volatile {dtype} val = arr[vidx];\n"
                f"    if(val != val) return 0;\n"
                f"    return ({dtype})val*({dtype})2.0+({dtype})1.0;\n"
                f"}}\n"
            )
            sig = f"{dtype} *arr,int n"
            call_args = "arr,N"
            ret = f"{dtype}"
            slow_code = (
                f"{dtype} hr4_check_{suf}({dtype} *arr, int idx, int n);\n\n"
                f"{ret} slow_hr4_{suf}({sig}){{\n"
                f"    {dtype} sum=0;\n"
                f"    for(int i=0;i<n;i++) sum+=hr4_check_{suf}(arr,i,n);\n"
                f"    return sum;\n}}"
            )
            fast_code = (
                f"{ret} fast_hr4_{suf}({sig}){{\n"
                f"    {dtype} sum=0;\n"
                f"    for(int i=0;i<n;i++) sum+=arr[i]*({dtype})2.0{DTYPES[dtype]['suffix']}+({dtype})1.0{DTYPES[dtype]['suffix']};\n"
                f"    return sum;\n}}"
            )
            setup = f"{dtype} *arr=malloc(N*sizeof({dtype}));for(int i=0;i<N;i++) arr[i]=({dtype})((i%100)+1)*0.01{DTYPES[dtype]['suffix']};"
            free_s = "free(arr);"

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
                "helper_code": helper_code,
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
