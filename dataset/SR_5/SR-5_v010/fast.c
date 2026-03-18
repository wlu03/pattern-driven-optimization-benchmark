#include <math.h>
double compute_norm(double *w, int m);
__attribute__((noinline))
void fast_sr5_v010(double *out, double *data, int n, double *w, int m) {
    double inv = (double)1.0 / compute_norm(w, m);
    for (int i = 0; i < n; i++)
        out[i] = data[i] * inv;
}