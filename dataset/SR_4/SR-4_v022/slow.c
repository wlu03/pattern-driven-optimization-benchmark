#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v022(int key);

void slow_sr4_v022(float *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v022(key0);
        float f1 = expensive_fn_v022(key1);
        arr[i] *= f0 * f1;
    }
}
float expensive_fn_v022(int key) {
    float r = 0.0f;
    for (int i = 0; i < 200; i++)
        r += sin((float)(key + i)) * cos((float)(key - i));
    return r;
}