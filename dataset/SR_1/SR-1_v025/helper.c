#include <math.h>
__attribute__((noinline, noclone))
double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 38; k++) r += (double)sin(base * k * 0.5);
    return r;
}