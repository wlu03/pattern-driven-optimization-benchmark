#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v019(int key);

void slow_sr4_v019(double *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v019(key0);
        double f1 = expensive_fn_v019(key1);
        arr[i] += f0 * f1;
    }
}
double expensive_fn_v019(int key) {
    double x = (double)key * 0.001;
    double r = 0.0;
    for (int i = 0; i < 1000; i++) {
        r += x * x * x - 3.0 * x * x + 2.0 * x - 1.0;
        x += 0.0001;
    }
    return r;
}