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
} AoS_v010;

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_humidity = 0.0;
    double total_wind_dir = 0.0;
    double total_pressure = 0.0;
    for (int i = 0; i < n; i++) {
        total_humidity += (double)arr[i].humidity;
        total_wind_dir += (double)arr[i].wind_dir;
        total_pressure += (double)arr[i].pressure;
    }
    return total_humidity + total_wind_dir + total_pressure;
}