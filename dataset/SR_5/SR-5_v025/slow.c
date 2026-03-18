#include <math.h>
double compute_norm(double *w, int m);
__attribute__((noinline))
void slow_sr5_v025(double *out, double *data, int n, double *w, int m) {
    int i = 0;
    while (i < n) {
        out[i] = data[i] / compute_norm(w, m);
        i++;
    }
}