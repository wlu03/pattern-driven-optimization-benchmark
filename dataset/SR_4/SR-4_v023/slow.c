#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v023(int key);

void slow_sr4_v023(double *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v023(key0);
        double f1 = expensive_fn_v023(key1);
        double f2 = expensive_fn_v023(key2);
        double f3 = expensive_fn_v023(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}
double expensive_fn_v023(int key) {
    double r = 0.0;
    for (int i = 1; i <= 30; i++)
        r += log((double)(key + i));
    return r;
}