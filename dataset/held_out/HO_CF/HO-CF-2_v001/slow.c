#include <stdint.h>
/* SLOW: bytecode interpreter using a switch() inside a for loop.
 * All opcode dispatches funnel through one indirect-jump site, giving
 * the BTB only one prediction entry. See LWN 2025 "Computed gotos for
 * efficient dispatch tables", https://lwn.net/Articles/1010905/.
 * Calibration: Rohou/Swamy/Seznec CGO 2015 measured ~3% on Haswell
 * ITTAGE; CPython documents 15-20%. We target the conservative regime. */
enum { OP_PUSH=0, OP_ADD=1, OP_SUB=2, OP_MUL=3, OP_DUP=4, OP_DROP=5,
       OP_XOR=6, OP_INC=7, OP_DEC=8, OP_HALT=9 };

int64_t slow_ho_cf2_v001(const uint8_t *prog, int n) {
    int64_t stk[256]; int sp = 0; int ip = 0;
    for (int step = 0; step < n; step++) {
        uint8_t op = prog[ip++];
        switch (op) {
            case OP_PUSH: stk[sp++] = (int64_t)prog[ip++]; break;
            case OP_ADD:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a+b; } break;
            case OP_SUB:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a-b; } break;
            case OP_MUL:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a*b; } break;
            case OP_DUP:  { int64_t a=stk[sp-1]; stk[sp++]=a; } break;
            case OP_DROP: sp--; break;
            case OP_XOR:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a^b; } break;
            case OP_INC:  stk[sp-1]++; break;
            case OP_DEC:  stk[sp-1]--; break;
            case OP_HALT: return sp > 0 ? stk[sp-1] : 0;
        }
        if (sp <= 0) sp = 1;     /* keep stack non-empty for determinism */
        if (sp >= 250) sp = 240;
    }
    return sp > 0 ? stk[sp-1] : 0;
}
