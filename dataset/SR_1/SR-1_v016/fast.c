__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 17; k++) r += (float)sin(base * k * 0.5);
    return r;
}
void fast_sr1_v016(float *arr, int n, float base) {
    float scale = series_fn(base);
    for (int i = 0; i < n; i++)
        arr[i] *= scale;
}