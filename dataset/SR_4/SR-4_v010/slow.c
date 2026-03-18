#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v010(int key);

void slow_sr4_v010(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v010(key);
        arr[i] += f0;
    }
}
double expensive_fn_v010(int key) {
    double base = 1.0 + (double)(key % 10) * 0.01;
    double r = base;
    for (int i = 0; i < 30; i++) r = pow(base, r * 0.01);
    return r;
}