#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 1000000
#define K 100

// SLOW_CODE_HERE
// FAST_CODE_HERE

static int cmp_int(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

int main() {
    int *arr_slow = malloc(N * sizeof(int));
    int *arr_fast = malloc(N * sizeof(int));
    int *out_slow = malloc(K * sizeof(int));
    int *out_fast = malloc(K * sizeof(int));
    int *orig_sorted = malloc(N * sizeof(int));

    for (int i = 0; i < N; i++) arr_slow[i] = i;
    memcpy(arr_fast, arr_slow, N * sizeof(int));
    memcpy(orig_sorted, arr_slow, N * sizeof(int));
    qsort(orig_sorted, N, sizeof(int), cmp_int);

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_ho_al1_v000(arr_slow, N, K, 42u, out_slow);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_ho_al1_v000(arr_fast, N, K, 42u, out_fast);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    // Correctness: both outputs must be K distinct values drawn from [0..N-1].
    int correct = 1;
    int *sslow = malloc(K * sizeof(int));
    int *sfast = malloc(K * sizeof(int));
    memcpy(sslow, out_slow, K * sizeof(int));
    memcpy(sfast, out_fast, K * sizeof(int));
    qsort(sslow, K, sizeof(int), cmp_int);
    qsort(sfast, K, sizeof(int), cmp_int);
    for (int i = 0; i < K; i++) {
        if (sslow[i] < 0 || sslow[i] >= N) { correct = 0; break; }
        if (sfast[i] < 0 || sfast[i] >= N) { correct = 0; break; }
        if (i > 0 && sslow[i] == sslow[i-1]) { correct = 0; break; }
        if (i > 0 && sfast[i] == sfast[i-1]) { correct = 0; break; }
    }
    free(sslow); free(sfast);

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr_slow); free(arr_fast); free(out_slow); free(out_fast); free(orig_sorted);
    return 0;
}
