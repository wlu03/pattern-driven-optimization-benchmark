#include <math.h>
__attribute__((noinline))
double series_fn(double base);
void slow_sr1_v003(double *arr, int n, double base) {
    int i = 0;
    while (i < n) {
        arr[i] *= series_fn(base);
        i++;
    }
}