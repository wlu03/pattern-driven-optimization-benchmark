#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define ROWS 2000
#define COLS 5000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int total = ROWS * COLS;
    int *src = malloc(total * sizeof(int));
    int *s = malloc(total * sizeof(int));
    int *f = malloc(total * sizeof(int));
    for (int k = 0; k < total; k++) src[k] = (int)(k % 100) * 0.1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    slow_mi4_v002(s, src, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    fast_mi4_v002(f, src, ROWS, COLS);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = 1;
    for (int k = 0; k < total; k++) {
        if (fabs((double)(s[k] - f[k])) > 1e-9) { correct = 0; break; }
    }
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(src); free(s); free(f);
    return 0;
}