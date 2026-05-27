"""Data Structure (DS-1..DS-4) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.

DS-4 also imports SAFE_AOS_FIELD_COUNT.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, SAFE_AOS_FIELD_COUNT, VariantMetadata


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
    Slow: malloc/free inside loop per chunk via noinline helpers in separate TU.
    Fast: allocate once, reuse.

    Compiler-resistance strategy:
    - helper.c contains noinline alloc_chunk / free_chunk functions compiled
      as a separate TU, preventing the compiler from eliding malloc/free.
    - volatile pointer inside alloc_chunk blocks dead store elimination.
    - Chunk sizes are kept small (8-16) to maximise allocation overhead
      relative to computation, with large N (10M-20M) for many iterations.
    """

    def __init__(self):
        super().__init__("DS-2", "Data Structure",
                         "Repeated Allocation vs Pre-allocation")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        dtype = rng.choice(["float", "double"])
        n = rng.choice([10000000, 20000000])
        chunk = rng.choice([8, 16])
        n_results = n // chunk + 1

        # ── helper.c: noinline alloc/free in separate TU ──
        helper_code = (
            f"#include <stdlib.h>\n\n"
            f"__attribute__((noinline))\n"
            f"void* ds2_alloc_{suf}(int n){{\n"
            f"    volatile void *p = malloc(n);\n"
            f"    return (void*)p;\n"
            f"}}\n\n"
            f"__attribute__((noinline))\n"
            f"void ds2_free_{suf}(void *p){{\n"
            f"    volatile void *vp = p;\n"
            f"    free((void*)vp);\n"
            f"}}\n"
        )

        # ── slow.c: declare extern helpers, malloc/free per chunk ──
        slow_code = (
            f"#include <stdlib.h>\n"
            f"void* ds2_alloc_{suf}(int n);\n"
            f"void ds2_free_{suf}(void *p);\n\n"
            f"void slow_ds2_{suf}({dtype} *results,{dtype} *input,int n,int chunk){{\n"
            f"    for(int i=0;i<n;i+=chunk){{\n"
            f"        int sz=(i+chunk<=n)?chunk:(n-i);\n"
            f"        {dtype} *tmp=({dtype}*)ds2_alloc_{suf}(sz*(int)sizeof({dtype}));\n"
            f"        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];\n"
            f"        {dtype} sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];\n"
            f"        results[i/chunk]=sum;\n"
            f"        ds2_free_{suf}(tmp);\n"
            f"    }}\n}}\n"
        )

        fast_code = (f"#include <stdlib.h>\n"
                     f"void fast_ds2_{suf}({dtype} *results,{dtype} *input,int n,int chunk){{\n"
                     f"    {dtype} *tmp=({dtype}*)malloc(chunk*sizeof({dtype}));\n"
                     f"    for(int i=0;i<n;i+=chunk){{\n"
                     f"        int sz=(i+chunk<=n)?chunk:(n-i);\n"
                     f"        for(int j=0;j<sz;j++) tmp[j]=input[i+j]*input[i+j];\n"
                     f"        {dtype} sum=0; for(int j=0;j<sz;j++) sum+=tmp[j];\n"
                     f"        results[i/chunk]=sum;\n"
                     f"    }}\n"
                     f"    free(tmp);\n}}\n")
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
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "helper_code": helper_code,
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
    Slow: large struct (512+ bytes) copied onto stack for every call via
    noinline function in helper.c (separate TU).
    Fast: pointer passed to noinline function in helper.c, no copy.

    Compiler-resistance strategy:
    - BOTH slow and fast processing functions live in helper.c as noinline
      in a separate TU.  This isolates the variable to purely pass-by-value
      (copies 512-1024 bytes onto stack) vs pass-by-pointer (8-byte pointer).
    - The struct has 64-128 double fields (512-1024 bytes) but the processing
      function only accesses 3 fields (first, middle, last), so copy overhead
      dominates over computation.
    - noinline prevents the compiler from inlining and eliminating the copy.
    """

    def __init__(self):
        super().__init__("DS-3", "Data Structure",
                         "Unnecessary Struct Copy (Pass-by-Value)")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        n_fields = rng.choice([64, 96, 128])  # 512-1024 bytes per struct
        n_structs = rng.choice([2000000, 4000000])

        # Generate field names
        fnames = [f"f{i}" for i in range(n_fields)]
        fields_decl = "".join(f"double {fn};" for fn in fnames)

        # Only access 3 fields (first, middle, last) so copy overhead dominates
        f_first, f_mid, f_last = fnames[0], fnames[n_fields//2], fnames[-1]
        body_val = f"double r=s.{f_first}+s.{f_mid}+s.{f_last};return r;"
        body_ptr = f"double r=s->{f_first}+s->{f_mid}+s->{f_last};return r;"

        struct_def = f"typedef struct{{{fields_decl}}} BS_{suf};"

        # ── helper.c: BOTH functions noinline in separate TU ──
        helper_code = (
            f"{struct_def}\n\n"
            f"__attribute__((noinline))\n"
            f"double ds3_process_{suf}(BS_{suf} s){{\n"
            f"    {body_val}\n"
            f"}}\n\n"
            f"__attribute__((noinline))\n"
            f"double ds3_process_fast_{suf}(const BS_{suf} *s){{\n"
            f"    {body_ptr}\n"
            f"}}\n"
        )

        # ── slow.c: declares extern helper, calls with pass-by-value ──
        slow_code = (
            f"{struct_def}\n"
            f"double ds3_process_{suf}(BS_{suf} s);\n\n"
            f"double slow_ds3_{suf}(BS_{suf} *arr, int n){{\n"
            f"    double total=0.0;\n"
            f"    for(int i=0;i<n;i++) total+=ds3_process_{suf}(arr[i]);\n"
            f"    return total;\n"
            f"}}\n"
        )

        # ── fast.c: pass-by-pointer, no copy ──
        fast_code = (
            f"{struct_def}\n"
            f"double ds3_process_fast_{suf}(const BS_{suf} *s);\n\n"
            f"double fast_ds3_{suf}(BS_{suf} *arr, int n){{\n"
            f"    double total=0.0;\n"
            f"    for(int i=0;i<n;i++) total+=ds3_process_fast_{suf}(&arr[i]);\n"
            f"    return total;\n"
            f"}}\n"
        )

        init_fields = "".join(f"arr[i].{fnames[j]}=(double)((i+{j})%100)*0.01;" for j in range(n_fields))

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N_FIELDS {n_fields}
#define N_STRUCTS {n_structs}
{struct_def}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    BS_{suf} *arr=(BS_{suf}*)malloc(N_STRUCTS*sizeof(BS_{suf}));
    for(int i=0;i<N_STRUCTS;i++){{{init_fields}}}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    double rs=slow_ds3_{suf}(arr,N_STRUCTS);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    double rf=fast_ds3_{suf}(arr,N_STRUCTS);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs(rs-rf),ref=fabs(rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "helper_code": helper_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"DS-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"n_fields={n_fields}, n={n_structs}",
                    dtype="double", difficulty="medium", compiler_fixable=False,
                    num_loops=1, num_arrays=1, lines_of_code=10,
                    expected_speedup_range="2x-8x", composition=[]))}


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
        guard_name = f"AOS_{suf.upper()}_DEFINED"
        struct_def = f"#ifndef {guard_name}\n#define {guard_name}\ntypedef struct {{\n{struct_fields_str}\n}} {struct_name};\n#endif"

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

        # Build test harness
        n_test = rng.choice([500000, 1000000, 2000000])
        # Allocate SoA arrays for fast path
        soa_allocs = "\n".join(
            f"    double *soa_{f} = malloc(N * sizeof(double));" for f in accessed_fields
        )
        soa_init = "\n".join(
            f"    for (int i = 0; i < N; i++) soa_{f}[i] = (double)arr[i].{f};" for f in accessed_fields
        )
        soa_args = ", ".join(f"soa_{f}" for f in accessed_fields)
        soa_frees = "\n".join(f"    free(soa_{f});" for f in accessed_fields)

        # Initialize struct fields with varied data
        field_inits = "\n".join(
            f"        arr[i].{fn} = ({ft})(i % 100) * 0.01 + 0.5;"
            for fn, ft in fields
        )

        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N {n_test}

{struct_def}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    {struct_name} *arr = malloc(N * sizeof({struct_name}));
    for (int i = 0; i < N; i++) {{
{field_inits}
    }}

{soa_allocs}
{soa_init}

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ds4_{suf}(arr, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ds4_{suf}({soa_args}, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-9);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));

    free(arr);
{soa_frees}
    return 0;
}}"""

        return {
            "slow_code": slow_code,
            "fast_code": fast_code,
            "test_code": test_code,
            "metadata": asdict(metadata)
        }
