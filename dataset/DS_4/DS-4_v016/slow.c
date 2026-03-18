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
} AoS_v016;

double slow_ds4_v016(AoS_v016 *arr, int n) {
    double total_temp = 0.0;
    double total_pressure = 0.0;
    for (int i = 0; i < n; i++) {
        total_temp += (double)arr[i].temp;
        total_pressure += (double)arr[i].pressure;
    }
    return total_temp + total_pressure;
}