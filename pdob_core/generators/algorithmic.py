"""Algorithmic (AL-1..AL-4) variant generators.

Extracted verbatim from ``generate_variants.py``. See ``generators/_shared.py``
for the shared helpers and base class these depend on.
"""

import random
from dataclasses import asdict

from ._shared import DTYPES, PatternTemplate, VariantMetadata


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

        # Build test harness based on problem type
        if problem in ("fibonacci", "tribonacci", "derangements"):
            # Single int arg, returns long long
            test_n = {"fibonacci": 35, "tribonacci": 25, "derangements": 25}[problem]
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = {test_n};
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""
        elif problem == "catalan":
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = 20;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""
        elif problem == "staircase":
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = 30;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_al1_{suf}(n);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""
        elif problem == "grid_paths":
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int r = 14, c = 14;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_al1_{suf}(r, c);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_al1_{suf}(r, c);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""
        elif problem == "binomial":
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = 28, k = 14;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_al1_{suf}(n, k);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_al1_{suf}(n, k);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""
        elif problem == "coin_ways":
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int coins[] = {{1, 5, 10, 25}};
    int nc = 4, amount = 30;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int r_slow = slow_al1_{suf}(coins, nc, amount);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int r_fast = fast_al1_{suf}(coins, nc, amount);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""
        elif problem == "min_cost_path":
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int m = 12, n = 12;
    int *grid = malloc(m * n * sizeof(int));
    srand(42);
    for (int i = 0; i < m * n; i++) grid[i] = rand() % 100;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int r_slow = slow_al1_{suf}(grid, m, n, m-1, n-1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int r_fast = fast_al1_{suf}(grid, m, n, m-1, n-1);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(grid);
    return 0;
}}"""
        else:  # partition_count
            test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int n = 60, max_val = 60;
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int r_slow = slow_al1_{suf}(n, max_val);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int r_fast = fast_al1_{suf}(n, max_val);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    return 0;
}}"""

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
            "test_code": test_code,
            "metadata": asdict(metadata)
        }


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
    Operates on int arrays to simulate text/pattern matching.

    Compiler-resistance strategy:
    - helper.c contains a noinline comparison function used by slow.c,
      compiled as a separate TU so the compiler cannot optimise the inner loop.
    - Adversarial data: text is all-ones with sparse mismatches placed at
      position (pn-1) so naive must scan nearly the full pattern before each
      mismatch — guaranteeing O(n*m) work for naive vs O(n+m) for KMP.
    - Pattern length 200-500 to emphasise the asymptotic gap.
    """

    def __init__(self):
        super().__init__("AL-3", "Algorithmic",
                         "Naive vs KMP Pattern Matching")

    def generate(self, variant_num: int, seed: int) -> dict:
        rng = random.Random(seed)
        suf = f"v{variant_num:03d}"
        tn = rng.choice([10000000, 20000000])
        pn = rng.choice([200, 250, 300, 400, 500])

        # ── helper.c: noinline element comparison (separate TU) ──
        helper_code = (
            f"__attribute__((noinline))\n"
            f"int al3_cmp_{suf}(int a, int b){{\n"
            f"    volatile int va = a, vb = b;\n"
            f"    return va == vb;\n"
            f"}}\n"
        )

        # ── slow.c: naive O(n*m) using the noinline comparator ──
        # The noinline call per character prevents the compiler from
        # vectorising or short-circuiting the inner loop.
        slow_code = (
            f"int al3_cmp_{suf}(int a, int b);\n\n"
            f"int slow_al3_{suf}(int *text,int tn,int *pat,int pn){{\n"
            f"    int count=0;\n"
            f"    for(int i=0;i<=tn-pn;i++){{\n"
            f"        int m=1;\n"
            f"        for(int j=0;j<pn;j++){{\n"
            f"            if(!al3_cmp_{suf}(text[i+j],pat[j])){{m=0;break;}}\n"
            f"        }}\n"
            f"        if(m) count++;\n"
            f"    }}\n"
            f"    return count;\n"
            f"}}\n"
        )

        # ── fast.c: KMP O(n+m) ──
        fast_code = (
            f"#include <stdlib.h>\n"
            f"static void build_fail_{suf}(int *pat,int pn,int *fail){{\n"
            f"    fail[0]=0; int k=0;\n"
            f"    for(int i=1;i<pn;i++){{\n"
            f"        while(k>0&&pat[k]!=pat[i]) k=fail[k-1];\n"
            f"        if(pat[k]==pat[i]) k++;\n"
            f"        fail[i]=k;\n"
            f"    }}\n"
            f"}}\n\n"
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
            f"    return count;\n"
            f"}}\n"
        )

        # ── test.c ──
        # Adversarial text: all ones, with a mismatch (value 0) injected every
        # (pn-1) positions.  The pattern is all ones (length pn).
        # This forces naive to compare (pn-1) elements before each mismatch,
        # giving true O(n*m) behaviour.  KMP skips forward after each mismatch.
        test_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define TN {tn}
#define PN {pn}

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {{
    int *text=(int*)malloc(TN*sizeof(int));
    /* Adversarial text: all 1s with a 0 every (PN-1) positions.
       Pattern is all 1s ⇒ naive scans (PN-1) chars before each mismatch. */
    for(int i=0;i<TN;i++) text[i]=1;
    for(int i=PN-1;i<TN;i+=PN-1) text[i]=0;

    int *pat=(int*)malloc(PN*sizeof(int));
    for(int i=0;i<PN;i++) pat[i]=1;

    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    int cs=slow_al3_{suf}(text,TN,pat,PN);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC,&t0);
    int cf=fast_al3_{suf}(text,TN,pat,PN);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct=(cs==cf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\\n",
           ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(text);free(pat);return correct?0:1;
}}"""
        return {"slow_code": slow_code, "fast_code": fast_code,
                "test_code": test_code, "helper_code": helper_code,
                "metadata": asdict(VariantMetadata(
                    pattern_id=self.pattern_id, variant_id=f"AL-3_v{variant_num:03d}",
                    category=self.category, pattern_name=self.name,
                    variant_desc=f"tn={tn}, pn={pn}, adversarial all-ones",
                    dtype="int", difficulty="hard", compiler_fixable=False,
                    num_loops=2, num_arrays=1, lines_of_code=18,
                    expected_speedup_range="5x-50x", composition=[]))}


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
