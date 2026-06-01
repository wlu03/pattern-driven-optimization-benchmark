// SLOW: TSVC s1113 pattern.  The loop reads a[N/2] on every iteration
// and also WRITES a[i] for every i.  When i == N/2, the read sees the
// just-written value -> the loop has a read-after-write (RAW)
// dependency on iteration index N/2.  GCC and clang at -O3 can't
// vectorize because they cannot prove the read doesn't alias with the
// store in some iteration.  Result: scalar loop with chain of dependent
// FMAs, ~1 element per chain-latency.
//
// Reference: VecTrans paper (arXiv:2503.19449) + TSVC_2 microbenchmark s1113.
void s1113_slow_ho_mi3_v003(float *a, float *b, long n);

void slow_ho_mi3_v003(float *a, float *b, long n) {
    s1113_slow_ho_mi3_v003(a, b, n);
}
