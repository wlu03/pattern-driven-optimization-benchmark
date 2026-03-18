__attribute__((noinline))
#include <math.h>
static float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 42; k++) r += (float)sin(base * k * 2.0);
    return r;
}
void fast_sr1_v028(float *arr, int n, float base) {
    float scale = series_fn(base);
    int i = 0;
    while (i < n) {
        arr[i] *= scale;
        i++;
    }
}