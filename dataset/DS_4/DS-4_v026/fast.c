#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v026(double *pad3, int n) {
    double total_pad3 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad3 += pad3[i];
    }
    return total_pad3;
}