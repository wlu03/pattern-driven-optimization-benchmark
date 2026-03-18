#include <math.h>
double compute_norm(double *w, int m);
__attribute__((noinline))
void slow_sr5_v023(double *out, double *data, int n, double *w, int m) {
    for (int i = 0; i < n; i++)
        out[i] = data[i] / compute_norm(w, m);
}