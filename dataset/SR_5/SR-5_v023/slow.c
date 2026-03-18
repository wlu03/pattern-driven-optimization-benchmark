#include <math.h>
/* L2 norm — aliasing: out[] may alias w[], compiler cannot hoist */
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return (double)sqrt((double)s);
}
__attribute__((noinline))
void slow_sr5_v023(double *out, double *data, int n, double *w, int m) {
    for (int i = 0; i < n; i++)
        out[i] = data[i] / compute_norm(w, m);
}