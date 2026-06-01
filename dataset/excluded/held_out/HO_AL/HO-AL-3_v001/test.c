#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>

// 1M (key, increment) pairs inserted from a Zipfian-ish key space.
// Top-NQ=100 hot keys each get a heavy weight (count >= 9000); the
// remaining inserts go to a long tail of small tail-keys.  CMS with
// w=2048, d=5: per-row mean overestimate ~= (N - hot_count)/w ~= 50;
// with min over 5 rows the practical tail is well under 5% of 9000 = 450.
#define N   500000
#define NQ  100

// SLOW_CODE_HERE
// FAST_CODE_HERE

int main() {
    uint32_t *keys = malloc(N * sizeof(uint32_t));
    int32_t  *incs = malloc(N * sizeof(int32_t));
    uint32_t *qk   = malloc(NQ * sizeof(uint32_t));
    int64_t  *fslow = malloc(NQ * sizeof(int64_t));
    int64_t  *ffast = malloc(NQ * sizeof(int64_t));
    if (!keys || !incs || !qk || !fslow || !ffast) return 1;

    // Build a key stream where the first NQ keys (top-100) each receive
    // ~N/200 = 5000 increments, and the remaining ~half-million inserts
    // go to a long tail.  This guarantees the top-NQ keys dominate.
    long pos = 0;
    srand(43);
    // Hot keys: 9500 inserts each => 950,000 total hot inserts.
    for (int q = 0; q < NQ; q++) {
        qk[q] = 1000u + (uint32_t)q;     // keys 1000..1099
        for (int t = 0; t < 9500 && pos < N; t++) {
            keys[pos] = qk[q];
            incs[pos] = 1;
            pos++;
        }
    }
    // Tail: 50,000 inserts to keys 2000..52000 (mean = 1 per key).
    while (pos < N) {
        keys[pos] = 2000u + (uint32_t)(rand() % 50000);
        incs[pos] = 1;
        pos++;
    }
    // Shuffle so the stream isn't sorted (CMS shouldn't care, but for realism).
    for (long i = N - 1; i > 0; i--) {
        long j = rand() % (i + 1);
        uint32_t tk = keys[i]; keys[i] = keys[j]; keys[j] = tk;
        int32_t  tv = incs[i]; incs[i] = incs[j]; incs[j] = tv;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_slow = slow_ho_al3_v001(keys, incs, N, qk, NQ, fslow);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_slow = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long r_fast = fast_ho_al3_v001(keys, incs, N, qk, NQ, ffast);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms_fast = (t1.tv_sec-t0.tv_sec)*1000.0 + (t1.tv_nsec-t0.tv_nsec)/1e6;
    (void)r_slow; (void)r_fast;

    // Relative-error correctness check, epsilon = 0.05 (5%).  CMS is
    // one-sided (always >= true); we just need the fast estimate to be
    // close to (and >= ) the exact slow count for every queried key.
    int correct = 1;
    for (int q = 0; q < NQ; q++) {
        if (ffast[q] < fslow[q]) { correct = 0; break; }
        double err = (double)(ffast[q] - fslow[q]) / fmax((double)fslow[q], 1.0);
        if (err > 0.05) { correct = 0; break; }
    }

    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow, ms_fast, correct, ms_slow / fmax(ms_fast, 0.001));
    free(keys); free(incs); free(qk); free(fslow); free(ffast);
    return 0;
}
