#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v002(int key);

void fast_sr4_v002(double *arr, int n, int key) {
    double f0 = expensive_fn_v002(key);
    int i = 0;
    while (i < n) {
        arr[i] *= f0;
        i++;
    }
}