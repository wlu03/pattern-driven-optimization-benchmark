__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 47; k++) r += (float)exp(-base * k * 0.1);
    return r;
}
void fast_sr1_v011(float *arr, int n, float base) {
    float scale = series_fn(base);
    for (int i = 0; i < n; i++)
        arr[i] *= scale;
}