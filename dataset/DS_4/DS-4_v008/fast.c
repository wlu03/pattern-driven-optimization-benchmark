#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v008(double *humidity, int n) {
    double total_humidity = -1e308;
    for (int i = 0; i < n; i++) {
        if (humidity[i] > total_humidity) total_humidity = humidity[i];
    }
    return total_humidity;
}