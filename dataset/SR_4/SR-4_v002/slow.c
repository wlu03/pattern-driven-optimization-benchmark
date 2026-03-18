#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v002(int key);

void slow_sr4_v002(float *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v002(key0);
        float f1 = expensive_fn_v002(key1);
        float f2 = expensive_fn_v002(key2);
        float f3 = expensive_fn_v002(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}
float expensive_fn_v002(int key) {
    float r = fabs((float)key) + 1.0f;
    for (int i = 0; i < 200; i++) r = sqrt(r + (float)i);
    return r;
}