#include <math.h>
/* L1 norm — aliasing: out[] may alias w[], compiler cannot hoist */
static float compute_norm(float *w, int m) {
    float s = 0.0;
    for (int j = 0; j < m; j++) s += (float)fabs((double)w[j]);
    return s;
}
__attribute__((noinline))
void slow_sr5_v027(float *out, float *data, int n, float *w, int m) {
    int i = 0;
    while (i < n) {
        out[i] = data[i] / compute_norm(w, m);
        i++;
    }
}