#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v024(double *pad6, double *wind_dir, int n) {
    double total_pad6 = 1e308;
    double total_wind_dir = 1e308;
    for (int i = 0; i < n; i++) {
        if (pad6[i] < total_pad6) total_pad6 = pad6[i];
        if (wind_dir[i] < total_wind_dir) total_wind_dir = wind_dir[i];
    }
    return total_pad6 + total_wind_dir;
}