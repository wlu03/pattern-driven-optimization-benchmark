#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double temp;
    double humidity;
    double pressure;
    double wind_speed;
    double wind_dir;
    double light;
    double noise;
    double co2;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v024;

double slow_ds4_v024(AoS_v024 *arr, int n) {
    double total_pad6 = 1e308;
    double total_wind_dir = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pad6 < total_pad6) total_pad6 = (double)arr[i].pad6;
        if ((double)arr[i].wind_dir < total_wind_dir) total_wind_dir = (double)arr[i].wind_dir;
    }
    return total_pad6 + total_wind_dir;
}