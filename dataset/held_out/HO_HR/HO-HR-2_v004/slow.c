#include <stdint.h>
/* SLOW: defensive unlikely() hint that's empirically WRONG.
 * The predicate is true ~40% of the time, but the programmer guessed
 * "rare" and marked it unlikely(). The wrong hint causes the CPU to
 * prefetch the wrong path and code layout puts the common case in the
 * cold path. https://lwn.net/Articles/420019/ (Rostedt 2011 documented
 * page_mapping(): annotation correct 1.91B times, wrong 1.27B = 39%). */
#ifndef unlikely
#define unlikely(x) __builtin_expect(!!(x), 0)
#endif

__attribute__((noinline))
static int predicate_v004(int x) {
    /* True ~40% of the time. Defeat constant-prop with noinline. */
    return (x * 13 + 7) % 100 < 40;
}

int64_t slow_ho_hr2_v004(const int *arr, int n) {
    int64_t sum_hot = 0, sum_cold = 0;
    for (int i = 0; i < n; i++) {
        if (unlikely(predicate_v004(arr[i]))) {
            /* The "rare" branch — but actually taken 40% of the time. */
            sum_hot += (int64_t)arr[i] * 17 + 3;
            sum_hot ^= (sum_hot >> 5);
        } else {
            sum_cold += arr[i];
            sum_cold *= 1103515245;
            sum_cold += 12345;
        }
    }
    return sum_hot + sum_cold;
}
