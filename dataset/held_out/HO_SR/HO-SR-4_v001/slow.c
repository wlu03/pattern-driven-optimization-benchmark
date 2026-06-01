#include <stdint.h>

// SLOW (inverted framing): the NAIVE intended-constant-time bitmask-
// OR scan.  The author wanted a side-channel-resistant table lookup
// that touches all n entries with constant work per index.  The body
// is purely arithmetic, no branches.  At -O3, however, both clang
// and gcc recognize the `result |= table[i] & mask` pattern with
// `mask = -cond` and `cond = (i == secret_idx)` -- they prove the
// loop returns table[secret_idx] and rewrite into a single
// `result = table[secret_idx]; break;` or a memcpy-style copy.  In
// either case the secret index leaks via timing / branch prediction.
//
// This is the "slow" baseline because it's the version that the
// compiler BREAKS.  fast.c is the version defended against the
// compiler with a `volatile` barrier.
//
// References:
// - Trail of Bits LLVM RFC: "__builtin_ct_select intrinsic"
// - Schneider et al. "When Compilers Break Constant-Time"
//   (arXiv:2410.13489)
// - Pornin eprint 2025/435 "On the Tightness of Constant-Time
//   Cryptographic Constructions"
int64_t slow_ho_sr4_v001(int64_t *table, int secret_idx, int n) {
    int64_t result = 0;
    for (int i = 0; i < n; i++) {
        int64_t cond = (i == secret_idx);
        int64_t mask = -cond;
        result |= table[i] & mask;
    }
    return result;
}
