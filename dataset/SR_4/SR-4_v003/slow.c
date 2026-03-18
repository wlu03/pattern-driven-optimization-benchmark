#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v003(int key);

void slow_sr4_v003(double *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v003(key);
        arr[i] += f0;
        i++;
    }
}
double expensive_fn_v003(int key) {
    double r = 0.0;
    for (int i = 1; i <= 500; i++)
        r += log((double)(key + i));
    return r;
}