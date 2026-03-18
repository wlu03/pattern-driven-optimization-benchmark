#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define TN 10000000
#define PN 6

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *text = malloc(TN * sizeof(int));
    int pattern[6] = {6, 0, 0, 3, 7, 1};
    unsigned rs = 77u;
    for (int i = 0; i < TN; i++) {
        rs = rs * 1664525u + 1013904223u;
        text[i] = (int)((rs >> 1) % 8u);
    }

    struct timespec t0, t1;
    volatile int c_slow = 0, c_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    c_slow = slow_al3_v028(text, TN, pattern, PN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    c_fast = fast_al3_v028(text, TN, pattern, PN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct = (c_slow == c_fast) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(text);
    return 0;
}