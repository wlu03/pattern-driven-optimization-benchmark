#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v024(int key);

void slow_sr4_v024(float *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v024(key0);
        float f1 = expensive_fn_v024(key1);
        arr[i] *= f0 * f1;
    }
}