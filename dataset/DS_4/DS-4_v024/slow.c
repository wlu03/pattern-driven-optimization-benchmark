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
} AoS_v024;

double slow_ds4_v024(AoS_v024 *arr, int n) {
    double total_humidity = 0.0;
    double total_noise = 0.0;
    int i = 0;
    while (i < n) {
        total_humidity += (double)arr[i].humidity;
        total_noise += (double)arr[i].noise;
        i++;
    }
    return total_humidity + total_noise;
}