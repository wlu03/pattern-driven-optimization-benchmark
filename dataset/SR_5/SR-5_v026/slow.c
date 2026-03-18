#include <math.h>
/* L2 norm — aliasing: out[] may alias w[], compiler cannot hoist */
static float compute_norm(float *w, int m) {
    float s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return (float)sqrt((double)s);
}
__attribute__((noinline))
void slow_sr5_v026(float *out, float *data, int n, float *w, int m) {
    for (int i = 0; i < n; i++)
        out[i] = data[i] / compute_norm(w, m);
}