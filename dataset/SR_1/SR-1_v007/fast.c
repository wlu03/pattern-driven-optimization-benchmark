__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 22; k++) r += (float)exp(-base * k * 0.05);
    return r;
}
void fast_sr1_v007(float *arr, int n, float base) {
    float scale = series_fn(base);
    int i = 0;
    while (i < n) {
        arr[i] *= scale;
        i++;
    }
}