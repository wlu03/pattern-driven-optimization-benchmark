#include <stdint.h>
/* FAST: inlined cursor + no per-call wrappers. The for-loop bound (n_bytes)
 * is the only check, hoisted outside the body. */

int32_t fast_ho_hr4_v004(const uint8_t *src, int n_bytes) {
    int32_t acc = 0;
    for (int i = 0; i < n_bytes; i++) {
        acc += src[i];
    }
    return acc;
}
