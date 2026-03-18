#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v020(int key);

void slow_sr4_v020(double *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v020(key0);
        double f1 = expensive_fn_v020(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}
double expensive_fn_v020(int key) {
    double x = (double)key * 0.001;
    double r = 0.0;
    for (int i = 0; i < 1000; i++) {
        r += x * x * x - 3.0 * x * x + 2.0 * x - 1.0;
        x += 0.0001;
    }
    return r;
}