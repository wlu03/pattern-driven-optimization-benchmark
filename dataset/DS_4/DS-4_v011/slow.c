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
} AoS_v011;

double slow_ds4_v011(AoS_v011 *arr, int n) {
    double total_co2 = 0.0;
    int i = 0;
    while (i < n) {
        total_co2 += (double)arr[i].co2;
        i++;
    }
    return total_co2;
}