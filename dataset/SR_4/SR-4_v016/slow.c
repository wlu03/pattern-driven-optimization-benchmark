#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v016(int key);

void slow_sr4_v016(float *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v016(key0);
        float f1 = expensive_fn_v016(key1);
        float f2 = expensive_fn_v016(key2);
        float f3 = expensive_fn_v016(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}