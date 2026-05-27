# Data Structure patterns: DS-1 through DS-4.
from ._entry import PatternEntry


DS_PATTERNS = [
    PatternEntry(
        pattern_id="DS-1",
        category="Data Structure",
        name="Linear Search vs Hash Lookup",
        compiler_difficulty="Very High",
        description="O(n) linear scan through 50 000-entry array for each of many queries. "
                    "Pre-build an open-addressing hash table; each lookup is O(1).",
        slow_code="""
int ds1_slow_lookup(int *keys, int *values, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (keys[i] == target) return values[i];
    }
    return -1;
}""",
        fast_code="""
#define HT_SIZE 65536
#define HT_MASK (HT_SIZE - 1)
typedef struct { int key; int value; int occupied; } HTEntry;

void ds1_build_ht(HTEntry *ht, int *keys, int *values, int n) {
    memset(ht, 0, HT_SIZE * sizeof(HTEntry));
    for (int i = 0; i < n; i++) {
        int h = (unsigned int)keys[i] & HT_MASK;
        while (ht[h].occupied) h = (h + 1) & HT_MASK;
        ht[h].key = keys[i];
        ht[h].value = values[i];
        ht[h].occupied = 1;
    }
}

int ds1_fast_lookup(HTEntry *ht, int target) {
    int h = (unsigned int)target & HT_MASK;
    while (ht[h].occupied) {
        if (ht[h].key == target) return ht[h].value;
        h = (h + 1) & HT_MASK;
    }
    return -1;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define HT_SIZE 65536
#define HT_MASK (HT_SIZE - 1)
typedef struct { int key; int value; int occupied; } HTEntry;

static int ds1_slow_lookup(int *keys, int *values, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (keys[i] == target) return values[i];
    }
    return -1;
}

// LLM_CODE_HERE

int main() {
    int n_keys = 50000;
    int n_queries = 1000;
    int *keys    = malloc(n_keys * sizeof(int));
    int *values  = malloc(n_keys * sizeof(int));
    int *queries = malloc(n_queries * sizeof(int));
    srand(42);
    for (int i = 0; i < n_keys; i++) {
        keys[i]   = i * 7 + 13;
        values[i] = i * 3;
    }
    for (int i = 0; i < n_queries; i++)
        queries[i] = keys[rand() % n_keys];

    /* build hash table for fast version */
    HTEntry *ht = malloc(HT_SIZE * sizeof(HTEntry));
    ds1_build_ht(ht, keys, values, n_keys);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int sum_fast = 0;
    for (int i = 0; i < n_queries; i++)
        sum_fast += optimized(ht, queries[i]);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int sum_slow = 0;
    for (int i = 0; i < n_queries; i++)
        sum_slow += ds1_slow_lookup(keys, values, n_keys, queries[i]);

    int correct = (sum_slow == sum_fast);
    printf("result=%d time_ms=%.4f correct=%d\\n", sum_fast, ms, correct);
    free(keys); free(values); free(queries); free(ht);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="DS-2",
        category="Data Structure",
        name="Repeated Allocation vs Pre-allocation",
        compiler_difficulty="High",
        description="malloc / free per chunk inside the processing loop. "
                    "Allocate the temp buffer once before the loop; reuse it.",
        slow_code="""
#include <stdlib.h>
void ds2_slow(double *results, double *input, int n, int chunk_size) {
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        double *temp = malloc(sz * sizeof(double));
        for (int j = 0; j < sz; j++) temp[j] = input[i + j] * input[i + j];
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk_size] = sum;
        free(temp);
    }
}""",
        fast_code="""
#include <stdlib.h>
void ds2_fast(double *results, double *input, int n, int chunk_size) {
    double *temp = malloc(chunk_size * sizeof(double));
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        for (int j = 0; j < sz; j++) temp[j] = input[i + j] * input[i + j];
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk_size] = sum;
    }
    free(temp);
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    int chunk_size = 1024;
    int n_results = n / chunk_size + 1;
    double *input    = malloc(n * sizeof(double));
    double *out      = malloc(n_results * sizeof(double));
    double *expected = malloc(n_results * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++)
        input[i] = -10.0 + 20.0 * ((double)rand() / RAND_MAX);

    /* compute expected */
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += input[i+j] * input[i+j];
        expected[i / chunk_size] = sum;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    optimized(out, input, n, chunk_size);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = 1;
    for (int i = 0; i < n_results; i++) {
        if (!_bench_close(out[i], expected[i], 1e-9, 1e-9)) {
            correct = 0; break;
        }
    }
    printf("result=%.10f time_ms=%.4f correct=%d\\n", out[0], ms, correct);
    free(input); free(out); free(expected);
    return 0;
}"""
    ),

    PatternEntry(
        pattern_id="DS-3",
        category="Data Structure",
        name="Unnecessary Copying (pass-by-value)",
        compiler_difficulty="Medium",
        description="512-byte BigStruct copied onto the stack for every call to the processing function. "
                    "Pass by const * — only the pointer is copied.",
        slow_code="""
typedef struct {
    double data[64];
    int size;
} BigStruct;

double ds3_slow_process(BigStruct s) {
    double sum = 0.0;
    for (int i = 0; i < s.size; i++) sum += s.data[i];
    return sum;
}""",
        fast_code="""
typedef struct {
    double data[64];
    int size;
} BigStruct;

double ds3_fast_process(const BigStruct *s) {
    double sum = 0.0;
    for (int i = 0; i < s->size; i++) sum += s->data[i];
    return sum;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct {
    double data[64];
    int size;
} BigStruct;

static double ds3_slow_process(BigStruct s) {
    double sum = 0.0;
    for (int i = 0; i < s.size; i++) sum += s.data[i];
    return sum;
}

// LLM_CODE_HERE

int main() {
    int n = 2000000;
    BigStruct *arr = malloc(n * sizeof(BigStruct));
    srand(42);
    for (int i = 0; i < n; i++) {
        arr[i].size = 64;
        for (int j = 0; j < 64; j++) arr[i].data[j] = (double)(i + j);
    }

    double ref_result = 0.0;
    for (int i = 0; i < n; i++) ref_result += ds3_slow_process(arr[i]);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double fast_result = 0.0;
    for (int i = 0; i < n; i++) fast_result += optimized(&arr[i]);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    int correct = _bench_close(ref_result, fast_result, 1e-6, 1e-6);
    printf("result=%.10f time_ms=%.4f correct=%d\\n", fast_result, ms, correct);
    free(arr);
    return 0;
}"""
    ),

    PatternEntry(pattern_id="DS-4", category="Data Structure", name="AoS vs SoA Cache Access",
        compiler_difficulty="Very High",
        description="Array of Structures causes 64-byte stride when accessing one field. "
                    "Structure of Arrays gives sequential 8-byte stride.",
        slow_code="""
typedef struct { double x,y,z,vx,vy,vz,mass,charge; } Particle;
double ds4_slow(Particle *p, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += p[i].mass;
    return total;
}""",
        fast_code="""
double ds4_fast(double *mass, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}""",
        test_harness="""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

typedef struct { double x,y,z,vx,vy,vz,mass,charge; } Particle;

static double ds4_slow_ref(Particle *p, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) total += p[i].mass;
    return total;
}

// LLM_CODE_HERE

int main() {
    int n = 5000000;
    Particle *p = malloc(n * sizeof(Particle));
    double *mass = malloc(n * sizeof(double));
    srand(42);
    for (int i = 0; i < n; i++) {
        p[i].x = p[i].y = p[i].z = p[i].vx = p[i].vy = p[i].vz = p[i].charge = 1.0;
        p[i].mass = (double)rand() / RAND_MAX;
        mass[i] = p[i].mass;
    }

    double expected = ds4_slow_ref(p, n);

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    double result = optimized(mass, n);
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec - start.tv_sec) * 1000.0 + (end.tv_nsec - start.tv_nsec) / 1e6;

    printf("result=%.10f time_ms=%.4f correct=%d\\n",
           result, ms, _bench_close(result, expected, 1e-6, 1e-6));
    free(p); free(mass);
    return 0;
}"""
    ),
]
