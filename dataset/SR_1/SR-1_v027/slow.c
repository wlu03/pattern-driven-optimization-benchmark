__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 38; k++) r += (float)sin(base * k * 1.0);
    return r;
}
void slow_sr1_v027(float *arr, int n, float base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}