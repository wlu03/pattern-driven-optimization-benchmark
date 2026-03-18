#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v012(int key);

void slow_sr4_v012(double *arr, int n, int key0, int key1, int key2, int key3) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v012(key0);
        double f1 = expensive_fn_v012(key1);
        double f2 = expensive_fn_v012(key2);
        double f3 = expensive_fn_v012(key3);
        arr[i] += f0 * f1 * f2 * f3;
        i++;
    }
}
double expensive_fn_v012(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 100; i++) r = sqrt(r + (double)i);
    return r;
}