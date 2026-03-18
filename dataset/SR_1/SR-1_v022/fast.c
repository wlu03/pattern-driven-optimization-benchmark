__attribute__((noinline))
#include <math.h>
static double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 30; k++) r += (double)log(base * k + 1.0) / k;
    return r;
}
void fast_sr1_v022(double *arr, int n, double base) {
    double scale = series_fn(base);
    for (int i = 0; i < n; i++)
        arr[i] *= scale;
}