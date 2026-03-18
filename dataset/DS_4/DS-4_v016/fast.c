#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v016(double *temp, double *pressure, int n) {
    double total_temp = 0.0;
    double total_pressure = 0.0;
    for (int i = 0; i < n; i++) {
        total_temp += temp[i];
        total_pressure += pressure[i];
    }
    return total_temp + total_pressure;
}