#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v026(double *temp, double *humidity, double *light, int n) {
    double total_temp = 0.0;
    double total_humidity = 0.0;
    double total_light = 0.0;
    int i = 0;
    while (i < n) {
        total_temp += temp[i];
        total_humidity += humidity[i];
        total_light += light[i];
        i++;
    }
    return total_temp + total_humidity + total_light;
}