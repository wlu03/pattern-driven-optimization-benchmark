__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 18; k++) r += (float)log(base * k + 1.0) / k;
    return r;
}
void slow_sr1_v008(float *arr, int n, float base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}