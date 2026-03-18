#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v027(int key);

void fast_sr4_v027(float *arr, int n, int key) {
    float f0 = expensive_fn_v027(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}