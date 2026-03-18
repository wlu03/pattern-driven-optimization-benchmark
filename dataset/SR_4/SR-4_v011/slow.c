#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v011(int key);

void slow_sr4_v011(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v011(key);
        arr[i] *= f0;
    }
}
double expensive_fn_v011(int key) {
    double r = 1.0;
    for (int i = 0; i < 30; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}