#include <math.h>
/* L1 norm — aliasing: out[] may alias w[], compiler cannot hoist */
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += (double)fabs((double)w[j]);
    return s;
}
__attribute__((noinline))
void slow_sr5_v029(double *out, double *data, int n, double *w, int m) {
    int i = 0;
    while (i < n) {
        out[i] = data[i] / compute_norm(w, m);
        i++;
    }
}