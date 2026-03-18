#include <math.h>
__attribute__((noinline))
float series_fn(float base);
void slow_sr1_v014(float *arr, int n, float base) {
    for (int i = 0; i < n; i++)
        arr[i] *= series_fn(base);
}