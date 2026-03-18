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
} AoS_v017;

double slow_ds4_v017(AoS_v017 *arr, int n) {
    double total_co2 = 0.0;
    double total_temp = 0.0;
    for (int i = 0; i < n; i++) {
        total_co2 += (double)arr[i].co2;
        total_temp += (double)arr[i].temp;
    }
    return total_co2 + total_temp;
}