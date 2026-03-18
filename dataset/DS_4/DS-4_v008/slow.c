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
} AoS_v008;

double slow_ds4_v008(AoS_v008 *arr, int n) {
    double total_humidity = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].humidity > total_humidity) total_humidity = (double)arr[i].humidity;
    }
    return total_humidity;
}