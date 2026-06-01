#include <stdint.h>
/* SLOW: per-byte switch detecting JSON characters needing escape. The compiler
 * can lower a small switch to a jump table, but the per-byte loop processes
 * one input element per iteration with a data-dependent branch on each. */

int32_t slow_ho_hr5_v004(const uint8_t *buf, int n) {
    int32_t count = 0;
    for (int i = 0; i < n; i++) {
        uint8_t c = buf[i];
        switch (c) {
            case '"':  count++; break;
            case '\\': count++; break;
            case '\b': count++; break;
            case '\f': count++; break;
            case '\n': count++; break;
            case '\r': count++; break;
            case '\t': count++; break;
            default:
                if (c < 0x20) count++;
                break;
        }
    }
    return count;
}
