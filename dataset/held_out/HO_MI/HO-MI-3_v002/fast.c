// FAST: split the loop into three parts so the vectorizer can prove
// no aliasing in each part:
//   (1) iterations [0, N/2): they read a[N/2] (constant within this
//       loop body because we haven't reached i==N/2 yet) and write
//       a[0..N/2-1] -- disjoint, vectorizable.
//   (2) the single i==N/2 iteration done by hand; capture the new
//       a[N/2] value in `tail_const`.
//   (3) iterations (N/2, N): they read `tail_const` (a scalar) and
//       write a[N/2+1..N-1] -- disjoint, vectorizable.
//
// Cite: VecTrans paper (arXiv:2503.19449) + TSVC_2 s1113.
void s1113_fast_ho_mi3_v002(float *a, float *b, long n);

void fast_ho_mi3_v002(float *a, float *b, long n) {
    s1113_fast_ho_mi3_v002(a, b, n);
}
