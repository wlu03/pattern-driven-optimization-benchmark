__attribute__((noinline))
#include <math.h>
static double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 46; k++) r += (double)exp(-base * k * 0.02);
    return r;
}
void fast_sr1_v029(double *arr, int n, double base) {
    double scale = series_fn(base);
    int i = 0;
    while (i < n) {
        arr[i] *= scale;
        i++;
    }
}