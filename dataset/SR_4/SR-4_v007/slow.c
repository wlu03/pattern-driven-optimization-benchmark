#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v007(int key);

void slow_sr4_v007(float *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v007(key);
        arr[i] += f0;
    }
}
float expensive_fn_v007(int key) {
    float r = 0.0f;
    for (int i = 0; i < 100; i++)
        r += sin((float)(key + i)) * cos((float)(key - i));
    return r;
}