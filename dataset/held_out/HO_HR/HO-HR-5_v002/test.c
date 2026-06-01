#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

#define N 15000000

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main(void) {
    uint8_t *buf = (uint8_t*)malloc((size_t)N);
    srand(44);
    /* mostly printable ASCII (97% benign), 3% escape-needing chars */
    for (int i = 0; i < N; i++) {
        int r = rand() % 100;
        if (r < 1) buf[i] = '"';
        else if (r < 2) buf[i] = '\\';
        else if (r < 3) buf[i] = (uint8_t)(rand() & 0x1f);
        else buf[i] = (uint8_t)(' ' + (rand() % 95));
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int32_t rs = slow_ho_hr5_v002(buf, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    int32_t rf = fast_ho_hr5_v002(buf, N);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec - t0.tv_sec) * 1000.0 + (t1.tv_nsec - t0.tv_nsec) / 1e6;

    int correct = (rs == rf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f rs=%d rf=%d\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001), rs, rf);
    free(buf);
    return correct ? 0 : 1;
}
