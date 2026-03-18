#include <math.h>
__attribute__((noinline, noclone))
double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 34; k++) r += (double)log(k + 1.0) * (double)sin(base * k);
    return r;
}