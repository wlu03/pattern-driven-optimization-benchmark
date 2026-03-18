#include <math.h>
static double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += (double)fabs((double)w[j]);
    return s;
}
__attribute__((noinline))
void fast_sr5_v008(double *out, double *data, int n, double *w, int m) {
    double inv = (double)1.0 / compute_norm(w, m);
    int i = 0;
    while (i < n) {
        out[i] = data[i] * inv;
        i++;
    }
}