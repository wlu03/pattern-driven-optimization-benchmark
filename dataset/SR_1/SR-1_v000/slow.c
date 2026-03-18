__attribute__((noinline))
#include <math.h>
static double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 32; k++) r += (double)sin(base * k * 1.0);
    return r;
}
void slow_sr1_v000(double *arr, int n, double base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}