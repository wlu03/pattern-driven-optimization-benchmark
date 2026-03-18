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
    float co2;
} AoS_v000;

double slow_ds4_v000(AoS_v000 *arr, int n) {
    double total_wind_speed = 1e308;
    double total_wind_dir = 1e308;
    double total_temp = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].wind_speed < total_wind_speed) total_wind_speed = (double)arr[i].wind_speed;
        if ((double)arr[i].wind_dir < total_wind_dir) total_wind_dir = (double)arr[i].wind_dir;
        if ((double)arr[i].temp < total_temp) total_temp = (double)arr[i].temp;
    }
    return total_wind_speed + total_wind_dir + total_temp;
}