#include <math.h>
float compute_norm(float *w, int m);
__attribute__((noinline))
void fast_sr5_v002(float *out, float *data, int n, float *w, int m) {
    float inv = (float)1.0 / compute_norm(w, m);
    for (int i = 0; i < n; i++)
        out[i] = data[i] * inv;
}