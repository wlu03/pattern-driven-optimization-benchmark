#include <math.h>
double compute_norm(double *w, int m);
__attribute__((noinline))
void fast_sr5_v018(double *out, double *data, int n, double *w, int m) {
    double inv = (double)1.0 / compute_norm(w, m);
    int i = 0;
    while (i < n) {
        out[i] = data[i] * inv;
        i++;
    }
}