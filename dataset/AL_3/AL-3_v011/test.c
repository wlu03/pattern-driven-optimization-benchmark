#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define TN 5000000
#define PN 300

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    /* Adversarial: pattern = PN-1 zeros then a 1.  Text = all zeros.
       Naive scans nearly the full pattern before failing at each position. */
    unsigned char *text    = calloc(TN, 1);
    unsigned char *pattern = calloc(PN, 1);
    pattern[PN - 1] = 1;

    struct timespec t0, t1;
    volatile int c_slow = 0, c_fast = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 3; r++)
        c_slow = slow_al3_v011(text, TN, pattern, PN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 3;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int r = 0; r < 3; r++)
        c_fast = fast_al3_v011(text, TN, pattern, PN);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = ((t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6) / 3;

    int correct = (c_slow == c_fast) ? 1 : 0;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(text); free(pattern);
    return 0;
}