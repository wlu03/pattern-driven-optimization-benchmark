#include <math.h>
__attribute__((noinline))
double series_fn(double base);
void fast_sr1_v010(double *arr, int n, double base) {
    double scale = series_fn(base);
    int i = 0;
    while (i < n) {
        arr[i] *= scale;
        i++;
    }
}