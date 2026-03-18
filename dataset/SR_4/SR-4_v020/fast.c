#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v020(int key);

void fast_sr4_v020(float *arr, int n, int key0, int key1) {
    float f0 = expensive_fn_v020(key0);
    float f1 = expensive_fn_v020(key1);
    int i = 0;
    while (i < n) {
        arr[i] *= f0 * f1;
        i++;
    }
}