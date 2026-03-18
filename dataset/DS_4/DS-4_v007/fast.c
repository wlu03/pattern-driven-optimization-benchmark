#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v007(double *vy, int n) {
    double total_vy = 0.0;
    for (int i = 0; i < n; i++) {
        total_vy += vy[i];
    }
    return total_vy;
}