// Direct: call the helper on src/dst with no intermediate buffer.  The
// helper's contract permits in == out, but more importantly it permits
// distinct in/out buffers; we just pass src and dst directly.  One
// memory pass instead of three.
extern void ho_hr1_transform_v002(const float *in, float *out, int n);

void fast_ho_hr1_v002(const float *src, float *dst, int n) {
    ho_hr1_transform_v002(src, dst, n);
}
