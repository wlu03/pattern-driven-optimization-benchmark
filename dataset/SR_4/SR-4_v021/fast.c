#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v021(int key);

void fast_sr4_v021(float *arr, int n, int key) {
    float f0 = expensive_fn_v021(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}