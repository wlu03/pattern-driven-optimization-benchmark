#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v025(int key);

void slow_sr4_v025(float *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v025(key0);
        float f1 = expensive_fn_v025(key1);
        float f2 = expensive_fn_v025(key2);
        arr[i] += f0 * f1 * f2;
    }
}
float expensive_fn_v025(int key) {
    float r = fabs((float)key) + 1.0f;
    for (int i = 0; i < 50; i++) r = sqrt(r + (float)i);
    return r;
}