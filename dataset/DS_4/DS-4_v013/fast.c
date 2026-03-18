#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v013(double *wind_speed, double *wind_dir, int n) {
    double total_wind_speed = 0.0;
    double total_wind_dir = 0.0;
    for (int i = 0; i < n; i++) {
        total_wind_speed += wind_speed[i];
        total_wind_dir += wind_dir[i];
    }
    return total_wind_speed + total_wind_dir;
}