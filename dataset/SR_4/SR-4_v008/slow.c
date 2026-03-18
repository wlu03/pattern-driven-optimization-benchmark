#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v008(int key);

void slow_sr4_v008(float *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v008(key0);
        float f1 = expensive_fn_v008(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}
float expensive_fn_v008(int key) {
    float r = fabs((float)key) + 1.0f;
    for (int i = 0; i < 500; i++) r = sqrt(r + (float)i);
    return r;
}