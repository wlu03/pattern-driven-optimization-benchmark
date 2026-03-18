#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v011(double *co2, int n) {
    double total_co2 = 0.0;
    int i = 0;
    while (i < n) {
        total_co2 += co2[i];
        i++;
    }
    return total_co2;
}