#include <stdint.h>

// FAST (defended): same bitmask-OR scan, but each iteration's
// intermediate `result` is declared `volatile` so the compiler is
// forbidden from proving the loop is equivalent to a single direct
// indexed load.  The optimizer must keep the body intact: an
// unconditional load of every table[i] plus the bitmask AND + OR
// fold.  This preserves constant-time behavior at the cost of
// disabling the loop's transformation into a branch/early-exit.
//
// In a real CT primitive this would use one of the volatile barriers
// recommended by the BearSSL playbook (Pornin), or the upcoming
// __builtin_ct_select intrinsic (Trail of Bits LLVM RFC, landing in
// LLVM 22).  For LLVM < 22 the volatile barrier is the portable
// defense.
//
// References: BearSSL (Pornin); Trail of Bits LLVM RFC for
// __builtin_ct_select; Schneider et al. arXiv:2410.13489.
int64_t fast_ho_sr4_v004(int64_t *table, int secret_idx, int n) {
    volatile int64_t result = 0;
    for (int i = 0; i < n; i++) {
        volatile int64_t cond = (i == secret_idx);
        int64_t mask = -cond;
        // Read-modify-write through the volatile barrier: the
        // compiler must materialize table[i] for every i and cannot
        // fold the loop into a direct indexed load.
        result = result | (table[i] & mask);
    }
    return result;
}
