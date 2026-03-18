__attribute__((noinline))
#include <math.h>
static double series_fn(double base) {
    double r = 0.0;
    for (int k = 1; k <= 46; k++) r += (double)log(base * k + 1.0) / k;
    return r;
}
void slow_sr1_v015(double *arr, int n, double base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}