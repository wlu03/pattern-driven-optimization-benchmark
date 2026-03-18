#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v017(double *co2, double *temp, int n) {
    double total_co2 = 0.0;
    double total_temp = 0.0;
    for (int i = 0; i < n; i++) {
        total_co2 += co2[i];
        total_temp += temp[i];
    }
    return total_co2 + total_temp;
}