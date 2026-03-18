#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v011(int key);

void fast_sr4_v011(double *arr, int n, int key0, int key1, int key2) {
    double f0 = expensive_fn_v011(key0);
    double f1 = expensive_fn_v011(key1);
    double f2 = expensive_fn_v011(key2);
    int i = 0;
    while (i < n) {
        arr[i] += f0 * f1 * f2;
        i++;
    }
}