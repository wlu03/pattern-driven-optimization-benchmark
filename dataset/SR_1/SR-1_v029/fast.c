#include <math.h>
__attribute__((noinline))
double series_fn(double base);
void fast_sr1_v029(double *arr, int n, double base) {
    double scale = series_fn(base);
    for (int i = 0; i < n; i++)
        arr[i] *= scale;
}