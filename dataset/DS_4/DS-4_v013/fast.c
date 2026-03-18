#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v013(double *pad6, double *pad5, int n) {
    double total_pad6 = 0.0;
    double total_pad5 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad6 += pad6[i];
        total_pad5 += pad5[i];
    }
    return total_pad6 + total_pad5;
}