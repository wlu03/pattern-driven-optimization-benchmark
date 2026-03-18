#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v001(int key);

void slow_sr4_v001(float *arr, int n, int key0, int key1, int key2) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v001(key0);
        float f1 = expensive_fn_v001(key1);
        float f2 = expensive_fn_v001(key2);
        arr[i] += f0 * f1 * f2;
        i++;
    }
}