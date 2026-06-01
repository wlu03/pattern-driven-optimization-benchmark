#include <stdint.h>
/* SLOW: 8-state FSM decoded via nested if-else cascade.
 * Each per-symbol transition involves multiple branches that the
 * predictor must learn separately. Compilers cannot synthesize a
 * precomputed transition table from procedural state-update code.
 * http://fastcompression.blogspot.com/2014/01/fse-decoding-how-it-works.html */

int32_t slow_ho_cf5_v003(const uint8_t *input, int n, uint8_t *out_syms) {
    int state = 0;
    int32_t checksum = 0;
    for (int i = 0; i < n; i++) {
        uint8_t b = input[i];
        uint8_t sym = 0;
        int next = 0;
        if (state == 0) {
            if (b < 64)       { sym = 0; next = 1; }
            else if (b < 128) { sym = 1; next = 2; }
            else if (b < 192) { sym = 2; next = 3; }
            else              { sym = 3; next = 0; }
        } else if (state == 1) {
            if (b < 32)       { sym = 4; next = 2; }
            else if (b < 96)  { sym = 5; next = 4; }
            else if (b < 160) { sym = 6; next = 5; }
            else              { sym = 7; next = 1; }
        } else if (state == 2) {
            if (b < 80)       { sym = 0; next = 6; }
            else if (b < 160) { sym = 1; next = 7; }
            else              { sym = 2; next = 3; }
        } else if (state == 3) {
            if (b < 100)      { sym = 3; next = 0; }
            else if (b < 200) { sym = 4; next = 4; }
            else              { sym = 5; next = 2; }
        } else if (state == 4) {
            if (b < 50)       { sym = 6; next = 5; }
            else if (b < 150) { sym = 7; next = 6; }
            else              { sym = 0; next = 1; }
        } else if (state == 5) {
            if (b < 75)       { sym = 1; next = 7; }
            else if (b < 175) { sym = 2; next = 0; }
            else              { sym = 3; next = 3; }
        } else if (state == 6) {
            if (b < 60)       { sym = 4; next = 1; }
            else if (b < 180) { sym = 5; next = 2; }
            else              { sym = 6; next = 4; }
        } else { /* state == 7 */
            if (b < 90)       { sym = 7; next = 0; }
            else if (b < 200) { sym = 0; next = 5; }
            else              { sym = 1; next = 6; }
        }
        out_syms[i] = sym;
        checksum = (checksum * 31) + sym;
        state = next;
    }
    return checksum;
}
