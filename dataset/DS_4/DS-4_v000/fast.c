#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v000(double *a, int n) {
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_a += a[i];
    }
    return total_a;
}