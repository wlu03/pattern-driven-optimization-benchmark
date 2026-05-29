// Noinline transformation function, placed in a separate TU so the
// compiler cannot inline-and-fuse it with surrounding memcpy()s.
// The function transforms `in` into `out` element-wise.  It can read
// and write the same buffer (in == out) safely.
__attribute__((noinline))
void ho_hr1_transform_v000(const float *in, float *out, int n) {
    for (int i = 0; i < n; i++) {
        float v = in[i];
        out[i] = v * 1.0001f + 0.5f;
    }
}
