#include <math.h>
static float compute_norm(float *w, int m) {
    float s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return (float)sqrt((double)s);
}
__attribute__((noinline))
void fast_sr5_v011(float *out, float *data, int n, float *w, int m) {
    float inv = (float)1.0 / compute_norm(w, m);
    int i = 0;
    while (i < n) {
        out[i] = data[i] * inv;
        i++;
    }
}