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
} AoS_v020;

double slow_ds4_v020(AoS_v020 *arr, int n) {
    double total_pad6 = 0.0;
    double total_noise = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad6 += (double)arr[i].pad6;
        total_noise += (double)arr[i].noise;
    }
    return total_pad6 + total_noise;
}