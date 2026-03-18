#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double expensive_fn_v002(int key);

void slow_sr4_v002(double *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v002(key);
        arr[i] *= f0;
        i++;
    }
}