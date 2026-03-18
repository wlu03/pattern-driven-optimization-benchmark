__attribute__((noinline))
#include <math.h>
static double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 46; k++) r += (double)exp(-base * k * 0.02);
    return r;
}
void slow_sr1_v029(double *arr, int n, double base) {
    int i = 0;
    while (i < n) {
        arr[i] *= series_fn(base);
        i++;
    }
}