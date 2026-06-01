#include <stdint.h>
/* SLOW: abstraction-induced redundancy. Many tiny per-byte read helpers,
 * each noinline so the compiler can't dissolve the wrapper. Each call
 * re-validates the cursor < end check. */

typedef struct { const uint8_t *cursor; const uint8_t *end; } cur_v000_t;

__attribute__((noinline))
static int read_byte_v003(cur_v000_t *c) {
    /* per-call bounds check */
    if (c->cursor >= c->end) return -1;
    int v = *c->cursor;
    c->cursor++;
    return v;
}

int32_t slow_ho_hr4_v003(const uint8_t *src, int n_bytes) {
    cur_v000_t c = { src, src + n_bytes };
    int32_t acc = 0;
    for (int i = 0; i < n_bytes; i++) {
        int v = read_byte_v003(&c);
        if (v < 0) break;
        acc += v;
    }
    return acc;
}
