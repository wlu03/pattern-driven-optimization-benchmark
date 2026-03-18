#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v010(int key);

void slow_sr4_v010(float *arr, int n, int key0, int key1, int key2, int key3) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v010(key0);
        float f1 = expensive_fn_v010(key1);
        float f2 = expensive_fn_v010(key2);
        float f3 = expensive_fn_v010(key3);
        arr[i] += f0 * f1 * f2 * f3;
        i++;
    }
}