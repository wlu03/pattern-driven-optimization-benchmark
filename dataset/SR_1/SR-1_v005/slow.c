#include <math.h>
__attribute__((noinline))
float series_fn(float base);
void slow_sr1_v005(float *arr, int n, float base) {
    int i = 0;
    while (i < n) {
        arr[i] *= series_fn(base);
        i++;
    }
}