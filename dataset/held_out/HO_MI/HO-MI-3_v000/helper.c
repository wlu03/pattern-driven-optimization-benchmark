// Per-element work is a 12-multiply polynomial in (pivot + b[i]) so the
// vector benefit is throughput-limited (FMA throughput), not memory.
// `float` doubles the SIMD lane count vs `double` -> 4-lane NEON.
// noinline so the compiler can't prove aliasing at the call site.
#define POLY(x) \
    ((((((((((((x) * 0.5f + 1.0f) * (x) + 0.25f) * (x) + 0.125f) * (x) + 0.0625f) * (x) \
        + 0.03125f) * (x) + 0.015625f) * (x) + 0.0078125f) * (x) + 0.00390625f) * (x) \
        + 0.001953125f) * (x) + 0.0009765625f) * (x) + 0.00048828125f)

__attribute__((noinline))
void s1113_slow_ho_mi3_v000(float *a, float *b, long n) {
    long mid = n / 2;
    for (long i = 0; i < n; i++) {
        float pivot = a[mid];
        float x = pivot + b[i];
        a[i] = POLY(x);
    }
}

__attribute__((noinline))
void s1113_fast_ho_mi3_v000(float *a, float *b, long n) {
    long mid = n / 2;
    float pre = a[mid];
    for (long i = 0; i < mid; i++) {
        float x = pre + b[i];
        a[i] = POLY(x);
    }
    float xm = pre + b[mid];
    float tail_const_y = POLY(xm);
    a[mid] = tail_const_y;
    float tail_pivot = a[mid];
    for (long i = mid + 1; i < n; i++) {
        float x = tail_pivot + b[i];
        a[i] = POLY(x);
    }
}
