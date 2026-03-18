__attribute__((noinline))
#include <math.h>
static double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 37; k++) r += (double)log(k + 1.0) * (double)sin(base * k);
    return r;
}
void slow_sr1_v013(double *arr, int n, double base) {
    int i = 0;
    while (i < n) {
        arr[i] *= series_fn(base);
        i++;
    }
}