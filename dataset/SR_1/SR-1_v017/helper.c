#include <math.h>
__attribute__((noinline, noclone))
double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 46; k++) r += (double)exp(-base * k * 0.02);
    return r;
}