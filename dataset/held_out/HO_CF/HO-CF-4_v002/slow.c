#include <stdint.h>
#include <string.h>
/* SLOW: per-call EOB check inside bit-stream consumer.
 * Every read_bits() pays for: (a) refill check, (b) bounds check,
 * (c) cursor-vs-end compare. CSE/PRE cannot hoist these because
 * the cursor changes every call. https://fgiesen.wordpress.com/2016/01/02/end-of-buffer-checks-in-decompressors/ */

typedef struct {
    const uint8_t *cursor;
    const uint8_t *end;
    uint64_t bitbuf;
    int bitcount;
} bs_slow_t;

__attribute__((noinline))
static int slow_get_bits_v002(bs_slow_t *s, int n) {
    /* per-call refill */
    while (s->bitcount < n && s->cursor < s->end) {
        s->bitbuf |= ((uint64_t)*s->cursor) << s->bitcount;
        s->bitcount += 8;
        s->cursor++;
    }
    if (s->bitcount < n) return 0;
    int v = (int)(s->bitbuf & ((1u << n) - 1u));
    s->bitbuf >>= n;
    s->bitcount -= n;
    return v;
}

int32_t slow_ho_cf4_v002(const uint8_t *src, int n_bytes, int n_syms) {
    bs_slow_t s = { src, src + n_bytes, 0, 0 };
    int32_t acc = 0;
    for (int i = 0; i < n_syms; i++) {
        int v = slow_get_bits_v002(&s, 5);
        acc += v;
    }
    return acc;
}
