#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v014(double *pad4, int n) {
    double total_pad4 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad4 += pad4[i];
    }
    return total_pad4;
}