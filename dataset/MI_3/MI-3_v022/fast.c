#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_mi3_v022(double *data, int n) {
    double total = 0.0;
    for (int i = 0; i < n - 3; i++) {
        total += (data[i+0] + data[i+1] + data[i+2] + data[i+3]) * (double)0.25;
    }
    return total;
}