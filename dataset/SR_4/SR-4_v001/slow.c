#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v001(int key);

void slow_sr4_v001(double *arr, int n, int key0, int key1, int key2) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v001(key0);
        double f1 = expensive_fn_v001(key1);
        double f2 = expensive_fn_v001(key2);
        arr[i] += f0 * f1 * f2;
        i++;
    }
}
double expensive_fn_v001(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 100; i++) r = sqrt(r + (double)i);
    return r;
}