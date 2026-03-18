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
} AoS_v003;

double slow_ds4_v003(AoS_v003 *arr, int n) {
    double total_pressure = 0.0;
    int i = 0;
    while (i < n) {
        total_pressure += (double)arr[i].pressure;
        i++;
    }
    return total_pressure;
}