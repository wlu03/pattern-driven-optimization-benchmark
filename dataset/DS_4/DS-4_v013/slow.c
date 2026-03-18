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
} AoS_v013;

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_wind_speed = 0.0;
    double total_wind_dir = 0.0;
    for (int i = 0; i < n; i++) {
        total_wind_speed += (double)arr[i].wind_speed;
        total_wind_dir += (double)arr[i].wind_dir;
    }
    return total_wind_speed + total_wind_dir;
}