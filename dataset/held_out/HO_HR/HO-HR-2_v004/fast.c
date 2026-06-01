#include <stdint.h>
/* FAST: remove the wrong unlikely() hint. With no hint the compiler
 * generates a fall-through layout that the branch predictor handles
 * correctly. Predicate is true ~40% of the time. */

__attribute__((noinline))
static int predicate_v004(int x) {
    return (x * 13 + 7) % 100 < 40;
}

int64_t fast_ho_hr2_v004(const int *arr, int n) {
    int64_t sum_hot = 0, sum_cold = 0;
    for (int i = 0; i < n; i++) {
        if (predicate_v004(arr[i])) {       /* NO unlikely hint */
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
