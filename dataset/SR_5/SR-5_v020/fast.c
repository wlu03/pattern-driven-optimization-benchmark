#include <math.h>
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += (double)fabs((double)w[j]);
    return s;
}
__attribute__((noinline))
void fast_sr5_v020(double *out, double *data, int n, double *w, int m) {
    double inv = (double)1.0 / compute_norm(w, m);
    for (int i = 0; i < n; i++)
        out[i] = data[i] * inv;
}