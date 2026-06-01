#include <stdint.h>
/* FAST: computed-goto dispatch via GCC's labels-as-values extension.
 * Each handler ends with NEXT_OP which is its own indirect-jump site;
 * BTB gets one prediction history slot per handler instead of one
 * global slot for the whole switch. https://lwn.net/Articles/1010905/ */
enum { F_PUSH=0, F_ADD=1, F_SUB=2, F_MUL=3, F_DUP=4, F_DROP=5,
       F_XOR=6, F_INC=7, F_DEC=8, F_HALT=9 };

int64_t fast_ho_cf2_v004(const uint8_t *prog, int n) {
    static void *const tbl[10] = {
        &&h_push, &&h_add, &&h_sub, &&h_mul, &&h_dup,
        &&h_drop, &&h_xor, &&h_inc, &&h_dec, &&h_halt
    };
    int64_t stk[256]; int sp = 0; int ip = 0; int step = 0;
    #define NEXT_OP() do { \
        if (sp <= 0) sp = 1; \
        if (sp >= 250) sp = 240; \
        if (++step >= n) goto done; \
        goto *tbl[prog[ip++]]; \
    } while (0)
    if (n <= 0) return 0;
    goto *tbl[prog[ip++]];

  h_push: stk[sp++] = (int64_t)prog[ip++]; NEXT_OP();
  h_add:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a+b; } NEXT_OP();
  h_sub:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a-b; } NEXT_OP();
  h_mul:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a*b; } NEXT_OP();
  h_dup:  { int64_t a=stk[sp-1]; stk[sp++]=a; } NEXT_OP();
  h_drop: sp--; NEXT_OP();
  h_xor:  { int64_t b=stk[--sp], a=stk[--sp]; stk[sp++]=a^b; } NEXT_OP();
  h_inc:  stk[sp-1]++; NEXT_OP();
  h_dec:  stk[sp-1]--; NEXT_OP();
  h_halt: return sp > 0 ? stk[sp-1] : 0;
  done:   return sp > 0 ? stk[sp-1] : 0;
    #undef NEXT_OP
}
