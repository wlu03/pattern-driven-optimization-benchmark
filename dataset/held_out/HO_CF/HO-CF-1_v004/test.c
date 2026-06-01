#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 3500000

typedef struct { int tag; float value; } HoCf1Rec;

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    HoCf1Rec *arr_slow = malloc(N * sizeof(HoCf1Rec));
    HoCf1Rec *arr_fast = malloc(N * sizeof(HoCf1Rec));
    if (!arr_slow || !arr_fast) return 1;
    int tags[8] = {0x1A, 0x2C, 0x37, 0x41, 0x58, 0x6F, 0x73, 0x89};
    srand(46);
    for (int i = 0; i < N; i++) {
        arr_slow[i].tag = tags[rand() & 7];
        arr_slow[i].value = (float)(rand() % 1000) * 0.001f;
    }
    memcpy(arr_fast, arr_slow, N * sizeof(HoCf1Rec));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_slow = slow_ho_cf1_v004(arr_slow, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    double r_fast = fast_ho_cf1_v004(arr_fast, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    double diff = fabs(r_slow - r_fast);
    double mag = fmax(fabs(r_slow), 1e-12);
    int correct = (diff / mag < 1e-6) || (diff < 1e-6);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(arr_slow); free(arr_fast);
    return 0;
}
