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
} AoS_v018;

double slow_ds4_v018(AoS_v018 *arr, int n) {
    double total_pressure = -1e308;
    double total_temp = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pressure > total_pressure) total_pressure = (double)arr[i].pressure;
        if ((double)arr[i].temp > total_temp) total_temp = (double)arr[i].temp;
    }
    return total_pressure + total_temp;
}