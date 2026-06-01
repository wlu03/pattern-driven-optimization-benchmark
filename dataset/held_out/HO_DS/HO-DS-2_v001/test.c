#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define DICT_N 12
#define NQ 1000000

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    int keys[DICT_N] = {17, 1024, 1, 65537, 99991, 3, 2147483, 555, 42,
                         123456, 999999, 7};
    int vals[DICT_N];
    for (int i = 0; i < DICT_N; i++) vals[i] = i * 7 + 3;

    int *queries = malloc(NQ * sizeof(int));
    srand(43);
    for (int i = 0; i < NQ; i++) queries[i] = keys[rand() % DICT_N];

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_ho_ds2_v001(keys, vals, DICT_N, queries, NQ);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_ho_ds2_v001(keys, vals, DICT_N, queries, NQ);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (r_slow == r_fast);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(queries);
    return 0;
}
