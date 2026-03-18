#include <math.h>
__attribute__((noinline, noclone))
double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 26; k++) r += (double)log(base * k + 1.0) / k;
    return r;
}