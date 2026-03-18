#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v018(double *pressure, double *temp, int n) {
    double total_pressure = -1e308;
    double total_temp = -1e308;
    for (int i = 0; i < n; i++) {
        if (pressure[i] > total_pressure) total_pressure = pressure[i];
        if (temp[i] > total_temp) total_temp = temp[i];
    }
    return total_pressure + total_temp;
}