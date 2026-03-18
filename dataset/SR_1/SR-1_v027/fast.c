#include <math.h>
__attribute__((noinline))
float series_fn(float base);
void fast_sr1_v027(float *arr, int n, float base) {
    float scale = series_fn(base);
    for (int i = 0; i < n; i++)
        arr[i] *= scale;
}