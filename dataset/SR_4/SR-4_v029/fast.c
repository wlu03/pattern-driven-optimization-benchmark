#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v029(int key);

void fast_sr4_v029(float *arr, int n, int key) {
    float f0 = expensive_fn_v029(key);
    int i = 0;
    while (i < n) {
        arr[i] += f0;
        i++;
    }
}