#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v010(double *humidity, double *wind_dir, double *pressure, int n) {
    double total_humidity = 0.0;
    double total_wind_dir = 0.0;
    double total_pressure = 0.0;
    for (int i = 0; i < n; i++) {
        total_humidity += humidity[i];
        total_wind_dir += wind_dir[i];
        total_pressure += pressure[i];
    }
    return total_humidity + total_wind_dir + total_pressure;
}