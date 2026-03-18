#include <math.h>
__attribute__((noinline, noclone))
double compute_norm(double *w, int m) {
    double s = 0.0;
    for (int j = 0; j < m; j++) s += w[j] * w[j];
    return (double)sqrt((double)s);
}