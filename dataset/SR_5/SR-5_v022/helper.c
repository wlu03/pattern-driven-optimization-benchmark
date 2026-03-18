#include <math.h>
__attribute__((noinline, noclone))
float compute_norm(float *w, int m) {
    float s = 0.0;
    for (int j = 0; j < m; j++) s += (float)fabs((double)w[j]);
    return s;
}