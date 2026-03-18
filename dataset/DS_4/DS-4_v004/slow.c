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
} AoS_v004;

double slow_ds4_v004(AoS_v004 *arr, int n) {
    double total_pad5 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad5 += (double)arr[i].pad5;
    }
    return total_pad5;
}