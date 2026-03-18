__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 31; k++) r += (float)log(k + 1.0) * (float)sin(base * k);
    return r;
}
void fast_sr1_v021(float *arr, int n, float base) {
    float scale = series_fn(base);
    for (int i = 0; i < n; i++)
        arr[i] *= scale;
}