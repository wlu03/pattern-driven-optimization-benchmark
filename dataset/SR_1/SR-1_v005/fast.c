#include <math.h>
__attribute__((noinline))
float series_fn(float base);
void fast_sr1_v005(float *arr, int n, float base) {
    float scale = series_fn(base);
    int i = 0;
    while (i < n) {
        arr[i] *= scale;
        i++;
    }
}