#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v021(double *pad0, int n) {
    double total_pad0 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad0 += pad0[i];
    }
    return total_pad0;
}