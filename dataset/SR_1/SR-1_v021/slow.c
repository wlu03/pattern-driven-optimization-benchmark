__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 31; k++) r += (float)log(k + 1.0) * (float)sin(base * k);
    return r;
}
void slow_sr1_v021(float *arr, int n, float base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}