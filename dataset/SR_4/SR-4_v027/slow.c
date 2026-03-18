#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v027(int key);

void slow_sr4_v027(double *arr, int n, int key0, int key1, int key2) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v027(key0);
        double f1 = expensive_fn_v027(key1);
        double f2 = expensive_fn_v027(key2);
        arr[i] += f0 * f1 * f2;
        i++;
    }
}
double expensive_fn_v027(int key) {
    unsigned int h = (unsigned int)key;
    double r = 0.0;
    for (int i = 0; i < 1000; i++) {
        h = h * 2654435761u;
        r += (double)(h & 0xFFFF) / 65536.0;
    }
    return r / 1000;
}