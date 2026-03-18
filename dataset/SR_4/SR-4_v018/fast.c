#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v018(int key);

void fast_sr4_v018(double *arr, int n, int key0, int key1) {
    double f0 = expensive_fn_v018(key0);
    double f1 = expensive_fn_v018(key1);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1;
    }
}