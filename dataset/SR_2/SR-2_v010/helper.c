#include <math.h>
__attribute__((noinline, noclone))
double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 16; k++) r += (double)sin(a * k) * (double)exp(-b * k * 0.1);
    return r;
}