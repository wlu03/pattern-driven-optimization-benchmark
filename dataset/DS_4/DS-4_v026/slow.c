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
} AoS_v026;

double slow_ds4_v026(AoS_v026 *arr, int n) {
    double total_temp = 0.0;
    double total_humidity = 0.0;
    double total_light = 0.0;
    int i = 0;
    while (i < n) {
        total_temp += (double)arr[i].temp;
        total_humidity += (double)arr[i].humidity;
        total_light += (double)arr[i].light;
        i++;
    }
    return total_temp + total_humidity + total_light;
}