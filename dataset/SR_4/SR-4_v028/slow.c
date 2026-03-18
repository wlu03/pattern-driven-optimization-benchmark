#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v028(int key);

void slow_sr4_v028(double *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v028(key0);
        double f1 = expensive_fn_v028(key1);
        double f2 = expensive_fn_v028(key2);
        arr[i] *= f0 * f1 * f2;
    }
}
double expensive_fn_v028(int key) {
    double base = 1.0 + (double)(key % 10) * 0.01;
    double r = base;
    for (int i = 0; i < 1000; i++) r = pow(base, r * 0.01);
    return r;
}