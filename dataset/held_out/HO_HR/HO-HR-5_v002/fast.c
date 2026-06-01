#include <stdint.h>
/* FAST: branchless per-byte class detection. The slow version's switch
 * forces a data-dependent branch every byte (compiler lowers to a jump
 * table + default-case branch). Rewriting as boolean arithmetic lets
 * -O3 auto-vectorize the entire loop into SIMD. */

int32_t fast_ho_hr5_v002(const uint8_t *buf, int n) {
    int32_t count = 0;
    for (int i = 0; i < n; i++) {
        uint8_t c = buf[i];
        /* boolean math: each predicate is 0/1, sum into count */
        int needs = (c < 0x20) | (c == '"') | (c == '\\');
        count += needs;
    }
    return count;
}
