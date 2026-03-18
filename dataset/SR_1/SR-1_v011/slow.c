#include <math.h>
__attribute__((noinline))
double series_fn(double base);
void slow_sr1_v011(double *arr, int n, double base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}