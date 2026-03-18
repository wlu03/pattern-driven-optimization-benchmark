#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
} AoS_v022;

double slow_ds4_v022(AoS_v022 *arr, int n) {
    double total_light = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].light < total_light) total_light = (double)arr[i].light;
    }
    return total_light;
}