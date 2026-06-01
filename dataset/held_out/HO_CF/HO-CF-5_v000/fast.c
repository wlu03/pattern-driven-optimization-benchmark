#include <stdint.h>
/* FAST: precomputed transition table. Each (state, input_byte) maps to
 * (symbol, next_state) via a flat array lookup. Branch-free per symbol. */

typedef struct { uint8_t sym; uint8_t next; } trans_v000_t;
static trans_v000_t g_table_v000[8 * 256];
static int g_init_v000 = 0;

static void build_table_v000(void) {
    for (int s = 0; s < 8; s++) for (int b = 0; b < 256; b++) {
        uint8_t sym = 0; uint8_t nxt = 0;
        if (s == 0) {
            if (b < 64)       { sym = 0; nxt = 1; }
            else if (b < 128) { sym = 1; nxt = 2; }
            else if (b < 192) { sym = 2; nxt = 3; }
            else              { sym = 3; nxt = 0; }
        } else if (s == 1) {
            if (b < 32)       { sym = 4; nxt = 2; }
            else if (b < 96)  { sym = 5; nxt = 4; }
            else if (b < 160) { sym = 6; nxt = 5; }
            else              { sym = 7; nxt = 1; }
        } else if (s == 2) {
            if (b < 80)       { sym = 0; nxt = 6; }
            else if (b < 160) { sym = 1; nxt = 7; }
            else              { sym = 2; nxt = 3; }
        } else if (s == 3) {
            if (b < 100)      { sym = 3; nxt = 0; }
            else if (b < 200) { sym = 4; nxt = 4; }
            else              { sym = 5; nxt = 2; }
        } else if (s == 4) {
            if (b < 50)       { sym = 6; nxt = 5; }
            else if (b < 150) { sym = 7; nxt = 6; }
            else              { sym = 0; nxt = 1; }
        } else if (s == 5) {
            if (b < 75)       { sym = 1; nxt = 7; }
            else if (b < 175) { sym = 2; nxt = 0; }
            else              { sym = 3; nxt = 3; }
        } else if (s == 6) {
            if (b < 60)       { sym = 4; nxt = 1; }
            else if (b < 180) { sym = 5; nxt = 2; }
            else              { sym = 6; nxt = 4; }
        } else {
            if (b < 90)       { sym = 7; nxt = 0; }
            else if (b < 200) { sym = 0; nxt = 5; }
            else              { sym = 1; nxt = 6; }
        }
        g_table_v000[s * 256 + b].sym = sym;
        g_table_v000[s * 256 + b].next = nxt;
    }
}

int32_t fast_ho_cf5_v000(const uint8_t *input, int n, uint8_t *out_syms) {
    if (!g_init_v000) { build_table_v000(); g_init_v000 = 1; }
    int state = 0;
    int32_t checksum = 0;
    for (int i = 0; i < n; i++) {
        trans_v000_t t = g_table_v000[state * 256 + input[i]];
        out_syms[i] = t.sym;
        checksum = (checksum * 31) + t.sym;
        state = t.next;
    }
    return checksum;
}
