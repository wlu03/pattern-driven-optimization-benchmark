#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v000(int key);

void fast_sr4_v000(double *arr, int n, int key) {
    double f0 = expensive_fn_v000(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}